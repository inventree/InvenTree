"""Registry for loading and managing multiple plugins at run-time.

- Holds the class and the object that contains all code to maintain plugin states
- Manages setup and teardown of plugin class instances
"""

import imp
import importlib
import logging
import os
import subprocess
from importlib import reload
from pathlib import Path
from typing import Dict, List, OrderedDict

from django.apps import apps
from django.conf import settings
from django.contrib import admin
from django.db.utils import IntegrityError, OperationalError, ProgrammingError
from django.urls import clear_url_caches, include, re_path
from django.utils.text import slugify

from maintenance_mode.core import (get_maintenance_mode, maintenance_mode_on,
                                   set_maintenance_mode)

from InvenTree.config import get_setting

from .helpers import (IntegrationPluginError, get_entrypoints, get_plugins,
                      handle_error, log_error)
from .plugin import InvenTreePlugin

logger = logging.getLogger('inventree')


class PluginsRegistry:
    """The PluginsRegistry class."""

    def __init__(self) -> None:
        """Initialize registry.

        Set up all needed references for internal and external states.
        """
        # plugin registry
        self.plugins: Dict[str, InvenTreePlugin] = {}           # List of active instances
        self.plugins_inactive: Dict[str, InvenTreePlugin] = {}  # List of inactive instances
        self.plugins_full: Dict[str, InvenTreePlugin] = {}      # List of all plugin instances

        self.plugin_modules: List(InvenTreePlugin) = []         # Holds all discovered plugins

        self.errors = {}                                        # Holds discovering errors

        # flags
        self.is_loading = False                                 # Are plugins beeing loaded right now
        self.apps_loading = True                                # Marks if apps were reloaded yet
        self.git_is_modern = True                               # Is a modern version of git available

        self.installed_apps = []                                # Holds all added plugin_paths

        # mixins
        self.mixins_settings = {}

    def get_plugin(self, slug):
        """Lookup plugin by slug (unique key)."""
        if slug not in self.plugins:
            logger.warning(f"Plugin registry has no record of plugin '{slug}'")
            return None

        return self.plugins[slug]

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
        if not settings.PLUGINS_ENABLED:
            # Plugins not enabled, do nothing
            return  # pragma: no cover

        logger.info('Start loading plugins')

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
                    print(f'[PLUGIN] Above error occured during testing - {retry_counter}/{settings.PLUGIN_RETRY} retries left')

                # now the loading will re-start up with init

            # disable full reload after the first round
            if full_reload:
                full_reload = False

        # Remove maintenance mode
        if not _maintenance:
            set_maintenance_mode(False)

        logger.info('Finished loading plugins')

    def unload_plugins(self):
        """Unload and deactivate all IntegrationPlugins."""
        if not settings.PLUGINS_ENABLED:
            # Plugins not enabled, do nothing
            return  # pragma: no cover

        logger.info('Start unloading plugins')

        # Set maintanace mode
        _maintenance = bool(get_maintenance_mode())
        if not _maintenance:
            set_maintenance_mode(True)  # pragma: no cover

        # remove all plugins from registry
        self._clean_registry()

        # deactivate all integrations
        self._deactivate_plugins()

        # remove maintenance
        if not _maintenance:
            set_maintenance_mode(False)  # pragma: no cover
        logger.info('Finished unloading plugins')

    def reload_plugins(self, full_reload: bool = False):
        """Safely reload.

        Args:
            full_reload (bool, optional): Reload everything - including plugin mechanism. Defaults to False.
        """
        # Do not reload whe currently loading
        if self.is_loading:
            return  # pragma: no cover

        logger.info('Start reloading plugins')

        with maintenance_mode_on():
            self.unload_plugins()
            self.load_plugins(full_reload)

        logger.info('Finished reloading plugins')

    def plugin_dirs(self):
        """Construct a list of directories from where plugins can be loaded"""

        dirs = ['plugin.builtin', ]

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
        if not settings.PLUGINS_ENABLED:
            # Plugins not enabled, do nothing
            return  # pragma: no cover

        collected_plugins = []

        # Collect plugins from paths
        for plugin in self.plugin_dirs():

            logger.info(f"Loading plugins from directory '{plugin}'")

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
        logger.info(f'Collected {len(collected_plugins)} plugins!')
        logger.info(", ".join([a.__module__ for a in collected_plugins]))

        return collected_plugins

    def install_plugin_file(self):
        """Make sure all plugins are installed in the current enviroment."""
        if settings.PLUGIN_FILE_CHECKED:
            logger.info('Plugin file was already checked')
            return True

        try:
            output = str(subprocess.check_output(['pip', 'install', '-U', '-r', settings.PLUGIN_FILE], cwd=settings.BASE_DIR.parent), 'utf-8')
        except subprocess.CalledProcessError as error:  # pragma: no cover
            logger.error(f'Ran into error while trying to install plugins!\n{str(error)}')
            return False
        except FileNotFoundError:  # pragma: no cover
            # System most likely does not have 'git' installed
            return False

        logger.info(f'plugin requirements were run\n{output}')

        # do not run again
        settings.PLUGIN_FILE_CHECKED = True
        return 'first_run'

    # endregion

    # region registry functions
    def with_mixin(self, mixin: str, active=None):
        """Returns reference to all plugins that have a specified mixin enabled."""
        result = []

        for plugin in self.plugins.values():
            if plugin.mixin_enabled(mixin):

                if active is not None:
                    # Filter by 'enabled' status
                    config = plugin.plugin_config()

                    if config.active != active:
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

        logger.info('Starting plugin initialisation')

        # Initialize plugins
        for plg in self.plugin_modules:
            # These checks only use attributes - never use plugin supplied functions -> that would lead to arbitrary code execution!!
            plg_name = plg.NAME
            plg_key = slugify(plg.SLUG if getattr(plg, 'SLUG', None) else plg_name)  # keys are slugs!

            try:
                plg_db, _ = PluginConfig.objects.get_or_create(key=plg_key, name=plg_name)
            except (OperationalError, ProgrammingError) as error:
                # Exception if the database has not been migrated yet - check if test are running - raise if not
                if not settings.PLUGIN_TESTING:
                    raise error  # pragma: no cover
                plg_db = None
            except (IntegrityError) as error:  # pragma: no cover
                logger.error(f"Error initializing plugin `{plg_name}`: {error}")

            # Append reference to plugin
            plg.db = plg_db

            # Always activate if testing
            if settings.PLUGIN_TESTING or (plg_db and plg_db.active):
                # Check if the plugin was blocked -> threw an error; option1: package, option2: file-based
                if disabled and ((plg.__name__ == disabled) or (plg.__module__ == disabled)):
                    safe_reference(plugin=plg, key=plg_key, active=False)
                    continue  # continue -> the plugin is not loaded

                # Initialize package - we can be sure that an admin has activated the plugin
                logger.info(f'Loading plugin `{plg_name}`')
                try:
                    plg_i: InvenTreePlugin = plg()
                    logger.info(f'Loaded plugin `{plg_name}`')
                except Exception as error:
                    handle_error(error, log_name='init')  # log error and raise it -> disable plugin

                # Safe extra attributes
                plg_i.is_package = getattr(plg_i, 'is_package', False)
                plg_i.pk = plg_db.pk if plg_db else None
                plg_i.db = plg_db

                # Run version check for plugin
                if (plg_i.MIN_VERSION or plg_i.MAX_VERSION) and not plg_i.check_version():
                    safe_reference(plugin=plg_i, key=plg_key, active=False)
                else:
                    safe_reference(plugin=plg_i, key=plg_key)
            else:  # pragma: no cover
                safe_reference(plugin=plg, key=plg_key, active=False)

    def _activate_plugins(self, force_reload=False, full_reload: bool = False):
        """Run activation functions for all plugins.

        Args:
            force_reload (bool, optional): Also reload base apps. Defaults to False.
            full_reload (bool, optional): Reload everything - including plugin mechanism. Defaults to False.
        """
        # activate integrations
        plugins = self.plugins.items()
        logger.info(f'Found {len(plugins)} active plugins')

        self.activate_plugin_settings(plugins)
        self.activate_plugin_schedule(plugins)
        self.activate_plugin_app(plugins, force_reload=force_reload, full_reload=full_reload)

    def _deactivate_plugins(self):
        """Run deactivation functions for all plugins."""
        self.deactivate_plugin_app()
        self.deactivate_plugin_schedule()
        self.deactivate_plugin_settings()
    # endregion

    # region mixin specific loading ...
    def activate_plugin_settings(self, plugins):
        """Activate plugin settings.

        Add all defined settings form the plugins to a unified dict in the registry.
        This dict is referenced by the PluginSettings for settings definitions.
        """
        logger.info('Activating plugin settings')

        self.mixins_settings = {}

        for slug, plugin in plugins:
            if plugin.mixin_enabled('settings'):
                plugin_setting = plugin.settings
                self.mixins_settings[slug] = plugin_setting

    def deactivate_plugin_settings(self):
        """Deactivate all plugin settings."""
        logger.info('Deactivating plugin settings')
        # clear settings cache
        self.mixins_settings = {}

    def activate_plugin_schedule(self, plugins):
        """Activate scheudles from plugins with the ScheduleMixin."""
        logger.info('Activating plugin tasks')

        from common.models import InvenTreeSetting

        # List of tasks we have activated
        task_keys = []

        if settings.PLUGIN_TESTING or InvenTreeSetting.get_setting('ENABLE_PLUGINS_SCHEDULE'):

            for _, plugin in plugins:

                if plugin.mixin_enabled('schedule'):
                    config = plugin.plugin_config()

                    # Only active tasks for plugins which are enabled
                    if config and config.active:
                        plugin.register_tasks()
                        task_keys += plugin.get_task_names()

        if len(task_keys) > 0:
            logger.info(f"Activated {len(task_keys)} scheduled tasks")

        # Remove any scheduled tasks which do not match
        # This stops 'old' plugin tasks from accumulating
        try:
            from django_q.models import Schedule

            scheduled_plugin_tasks = Schedule.objects.filter(name__istartswith="plugin.")

            deleted_count = 0

            for task in scheduled_plugin_tasks:
                if task.name not in task_keys:
                    task.delete()
                    deleted_count += 1

            if deleted_count > 0:
                logger.info(f"Removed {deleted_count} old scheduled tasks")  # pragma: no cover
        except (ProgrammingError, OperationalError):
            # Database might not yet be ready
            logger.warning("activate_integration_schedule failed, database not ready")

    def deactivate_plugin_schedule(self):
        """Deactivate ScheduleMixin.

        Currently nothing is done here.
        """
        pass

    def activate_plugin_app(self, plugins, force_reload=False, full_reload: bool = False):
        """Activate AppMixin plugins - add custom apps and reload.

        Args:
            plugins (dict): List of IntegrationPlugins that should be installed
            force_reload (bool, optional): Only reload base apps. Defaults to False.
            full_reload (bool, optional): Reload everything - including plugin mechanism. Defaults to False.
        """
        from common.models import InvenTreeSetting

        if settings.PLUGIN_TESTING or InvenTreeSetting.get_setting('ENABLE_PLUGINS_APP'):
            logger.info('Registering IntegrationPlugin apps')
            apps_changed = False

            # add them to the INSTALLED_APPS
            for _, plugin in plugins:
                if plugin.mixin_enabled('app'):
                    plugin_path = self._get_plugin_path(plugin)
                    if plugin_path not in settings.INSTALLED_APPS:
                        settings.INSTALLED_APPS += [plugin_path]
                        self.installed_apps += [plugin_path]
                        apps_changed = True

            # if apps were changed or force loading base apps -> reload
            if apps_changed or force_reload:
                # first startup or force loading of base apps -> registry is prob false
                if self.apps_loading or force_reload:
                    self.apps_loading = False
                    self._reload_apps(force_reload=True, full_reload=full_reload)
                else:
                    self._reload_apps(full_reload=full_reload)

                # rediscover models/ admin sites
                self._reregister_contrib_apps()

                # update urls - must be last as models must be registered for creating admin routes
                self._update_urls()

    def _reregister_contrib_apps(self):
        """Fix reloading of contrib apps - models and admin.

        This is needed if plugins were loaded earlier and then reloaded as models and admins rely on imports.
        Those register models and admin in their respective objects (e.g. admin.site for admin).
        """
        for plugin_path in self.installed_apps:
            try:
                app_name = plugin_path.split('.')[-1]
                app_config = apps.get_app_config(app_name)
            except LookupError:  # pragma: no cover
                # the plugin was never loaded correctly
                logger.debug(f'{app_name} App was not found during deregistering')
                break

            # reload models if they were set
            # models_module gets set if models were defined - even after multiple loads
            # on a reload the models registery is empty but models_module is not
            if app_config.models_module and len(app_config.models) == 0:
                reload(app_config.models_module)

            # check for all models if they are registered with the site admin
            model_not_reg = False
            for model in app_config.get_models():
                if not admin.site.is_registered(model):
                    model_not_reg = True

            # reload admin if at least one model is not registered
            # models are registered with admin in the 'admin.py' file - so we check
            # if the app_config has an admin module before trying to laod it
            if model_not_reg and hasattr(app_config.module, 'admin'):
                reload(app_config.module.admin)

    def _get_plugin_path(self, plugin):
        """Parse plugin path.

        The input can be eiter:
        - a local file / dir
        - a package
        """
        try:
            # for local path plugins
            plugin_path = '.'.join(plugin.path().relative_to(settings.BASE_DIR).parts)
        except ValueError:  # pragma: no cover
            # plugin is shipped as package - extract plugin module name
            plugin_path = plugin.__module__.split('.')[0]
        return plugin_path

    def deactivate_plugin_app(self):
        """Deactivate AppMixin plugins - some magic required."""
        # unregister models from admin
        for plugin_path in self.installed_apps:
            models = []  # the modelrefs need to be collected as poping an item in a iter is not welcomed
            app_name = plugin_path.split('.')[-1]
            try:
                app_config = apps.get_app_config(app_name)

                # check all models
                for model in app_config.get_models():
                    # remove model from admin site
                    try:
                        admin.site.unregister(model)
                    except Exception:  # pragma: no cover
                        pass
                    models += [model._meta.model_name]
            except LookupError:  # pragma: no cover
                # if an error occurs the app was never loaded right -> so nothing to do anymore
                logger.debug(f'{app_name} App was not found during deregistering')
                break

            # unregister the models (yes, models are just kept in multilevel dicts)
            for model in models:
                # remove model from general registry
                apps.all_models[plugin_path].pop(model)

            # clear the registry for that app
            # so that the import trick will work on reloading the same plugin
            # -> the registry is kept for the whole lifecycle
            if models and app_name in apps.all_models:
                apps.all_models.pop(app_name)

        # remove plugin from installed_apps
        self._clean_installed_apps()

        # reset load flag and reload apps
        settings.INTEGRATION_APPS_LOADED = False
        self._reload_apps()

        # update urls to remove the apps from the site admin
        self._update_urls()

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

    def _try_reload(self, cmd, *args, **kwargs):
        """Wrapper to try reloading the apps.

        Throws an custom error that gets handled by the loading function.
        """
        try:
            cmd(*args, **kwargs)
            return True, []
        except Exception as error:  # pragma: no cover
            handle_error(error)
    # endregion


registry: PluginsRegistry = PluginsRegistry()


def call_function(plugin_name, function_name, *args, **kwargs):
    """Global helper function to call a specific member function of a plugin."""
    return registry.call_plugin_function(plugin_name, function_name, *args, **kwargs)
