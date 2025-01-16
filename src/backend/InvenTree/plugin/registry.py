"""Registry for loading and managing multiple plugins at run-time.

- Holds the class and the object that contains all code to maintain plugin states
- Manages setup and teardown of plugin class instances
"""

import importlib
import importlib.machinery
import importlib.util
import os
import sys
import time
from collections import OrderedDict
from importlib.machinery import SourceFileLoader
from pathlib import Path
from threading import Lock
from typing import Any, Optional, Union

from django.apps import apps
from django.conf import settings
from django.contrib import admin
from django.db.utils import IntegrityError, OperationalError, ProgrammingError
from django.urls import clear_url_caches, path
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

import structlog

from common.settings import get_global_setting, set_global_setting
from InvenTree.config import get_plugin_dir
from InvenTree.ready import canAppAccessDatabase

from .helpers import (
    IntegrationPluginError,
    get_entrypoints,
    get_plugins,
    handle_error,
    log_error,
)
from .plugin import InvenTreePlugin

logger = structlog.get_logger('inventree')


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
        self.plugins: dict[str, InvenTreePlugin] = {}  # List of active instances
        self.plugins_inactive: dict[
            str, InvenTreePlugin
        ] = {}  # List of inactive instances
        self.plugins_full: dict[
            str, InvenTreePlugin
        ] = {}  # List of all plugin instances

        # Keep an internal hash of the plugin registry state
        self.registry_hash = None

        self.plugin_modules: list[InvenTreePlugin] = []  # Holds all discovered plugins
        self.mixin_modules: dict[str, Any] = {}  # Holds all discovered mixins

        self.errors = {}  # Holds discovering errors

        self.loading_lock = Lock()  # Lock to prevent multiple loading at the same time

        # flags
        self.plugins_loaded = (
            False  # Marks if the registry fully loaded and all django apps are reloaded
        )
        self.apps_loading = True  # Marks if apps were reloaded yet

        self.installed_apps = []  # Holds all added plugin_paths

    @property
    def is_loading(self):
        """Return True if the plugin registry is currently loading."""
        return self.loading_lock.locked()

    def get_plugin(self, slug, active=None):
        """Lookup plugin by slug (unique key)."""
        # Check if the registry needs to be reloaded
        self.check_reload()

        if slug not in self.plugins:
            logger.warning("Plugin registry has no record of plugin '%s'", slug)
            return None

        plg = self.plugins[slug]

        if active is not None and active != plg.is_active():
            return None

        return plg

    def get_plugin_config(self, slug: str, name: Union[str, None] = None):
        """Return the matching PluginConfig instance for a given plugin.

        Args:
            slug: The plugin slug
            name: The plugin name (optional)
        """
        import InvenTree.ready
        from plugin.models import PluginConfig

        if InvenTree.ready.isImportingData():
            return None

        try:
            cfg = PluginConfig.objects.filter(key=slug).first()

            if not cfg:
                cfg = PluginConfig.objects.create(key=slug)

        except PluginConfig.DoesNotExist:
            return None
        except (IntegrityError, OperationalError, ProgrammingError):  # pragma: no cover
            return None

        if name and cfg.name != name:
            # Update the name if it has changed
            try:
                cfg.name = name
                cfg.save()
            except Exception:
                logger.exception('Failed to update plugin name')

        return cfg

    def set_plugin_state(self, slug, state):
        """Set the state(active/inactive) of a plugin.

        Args:
            slug (str): Plugin slug
            state (bool): Plugin state - true = active, false = inactive
        """
        # Check if the registry needs to be reloaded
        self.check_reload()

        if slug not in self.plugins_full:
            logger.warning("Plugin registry has no record of plugin '%s'", slug)
            return

        cfg = self.get_plugin_config(slug)
        cfg.active = state
        cfg.save()

        # Update the registry hash value
        self.update_plugin_hash()

    def call_plugin_function(self, slug: str, func: str, *args, **kwargs):
        """Call a member function (named by 'func') of the plugin named by 'slug'.

        As this is intended to be run by the background worker,
        we do not perform any try/except here.

        Instead, any error messages are returned to the worker.
        """
        # Check if the registry needs to be reloaded
        self.check_reload()

        plugin = self.get_plugin(slug)

        if not plugin:
            return

        plugin_func = getattr(plugin, func)

        return plugin_func(*args, **kwargs)

    # region registry functions
    def with_mixin(self, mixin: str, active=True, builtin=None):
        """Returns reference to all plugins that have a specified mixin enabled.

        Args:
            mixin (str): Mixin name
            active (bool, optional): Filter by 'active' status of plugin. Defaults to True.
            builtin (bool, optional): Filter by 'builtin' status of plugin. Defaults to None.
        """
        # Check if the registry needs to be loaded
        self.check_reload()

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

    # region loading / unloading
    def _load_plugins(
        self, full_reload: bool = False, _internal: Optional[list] = None
    ):
        """Load and activate all IntegrationPlugins.

        Args:
            full_reload (bool, optional): Reload everything - including plugin mechanism. Defaults to False.
            _internal (list, optional): Internal apps to reload (used for testing). Defaults to None
        """
        logger.info('Loading plugins')

        try:
            self._init_plugins()
            self._activate_plugins(full_reload=full_reload, _internal=_internal)
        except (OperationalError, ProgrammingError, IntegrityError):
            # Exception if the database has not been migrated yet, or is not ready
            pass
        except IntegrationPluginError:
            # Plugin specific error has already been handled
            pass

        # ensure plugins_loaded is True
        self.plugins_loaded = True

        logger.debug('Finished loading plugins')

        # Trigger plugins_loaded event
        if canAppAccessDatabase():
            from plugin.events import PluginEvents, trigger_event

            trigger_event(PluginEvents.PLUGINS_LOADED)

    def _unload_plugins(self, force_reload: bool = False):
        """Unload and deactivate all IntegrationPlugins.

        Args:
            force_reload (bool, optional): Also reload base apps. Defaults to False.
        """
        logger.info('Start unloading plugins')

        # remove all plugins from registry
        self._clean_registry()

        # deactivate all integrations
        self._deactivate_plugins(force_reload=force_reload)

        logger.info('Finished unloading plugins')

    def reload_plugins(
        self,
        full_reload: bool = False,
        force_reload: bool = False,
        collect: bool = False,
        _internal: Optional[list] = None,
    ):
        """Reload the plugin registry.

        This should be considered the single point of entry for loading plugins!

        Args:
            full_reload (bool, optional): Reload everything - including plugin mechanism. Defaults to False.
            force_reload (bool, optional): Also reload base apps. Defaults to False.
            collect (bool, optional): Collect plugins before reloading. Defaults to False.
            _internal (list, optional): Internal apps to reload (used for testing). Defaults to None
        """
        # Do not reload when currently loading
        if self.is_loading:
            logger.debug('Skipping reload - plugin registry is currently loading')
            return

        if self.loading_lock.acquire(blocking=False):
            logger.info(
                'Plugin Registry: Reloading plugins - Force: %s, Full: %s, Collect: %s',
                force_reload,
                full_reload,
                collect,
            )

            if collect and not settings.PLUGINS_INSTALL_DISABLED:
                logger.info('Collecting plugins')
                self.install_plugin_file()
                self.plugin_modules = self.collect_plugins()

            self.plugins_loaded = False
            self._unload_plugins(force_reload=force_reload)
            self.plugins_loaded = True
            self._load_plugins(full_reload=full_reload, _internal=_internal)

            self.update_plugin_hash()

            self.loading_lock.release()
            logger.info('Plugin Registry: Loaded %s plugins', len(self.plugins))

    def plugin_dirs(self):
        """Construct a list of directories from where plugins can be loaded."""
        # Builtin plugins are *always* loaded
        dirs = ['plugin.builtin']

        if settings.PLUGINS_ENABLED:
            # Any 'external' plugins are only loaded if PLUGINS_ENABLED is set to True

            if settings.TESTING or settings.DEBUG:
                # If in TEST or DEBUG mode, load plugins from the 'samples' directory
                dirs.append('plugin.samples')

            if settings.TESTING:
                custom_dirs = os.getenv('INVENTREE_PLUGIN_TEST_DIR', None)
            else:  # pragma: no cover
                custom_dirs = get_plugin_dir()

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
                            logger.exception(
                                "Could not create plugin directory '%s'", pd
                            )
                            continue

                    # Ensure the directory has an __init__.py file
                    init_filename = pd.joinpath('__init__.py')

                    if not init_filename.exists():
                        try:
                            init_filename.write_text('# InvenTree plugin directory\n')
                        except Exception:  # pragma: no cover
                            logger.exception(
                                "Could not create file '%s'", init_filename
                            )
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
                        logger.info("Added plugin directory: '%s' as '%s'", pd, pd_path)

        return dirs

    def collect_plugins(self):
        """Collect plugins from all possible ways of loading. Returned as list."""
        collected_plugins = []

        # Collect plugins from paths
        for plugin_dir in self.plugin_dirs():
            logger.debug("Loading plugins from directory '%s'", plugin_dir)

            parent_path = None
            parent_obj = Path(plugin_dir)

            # If a "path" is provided, some special handling is required
            if parent_obj.name is not plugin_dir and len(parent_obj.parts) > 1:
                # Ensure PosixPath object is converted to a string, before passing to get_plugins
                parent_path = str(parent_obj.parent)
                plugin_dir = parent_obj.name

            # Gather Modules
            if parent_path:
                # On python 3.12 use new loader method
                if sys.version_info < (3, 12):
                    raw_module = _load_source(
                        plugin_dir, str(parent_obj.joinpath('__init__.py'))
                    )
                else:
                    raw_module = SourceFileLoader(
                        plugin_dir, str(parent_obj.joinpath('__init__.py'))
                    ).load_module()
            else:
                raw_module = importlib.import_module(plugin_dir)

            modules = get_plugins(raw_module, InvenTreePlugin, path=parent_path)

            for item in modules or []:
                collected_plugins.append(item)

        # From this point any plugins are considered "external" and only loaded if plugins are explicitly enabled
        if settings.PLUGINS_ENABLED:
            # Check if not running in testing mode and apps should be loaded from hooks
            if (not settings.PLUGIN_TESTING) or (
                settings.PLUGIN_TESTING and settings.PLUGIN_TESTING_SETUP
            ):
                # Collect plugins from setup entry points
                for entry in get_entrypoints():
                    try:
                        plugin = entry.load()
                        plugin.is_package = True
                        plugin.package_name = getattr(entry.dist, 'name', None)
                        plugin._get_package_metadata()
                        collected_plugins.append(plugin)
                    except Exception as error:  # pragma: no cover
                        handle_error(error, do_raise=False, log_name='discovery')

        # Log collected plugins
        logger.info('Collected %s plugins', len(collected_plugins))
        logger.debug(', '.join([a.__module__ for a in collected_plugins]))

        return collected_plugins

    def discover_mixins(self):
        """Discover all mixins from plugins and register them."""
        collected_mixins = {}

        for plg in self.plugins.values():
            collected_mixins.update(plg.get_registered_mixins())

        self.mixin_modules = collected_mixins

    def install_plugin_file(self):
        """Make sure all plugins are installed in the current environment."""
        from plugin.installer import install_plugins_file, plugins_file_hash

        file_hash = plugins_file_hash()

        if file_hash != settings.PLUGIN_FILE_HASH:
            install_plugins_file()
            settings.PLUGIN_FILE_HASH = file_hash

    # endregion

    # region general internal loading / activating / deactivating / unloading
    def _init_plugin(self, plugin, configs: dict):
        """Initialise a single plugin.

        Args:
            plugin: Plugin module
        """
        from InvenTree import version

        def safe_reference(plugin, key: str, active: bool = True):
            """Safe reference to plugin dicts."""
            if active:
                self.plugins[key] = plugin
            else:
                # Deactivate plugin in db (if currently set as active)
                if not settings.PLUGIN_TESTING and plugin.db.active:  # pragma: no cover
                    plugin.db.active = False
                    plugin.db.save(no_reload=True)
                self.plugins_inactive[key] = plugin.db
            self.plugins_full[key] = plugin

        # These checks only use attributes - never use plugin supplied functions -> that would lead to arbitrary code execution!!
        plg_name = plugin.NAME
        plg_key = slugify(
            plugin.SLUG if getattr(plugin, 'SLUG', None) else plg_name
        )  # keys are slugs!

        logger.info("Loading plugin '%s'", plg_key)

        if plg_key in configs:
            plg_db = configs[plg_key]
        else:
            plg_db = self.get_plugin_config(plg_key, plg_name)

        plugin.db = plg_db

        # Check if this is a 'builtin' plugin
        builtin = plugin.check_is_builtin()

        package_name = None

        # Extract plugin package name
        if getattr(plugin, 'is_package', False):
            package_name = getattr(plugin, 'package_name', None)

        # Auto-enable builtin plugins
        if builtin and plg_db and not plg_db.active:
            plg_db.active = True
            plg_db.save()

        # Save the package_name attribute to the plugin
        if plg_db.package_name != package_name:
            plg_db.package_name = package_name
            plg_db.save()

        # Determine if this plugin should be loaded:
        # - If PLUGIN_TESTING is enabled
        # - If this is a 'builtin' plugin
        # - If this plugin has been explicitly enabled by the user
        if settings.PLUGIN_TESTING or builtin or (plg_db and plg_db.active):
            # Initialize package - we can be sure that an admin has activated the plugin
            logger.debug('Loading plugin `%s`', plg_name)

            try:
                t_start = time.time()
                plg_i: InvenTreePlugin = plugin()
                dt = time.time() - t_start
                logger.debug('Loaded plugin `%s` in %.3fs', plg_name, dt)
            except Exception as error:
                handle_error(
                    error, log_name='init'
                )  # log error and raise it -> disable plugin

                logger.warning('Plugin `%s` could not be loaded', plg_name)

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
                _msg = _(
                    f"Plugin '{p}' is not compatible with the current InvenTree version {v}"
                )
                if v := plg_i.MIN_VERSION:
                    _msg += _(f'Plugin requires at least version {v}')
                if v := plg_i.MAX_VERSION:
                    _msg += _(f'Plugin requires at most version {v}')
                # Log to error stack
                log_error(_msg, reference='init')
            else:
                safe_reference(plugin=plg_i, key=plg_key)
        else:  # pragma: no cover
            safe_reference(plugin=plugin, key=plg_key, active=False)

    def _init_plugins(self):
        """Initialise all found plugins.

        Args:
            disabled (str, optional): Loading path of disabled app. Defaults to None.

        Raises:
            error: IntegrationPluginError
        """
        # Imports need to be in this level to prevent early db model imports
        from plugin.models import PluginConfig

        logger.debug('Starting plugin initialization')

        # Fetch and cache list of existing plugin configuration instances
        plugin_configs = {cfg.key: cfg for cfg in PluginConfig.objects.all()}

        # Initialize plugins
        for plg in self.plugin_modules:
            # Attempt to load each individual plugin
            attempts = settings.PLUGIN_RETRY

            while attempts > 0:
                attempts -= 1

                try:
                    self._init_plugin(plg, plugin_configs)
                    break
                except Exception as error:
                    # Handle the error, log it and try again
                    if attempts == 0:
                        handle_error(error, log_name='init', do_raise=True)

                        logger.exception(
                            '[PLUGIN] Encountered an error with %s:\n%s',
                            error.path,
                            str(error),
                        )

        logger.debug('Finished plugin initialization')

    def __get_mixin_order(self):
        """Returns a list of mixin classes, in the order that they should be activated."""
        # Preset list of mixins
        order = self.DEFAULT_MIXIN_ORDER

        # Append mixins that are not defined in the default list
        order += [
            m.get('cls')
            for m in self.mixin_modules.values()
            if m.get('cls') not in order
        ]

        # Final list of mixins
        return order

    def _activate_plugins(
        self,
        force_reload=False,
        full_reload: bool = False,
        _internal: Optional[list] = None,
    ):
        """Run activation functions for all plugins.

        Args:
            force_reload (bool, optional): Also reload base apps. Defaults to False.
            full_reload (bool, optional): Reload everything - including plugin mechanism. Defaults to False.
        """
        # Collect mixins
        self.discover_mixins()

        # Activate integrations
        plugins = self.plugins.items()
        logger.info('Found %s active plugins', len(plugins))

        for mixin in self.__get_mixin_order():
            if hasattr(mixin, '_activate_mixin'):
                mixin._activate_mixin(
                    self,
                    plugins,
                    force_reload=force_reload,
                    full_reload=full_reload,
                    _internal=_internal,
                )

        logger.debug('Done activating')

    def _deactivate_plugins(self, force_reload: bool = False):
        """Run deactivation functions for all plugins.

        Args:
            force_reload (bool, optional): Also reload base apps. Defaults to False.
        """
        for mixin in reversed(self.__get_mixin_order()):
            if hasattr(mixin, '_deactivate_mixin'):
                mixin._deactivate_mixin(self, force_reload=force_reload)

        logger.debug('Finished deactivating plugins')

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
            handle_error(error, do_raise=False)

    def _reload_apps(
        self,
        force_reload: bool = False,
        full_reload: bool = False,
        _internal: Optional[list] = None,
    ):
        """Internal: reload apps using django internal functions.

        Args:
            force_reload (bool, optional): Also reload base apps. Defaults to False.
            full_reload (bool, optional): Reload everything - including plugin mechanism. Defaults to False.
            _internal (list, optional): Internal use only (for testing). Defaults to None.
        """
        loadable_apps = settings.INSTALLED_APPS
        if _internal:
            loadable_apps += _internal

        if force_reload:
            # we can not use the built in functions as we need to brute force the registry
            apps.app_configs = OrderedDict()
            apps.apps_ready = apps.models_ready = apps.loading = apps.ready = False
            apps.clear_cache()
            self._try_reload(apps.populate, loadable_apps)
        else:
            self._try_reload(apps.set_installed_apps, loadable_apps)

    def _clean_installed_apps(self):
        for plugin in self.installed_apps:
            if plugin in settings.INSTALLED_APPS:
                settings.INSTALLED_APPS.remove(plugin)

        self.installed_apps = []

    def _clean_registry(self):
        """Remove all plugins from registry."""
        self.plugins: dict[str, InvenTreePlugin] = {}
        self.plugins_inactive: dict[str, InvenTreePlugin] = {}
        self.plugins_full: dict[str, InvenTreePlugin] = {}

    def _update_urls(self):
        """Due to the order in which plugins are loaded, the patterns in urls.py may be out of date.

        This function updates the patterns in urls.py to ensure that the correct patterns are loaded,
        and then refreshes the django url cache.

        Note that we also have to refresh the admin site URLS,
        as any custom AppMixin plugins require admin integration
        """
        from InvenTree.urls import urlpatterns
        from plugin.urls import get_plugin_urls

        for index, url in enumerate(urlpatterns):
            app_name = getattr(url, 'app_name', None)

            admin_url = settings.INVENTREE_ADMIN_URL

            if app_name == 'admin':
                urlpatterns[index] = path(
                    f'{admin_url}/', admin.site.urls, name='inventree-admin'
                )

            if app_name == 'plugin':
                urlpatterns[index] = get_plugin_urls()

        # Refresh the URL cache
        clear_url_caches()

    # endregion

    # region plugin registry hash calculations
    def update_plugin_hash(self):
        """When the state of the plugin registry changes, update the hash."""
        self.registry_hash = self.calculate_plugin_hash()

        try:
            old_hash = get_global_setting(
                '_PLUGIN_REGISTRY_HASH', '', create=False, cache=False
            )
        except Exception:
            old_hash = ''

        if old_hash != self.registry_hash:
            try:
                logger.debug(
                    'Updating plugin registry hash: %s', str(self.registry_hash)
                )
                set_global_setting(
                    '_PLUGIN_REGISTRY_HASH', self.registry_hash, change_user=None
                )
            except (OperationalError, ProgrammingError):
                # Exception if the database has not been migrated yet, or is not ready
                pass
            except Exception as exc:
                # Some other exception, we want to know about it
                logger.exception('Failed to update plugin registry hash: %s', str(exc))

    def plugin_settings_keys(self):
        """A list of keys which are used to store plugin settings."""
        return [
            'ENABLE_PLUGINS_APP',
            'ENABLE_PLUGINS_EVENTS',
            'ENABLE_PLUGINS_INTERFACE',
            'ENABLE_PLUGINS_NAVIGATION',
            'ENABLE_PLUGINS_SCHEDULE',
            'ENABLE_PLUGINS_URL',
        ]

    def calculate_plugin_hash(self):
        """Calculate a 'hash' value for the current registry.

        This is used to detect changes in the plugin registry,
        and to inform other processes that the plugin registry has changed
        """
        from hashlib import md5

        data = md5()

        # Hash for all loaded plugins
        for slug, plug in self.plugins.items():
            data.update(str(slug).encode())
            data.update(str(plug.name).encode())
            data.update(str(plug.version).encode())
            data.update(str(plug.is_active()).encode())

        for k in self.plugin_settings_keys():
            try:
                val = get_global_setting(k, create=False)
                msg = f'{k}-{val}'

                data.update(msg.encode())
            except Exception:
                pass

        return str(data.hexdigest())

    def check_reload(self):
        """Determine if the registry needs to be reloaded."""
        if settings.TESTING:
            # Skip if running during unit testing
            return

        if not canAppAccessDatabase(allow_shell=True):
            # Skip check if database cannot be accessed
            return

        logger.debug('Checking plugin registry hash')

        # If not already cached, calculate the hash
        if not self.registry_hash:
            self.registry_hash = self.calculate_plugin_hash()

        try:
            reg_hash = get_global_setting('_PLUGIN_REGISTRY_HASH', '', create=False)
        except Exception as exc:
            logger.exception('Failed to retrieve plugin registry hash: %s', str(exc))
            return

        if reg_hash and reg_hash != self.registry_hash:
            logger.info('Plugin registry hash has changed - reloading')
            self.reload_plugins(full_reload=True, force_reload=True, collect=True)

    # endregion


registry: PluginsRegistry = PluginsRegistry()


def call_plugin_function(plugin_name: str, function_name: str, *args, **kwargs):
    """Global helper function to call a specific member function of a plugin."""
    return registry.call_plugin_function(plugin_name, function_name, *args, **kwargs)


def _load_source(modname, filename):
    """Helper function to replace deprecated & removed imp.load_source.

    See https://docs.python.org/3/whatsnew/3.12.html#imp
    """
    loader = importlib.machinery.SourceFileLoader(modname, filename)
    spec = importlib.util.spec_from_file_location(modname, filename, loader=loader)
    module = importlib.util.module_from_spec(spec)
    # The module is always executed and not cached in sys.modules.
    # Uncomment the following line to cache the module.
    # sys.modules[module.__name__] = module
    loader.exec_module(module)
    return module
