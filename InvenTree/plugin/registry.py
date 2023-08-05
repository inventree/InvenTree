"""Registry for loading and managing multiple plugins at run-time.

- Holds the class and the object that contains all code to maintain plugin states
- Manages setup and teardown of plugin class instances
"""

import imp
import importlib
import logging
import os
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, OrderedDict

from django.apps import apps
from django.conf import settings
from django.contrib import admin
from django.db.utils import IntegrityError, OperationalError, ProgrammingError
from django.urls import clear_url_caches, include, re_path
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from maintenance_mode.core import (get_maintenance_mode, maintenance_mode_on,
                                   set_maintenance_mode)

from InvenTree.config import get_setting
from InvenTree.ready import canAppAccessDatabase

from .helpers import (IntegrationPluginError, get_entrypoints, get_plugins,
                      handle_error, log_error)
from .plugin import InvenTreePlugin

logger = logging.getLogger('inventree')


class PluginsRegistry:
    """The PluginsRegistry class."""

    from .base.integration.AppMixin import AppMixin
    from .base.integration.ScheduleMixin import ScheduleMixin
    from .base.integration.SettingsMixin import SettingsMixin
    from .base.integration.UrlsMixin import UrlsMixin

    DEFAULT_MIXIN_ORDER = [SettingsMixin, ScheduleMixin, AppMixin, UrlsMixin]

    def __init__(self) -> None:
        """Initialize registry.

        Set up all needed references for internal and external states.
        """
        # plugin registry
        self.plugins: Dict[str, InvenTreePlugin] = {}           # List of active instances
        self.plugins_inactive: Dict[str, InvenTreePlugin] = {}  # List of inactive instances
        self.plugins_full: Dict[str, InvenTreePlugin] = {}      # List of all plugin instances

        self.plugin_modules: List[InvenTreePlugin] = []         # Holds all discovered plugins
        self.mixin_modules: Dict[str, Any] = {}                 # Holds all discovered mixins

        self.errors = {}                                        # Holds discovering errors

        # flags
        self.is_loading = False                                 # Are plugins being loaded right now
        self.plugins_loaded = False                             # Marks if the registry fully loaded and all django apps are reloaded
        self.apps_loading = True                                # Marks if apps were reloaded yet

        self.installed_apps = []                                # Holds all added plugin_paths

    def get_plugin(self, slug):
        """Lookup plugin by slug (unique key)."""
        if slug not in self.plugins:
            logger.warning(f"Plugin registry has no record of plugin '{slug}'")
            return None

        return self.plugins[slug]

    def set_plugin_state(self, slug, state):
        """Set the state(active/inactive) of a plugin.

        Args:
            slug (str): Plugin slug
            state (bool): Plugin state - true = active, false = inactive
        """
        if slug not in self.plugins_full:
            logger.warning(f"Plugin registry has no record of plugin '{slug}'")
            return

        plugin = self.plugins_full[slug].db
        plugin.active = state
        plugin.save()

    def call_plugin_function(self, slug, func, *args, **kwargs):
        """Call a member function (named by 'func') of the plugin named by 'slug'.

        As this is intended to be run by the background worker,
        we do not perform any try/except here.

        Instead, any error messages are returned to the worker.
        """
        plugin = self.get_plugin(slug)

        if not plugin:
            return

        plugin_func = getattr(plugin, func)

        return plugin_func(*args, **kwargs)

    # region public functions
    # region loading / unloading
    def load_plugins(self, full_reload: bool = False):
        """Load and activate all IntegrationPlugins.

        Args:
            full_reload (bool, optional): Reload everything - including plugin mechanism. Defaults to False.
        """

        logger.info('Loading plugins')

        # Set maintanace mode
        _maintenance = bool(get_maintenance_mode())
        if not _maintenance:
            set_maintenance_mode(True)

        registered_successful = False
        blocked_plugin = None
        retry_counter = settings.PLUGIN_RETRY

        while not registered_successful:
            try:
                # We are using the db so for migrations etc we need to try this block
                self._init_plugins(blocked_plugin)
                self._activate_plugins(full_reload=full_reload)
                registered_successful = True
            except (OperationalError, ProgrammingError):  # pragma: no cover
                # Exception if the database has not been migrated yet
                logger.info('Database not accessible while loading plugins')
                break
            except IntegrationPluginError as error:
                logger.error(f'[PLUGIN] Encountered an error with {error.path}:\n{error.message}')
                log_error({error.path: error.message}, 'load')
                blocked_plugin = error.path  # we will not try to load this app again

                # Initialize apps without any plugins
                self._clean_registry()
                self._clean_installed_apps()
                self._activate_plugins(force_reload=True, full_reload=full_reload)

                # We do not want to end in an endless loop
                retry_counter -= 1

                if retry_counter <= 0:  # pragma: no cover
                    if settings.PLUGIN_TESTING:
                        print('[PLUGIN] Max retries, breaking loading')
                    break
                if settings.PLUGIN_TESTING:
                    print(f'[PLUGIN] Above error occurred during testing - {retry_counter}/{settings.PLUGIN_RETRY} retries left')

                # now the loading will re-start up with init

            # disable full reload after the first round
            if full_reload:
                full_reload = False

        # ensure plugins_loaded is True
        self.plugins_loaded = True

        # Remove maintenance mode
        if not _maintenance:
            set_maintenance_mode(False)

        logger.debug('Finished loading plugins')

        # Trigger plugins_loaded event
        if canAppAccessDatabase():
            from plugin.events import trigger_event
            trigger_event('plugins_loaded')

    def unload_plugins(self, force_reload: bool = False):
        """Unload and deactivate all IntegrationPlugins.

        Args:
            force_reload (bool, optional): Also reload base apps. Defaults to False.
        """

        logger.info('Start unloading plugins')

        # Set maintanace mode
        _maintenance = bool(get_maintenance_mode())
        if not _maintenance:
            set_maintenance_mode(True)  # pragma: no cover

        # remove all plugins from registry
        self._clean_registry()

        # deactivate all integrations
        self._deactivate_plugins(force_reload=force_reload)

        # remove maintenance
        if not _maintenance:
            set_maintenance_mode(False)  # pragma: no cover

        logger.info('Finished unloading plugins')

    def reload_plugins(self, full_reload: bool = False, force_reload: bool = False):
        """Safely reload.

        Args:
            full_reload (bool, optional): Reload everything - including plugin mechanism. Defaults to False.
            force_reload (bool, optional): Also reload base apps. Defaults to False.
        """
        # Do not reload when currently loading
        if self.is_loading:
            return  # pragma: no cover

        logger.info('Start reloading plugins')

        with maintenance_mode_on():
            self.plugins_loaded = False
            self.unload_plugins(force_reload=force_reload)
            self.plugins_loaded = True
            self.load_plugins(full_reload=full_reload)

        logger.info('Finished reloading plugins')

    def plugin_dirs(self):
        """Construct a list of directories from where plugins can be loaded"""

        # Builtin plugins are *always* loaded
        dirs = ['plugin.builtin', ]

        if settings.PLUGINS_ENABLED:
            # Any 'external' plugins are only loaded if PLUGINS_ENABLED is set to True

            if settings.TESTING or settings.DEBUG:
                # If in TEST or DEBUG mode, load plugins from the 'samples' directory
                dirs.append('plugin.samples')

            if settings.TESTING:
                custom_dirs = os.getenv('INVENTREE_PLUGIN_TEST_DIR', None)
            else:  # pragma: no cover
                custom_dirs = get_setting('INVENTREE_PLUGIN_DIR', 'plugin_dir')

                # Load from user specified directories (unless in testing mode)
                dirs.append('plugins')

            if custom_dirs is not None:
                # Allow multiple plugin directories to be specified
                for pd_text in custom_dirs.split(','):
                    pd = Path(pd_text.strip()).absolute()

                    # Attempt to create the directory if it does not already exist
                    if not pd.exists():
                        try:
                            pd.mkdir(exist_ok=True)
                        except Exception:  # pragma: no cover
                            logger.error(f"Could not create plugin directory '{pd}'")
                            continue

                    # Ensure the directory has an __init__.py file
                    init_filename = pd.joinpath('__init__.py')

                    if not init_filename.exists():
                        try:
                            init_filename.write_text("# InvenTree plugin directory\n")
                        except Exception:  # pragma: no cover
                            logger.error(f"Could not create file '{init_filename}'")
                            continue

                    # By this point, we have confirmed that the directory at least exists
                    if pd.exists() and pd.is_dir():
                        # Convert to python dot-path
                        if pd.is_relative_to(settings.BASE_DIR):
                            pd_path = '.'.join(pd.relative_to(settings.BASE_DIR).parts)
                        else:
                            pd_path = str(pd)

                        # Add path
                        dirs.append(pd_path)
                        logger.info(f"Added plugin directory: '{pd}' as '{pd_path}'")

        return dirs

    def collect_plugins(self):
        """Collect plugins from all possible ways of loading. Returned as list."""

        collected_plugins = []

        # Collect plugins from paths
        for plugin in self.plugin_dirs():

            logger.debug(f"Loading plugins from directory '{plugin}'")

            parent_path = None
            parent_obj = Path(plugin)

            # If a "path" is provided, some special handling is required
            if parent_obj.name is not plugin and len(parent_obj.parts) > 1:
                # Ensure PosixPath object is converted to a string, before passing to get_plugins
                parent_path = str(parent_obj.parent)
                plugin = parent_obj.name

            # Gather Modules
            if parent_path:
                raw_module = imp.load_source(plugin, str(parent_obj.joinpath('__init__.py')))
            else:
                raw_module = importlib.import_module(plugin)
            modules = get_plugins(raw_module, InvenTreePlugin, path=parent_path)

            if modules:
                [collected_plugins.append(item) for item in modules]

        # From this point any plugins are considered "external" and only loaded if plugins are explicitly enabled
        if settings.PLUGINS_ENABLED:

            # Check if not running in testing mode and apps should be loaded from hooks
            if (not settings.PLUGIN_TESTING) or (settings.PLUGIN_TESTING and settings.PLUGIN_TESTING_SETUP):
                # Collect plugins from setup entry points
                for entry in get_entrypoints():
                    try:
                        plugin = entry.load()
                        plugin.is_package = True
                        plugin._get_package_metadata()
                        collected_plugins.append(plugin)
                    except Exception as error:  # pragma: no cover
                        handle_error(error, do_raise=False, log_name='discovery')

        # Log collected plugins
        logger.info(f'Collected {len(collected_plugins)} plugins')
        logger.debug(", ".join([a.__module__ for a in collected_plugins]))

        return collected_plugins

    def discover_mixins(self):
        """Discover all mixins from plugins and register them."""
        collected_mixins = {}

        for plg in self.plugins.values():
            collected_mixins.update(plg.get_registered_mixins())

        self.mixin_modules = collected_mixins

    def install_plugin_file(self):
        """Make sure all plugins are installed in the current environment."""
        if settings.PLUGIN_FILE_CHECKED:
            logger.info('Plugin file was already checked')
            return True

        try:
            subprocess.check_output(['pip', 'install', '-U', '-r', settings.PLUGIN_FILE], cwd=settings.BASE_DIR.parent)
        except subprocess.CalledProcessError as error:  # pragma: no cover
            logger.error(f'Ran into error while trying to install plugins!\n{str(error)}')
            return False
        except FileNotFoundError:  # pragma: no cover
            # System most likely does not have 'git' installed
            return False

        # do not run again
        settings.PLUGIN_FILE_CHECKED = True
        return 'first_run'

    # endregion

    # region registry functions
    def with_mixin(self, mixin: str, active=None, builtin=None):
        """Returns reference to all plugins that have a specified mixin enabled."""
        result = []

        for plugin in self.plugins.values():
            if plugin.mixin_enabled(mixin):

                if active is not None:
                    # Filter by 'active' status of plugin
                    if active != plugin.is_active():
                        continue

                if builtin is not None:
                    # Filter by 'builtin' status of plugin
                    if builtin != plugin.is_builtin:
                        continue

                result.append(plugin)

        return result
    # endregion
    # endregion

    # region general internal loading /activating / deactivating / deloading
    def _init_plugins(self, disabled: str = None):
        """Initialise all found plugins.

        Args:
            disabled (str, optional): Loading path of disabled app. Defaults to None.

        Raises:
            error: IntegrationPluginError
        """
        # Imports need to be in this level to prevent early db model imports
        from InvenTree import version
        from plugin.models import PluginConfig

        def safe_reference(plugin, key: str, active: bool = True):
            """Safe reference to plugin dicts."""
            if active:
                self.plugins[key] = plugin
            else:
                # Deactivate plugin in db
                if not settings.PLUGIN_TESTING:  # pragma: no cover
                    plugin.db.active = False
                    plugin.db.save(no_reload=True)
                self.plugins_inactive[key] = plugin.db
            self.plugins_full[key] = plugin

        logger.debug('Starting plugin initialisation')

        # Initialize plugins
        for plg in self.plugin_modules:
            # These checks only use attributes - never use plugin supplied functions -> that would lead to arbitrary code execution!!
            plg_name = plg.NAME
            plg_key = slugify(plg.SLUG if getattr(plg, 'SLUG', None) else plg_name)  # keys are slugs!

            try:
                plg_db, _created = PluginConfig.objects.get_or_create(key=plg_key, name=plg_name)
            except (OperationalError, ProgrammingError) as error:
                # Exception if the database has not been migrated yet - check if test are running - raise if not
                if not settings.PLUGIN_TESTING:
                    raise error  # pragma: no cover
                plg_db = None
            except (IntegrityError) as error:  # pragma: no cover
                logger.error(f"Error initializing plugin `{plg_name}`: {error}")
                handle_error(error, log_name='init')

            # Append reference to plugin
            plg.db = plg_db

            # Check if this is a 'builtin' plugin
            builtin = plg.check_is_builtin()

            # Auto-enable builtin plugins
            if builtin and plg_db and not plg_db.active:
                plg_db.active = True
                plg_db.save()

            # Determine if this plugin should be loaded:
            # - If PLUGIN_TESTING is enabled
            # - If this is a 'builtin' plugin
            # - If this plugin has been explicitly enabled by the user
            if settings.PLUGIN_TESTING or builtin or (plg_db and plg_db.active):
                # Check if the plugin was blocked -> threw an error; option1: package, option2: file-based
                if disabled and ((plg.__name__ == disabled) or (plg.__module__ == disabled)):
                    safe_reference(plugin=plg, key=plg_key, active=False)
                    continue  # continue -> the plugin is not loaded

                # Initialize package - we can be sure that an admin has activated the plugin
                logger.debug(f'Loading plugin `{plg_name}`')

                try:
                    t_start = time.time()
                    plg_i: InvenTreePlugin = plg()
                    dt = time.time() - t_start
                    logger.info(f'Loaded plugin `{plg_name}` in {dt:.3f}s')
                except Exception as error:
                    handle_error(error, log_name='init')  # log error and raise it -> disable plugin
                    logger.warning(f"Plugin `{plg_name}` could not be loaded")

                # Safe extra attributes
                plg_i.is_package = getattr(plg_i, 'is_package', False)
                plg_i.pk = plg_db.pk if plg_db else None
                plg_i.db = plg_db

                # Run version check for plugin
                if (plg_i.MIN_VERSION or plg_i.MAX_VERSION) and not plg_i.check_version():
                    # Disable plugin
                    safe_reference(plugin=plg_i, key=plg_key, active=False)

                    p = plg_name
                    v = version.inventreeVersion()
                    _msg = _(f"Plugin '{p}' is not compatible with the current InvenTree version {v}")
                    if v := plg_i.MIN_VERSION:
                        _msg += _(f'Plugin requires at least version {v}')
                    if v := plg_i.MAX_VERSION:
                        _msg += _(f'Plugin requires at most version {v}')
                    # Log to error stack
                    log_error(_msg, reference='init')
                else:
                    safe_reference(plugin=plg_i, key=plg_key)
            else:  # pragma: no cover
                safe_reference(plugin=plg, key=plg_key, active=False)

    def __get_mixin_order(self):
        """Returns a list of mixin classes, in the order that they should be activated."""
        # Preset list of mixins
        order = self.DEFAULT_MIXIN_ORDER

        # Append mixins that are not defined in the default list
        order += [m.get('cls') for m in self.mixin_modules.values() if m.get('cls') not in order]

        # Final list of mixins
        return order

    def _activate_plugins(self, force_reload=False, full_reload: bool = False):
        """Run activation functions for all plugins.

        Args:
            force_reload (bool, optional): Also reload base apps. Defaults to False.
            full_reload (bool, optional): Reload everything - including plugin mechanism. Defaults to False.
        """
        # Collect mixins
        self.discover_mixins()

        # Activate integrations
        plugins = self.plugins.items()
        logger.info(f'Found {len(plugins)} active plugins')

        for mixin in self.__get_mixin_order():
            if hasattr(mixin, '_activate_mixin'):
                mixin._activate_mixin(self, plugins, force_reload=force_reload, full_reload=full_reload)

        logger.debug('Done activating')

    def _deactivate_plugins(self, force_reload: bool = False):
        """Run deactivation functions for all plugins.

        Args:
            force_reload (bool, optional): Also reload base apps. Defaults to False.
        """
        for mixin in reversed(self.__get_mixin_order()):
            if hasattr(mixin, '_deactivate_mixin'):
                mixin._deactivate_mixin(self, force_reload=force_reload)

        logger.info('Done deactivating')
    # endregion

    # region mixin specific loading ...
    def _try_reload(self, cmd, *args, **kwargs):
        """Wrapper to try reloading the apps.

        Throws an custom error that gets handled by the loading function.
        """
        try:
            cmd(*args, **kwargs)
            return True, []
        except Exception as error:  # pragma: no cover
            handle_error(error)

    def _reload_apps(self, force_reload: bool = False, full_reload: bool = False):
        """Internal: reload apps using django internal functions.

        Args:
            force_reload (bool, optional): Also reload base apps. Defaults to False.
            full_reload (bool, optional): Reload everything - including plugin mechanism. Defaults to False.
        """
        # If full_reloading is set to true we do not want to set the flag
        if not full_reload:
            self.is_loading = True  # set flag to disable loop reloading
        if force_reload:
            # we can not use the built in functions as we need to brute force the registry
            apps.app_configs = OrderedDict()
            apps.apps_ready = apps.models_ready = apps.loading = apps.ready = False
            apps.clear_cache()
            self._try_reload(apps.populate, settings.INSTALLED_APPS)
        else:
            self._try_reload(apps.set_installed_apps, settings.INSTALLED_APPS)
        self.is_loading = False

    def _clean_installed_apps(self):
        for plugin in self.installed_apps:
            if plugin in settings.INSTALLED_APPS:
                settings.INSTALLED_APPS.remove(plugin)

        self.installed_apps = []

    def _clean_registry(self):
        """Remove all plugins from registry."""
        self.plugins: Dict[str, InvenTreePlugin] = {}
        self.plugins_inactive: Dict[str, InvenTreePlugin] = {}
        self.plugins_full: Dict[str, InvenTreePlugin] = {}

    def _update_urls(self):
        from InvenTree.urls import frontendpatterns as urlpattern
        from InvenTree.urls import urlpatterns as global_pattern
        from plugin.urls import get_plugin_urls

        for index, url in enumerate(urlpattern):
            if hasattr(url, 'app_name'):
                if url.app_name == 'admin':
                    urlpattern[index] = re_path(r'^admin/', admin.site.urls, name='inventree-admin')
                elif url.app_name == 'plugin':
                    urlpattern[index] = get_plugin_urls()

        # Replace frontendpatterns
        global_pattern[0] = re_path('', include(urlpattern))
        clear_url_caches()
    # endregion


registry: PluginsRegistry = PluginsRegistry()


def call_function(plugin_name, function_name, *args, **kwargs):
    """Global helper function to call a specific member function of a plugin."""
    return registry.call_plugin_function(plugin_name, function_name, *args, **kwargs)
