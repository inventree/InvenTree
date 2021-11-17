# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import importlib
import pathlib
import logging
from typing import OrderedDict
from importlib import reload

from django.apps import AppConfig, apps
from django.conf import settings
from django.db.utils import OperationalError, ProgrammingError
from django.conf.urls import url, include
from django.urls import clear_url_caches
from django.contrib import admin

try:
    from importlib import metadata
except:
    import importlib_metadata as metadata

from maintenance_mode.core import maintenance_mode_on
from maintenance_mode.core import get_maintenance_mode, set_maintenance_mode

from plugin import plugins as inventree_plugins
from plugin.integration import IntegrationPluginBase

logger = logging.getLogger('inventree')


class PluginAppConfig(AppConfig):
    name = 'plugin'

    def ready(self):
        if not settings.INTEGRATION_PLUGINS_RELOADING:
            self._collect_plugins()
            self.load_plugins()

    # region public plugin functions
    def load_plugins(self):
        """load and activate all IntegrationPlugins"""
        logger.info('Start loading plugins')
        # set maintanace mode
        _maintenance = get_maintenance_mode()
        if not _maintenance:
            set_maintenance_mode(True)

        try:
            # we are using the db so for migrations etc we need to try this block
            self._init_plugins()
            self._activate_plugins()
        except (OperationalError, ProgrammingError):
            # Exception if the database has not been migrated yet
            logger.info('Database not accessible while loading plugins')

        # remove maintenance
        if not _maintenance:
            set_maintenance_mode(False)
        logger.info('Finished loading plugins')

    def unload_plugins(self):
        """unload and deactivate all IntegrationPlugins"""
        logger.info('Start unloading plugins')
        # set maintanace mode
        _maintenance = get_maintenance_mode()
        if not _maintenance:
            set_maintenance_mode(True)

        # remove all plugins from registry
        # plugins = settings.INTEGRATION_PLUGINS
        settings.INTEGRATION_PLUGINS = {}
        # plugins_inactive = settings.INTEGRATION_PLUGINS_INACTIVE
        settings.INTEGRATION_PLUGINS_INACTIVE = {}

        # deactivate all integrations
        self._deactivate_plugins()

        # remove maintenance
        if not _maintenance:
            set_maintenance_mode(False)
        logger.info('Finished unloading plugins')

    def reload_plugins(self):
        """safely reload IntegrationPlugins"""
        logger.info('Start reloading plugins')
        with maintenance_mode_on():
            self.unload_plugins()
            self.load_plugins()
        logger.info('Finished reloading plugins')
    # endregion

    # region general plugin managment mechanisms
    def _collect_plugins(self):
        """collect integration plugins from all possible ways of loading"""
        # Collect plugins from paths
        for plugin in settings.PLUGIN_DIRS:
            modules = inventree_plugins.get_plugins(importlib.import_module(plugin), IntegrationPluginBase, True)
            if modules:
                [settings.PLUGINS.append(item) for item in modules]

        # check if running in testing mode and apps should be loaded from hooks
        if (not settings.PLUGIN_TESTING) or (settings.PLUGIN_TESTING and settings.PLUGIN_TESTING_SETUP):
            # Collect plugins from setup entry points
            for entry in metadata.entry_points().get('inventree_plugins', []):
                plugin = entry.load()
                plugin.is_package = True
                settings.PLUGINS.append(plugin)

        # Log found plugins
        logger.info(f'Found {len(settings.PLUGINS)} plugins!')
        logger.info(", ".join([a.__module__ for a in settings.PLUGINS]))

    def _init_plugins(self):
        """initialise all found plugins"""
        from plugin.models import PluginConfig

        logger.info('Starting plugin initialisation')
        # Initialize integration plugins
        for plugin in inventree_plugins.load_integration_plugins():
            # check if package
            was_packaged = getattr(plugin, 'is_package', False)

            # check if activated
            # these checks only use attributes - never use plugin supplied functions -> that would lead to arbitrary code execution!!
            plug_name = plugin.PLUGIN_NAME
            plug_key = plugin.PLUGIN_SLUG if getattr(plugin, 'PLUGIN_SLUG', None) else plug_name
            try:
                plugin_db_setting, _ = PluginConfig.objects.get_or_create(key=plug_key, name=plug_name)
            except (OperationalError, ProgrammingError) as error:
                # Exception if the database has not been migrated yet - check if test are running - raise if not
                if not settings.PLUGIN_TESTING:
                    raise error
                plugin_db_setting = None

            # always activate if testing
            if settings.PLUGIN_TESTING or (plugin_db_setting and plugin_db_setting.active):
                # init package
                # now we can be sure that an admin has activated the plugin -> as of Nov 2021 there are not many checks in place
                # but we could enhance those to check signatures, run the plugin against a whitelist etc.
                logger.info(f'Loading integration plugin {plugin.PLUGIN_NAME}')
                plugin = plugin()
                logger.info(f'Loaded integration plugin {plugin.slug}')
                plugin.is_package = was_packaged
                if plugin_db_setting:
                    plugin.pk = plugin_db_setting.pk

                # safe reference
                settings.INTEGRATION_PLUGINS[plugin.slug] = plugin
            else:
                # save for later reference
                settings.INTEGRATION_PLUGINS_INACTIVE[plug_key] = plugin_db_setting

    def _activate_plugins(self):
        """run integration functions for all plugins"""
        # activate integrations
        plugins = settings.INTEGRATION_PLUGINS.items()
        logger.info(f'Found {len(plugins)} active plugins')

        self.activate_integration_globalsettings(plugins)
        self.activate_integration_app(plugins)

    def _deactivate_plugins(self):
        """run integration deactivation functions for all plugins"""
        self.deactivate_integration_app()
        self.deactivate_integration_globalsettings()
    # endregion

    # region specific integrations
    # region integration_globalsettings
    def activate_integration_globalsettings(self, plugins):
        from common.models import InvenTreeSetting

        if settings.PLUGIN_TESTING or InvenTreeSetting.get_setting('ENABLE_PLUGINS_GLOBALSETTING'):
            logger.info('Registering IntegrationPlugin global settings')
            for slug, plugin in plugins:
                if plugin.mixin_enabled('globalsettings'):
                    plugin_setting = plugin.globalsettingspatterns
                    settings.INTEGRATION_PLUGIN_GLOBALSETTING[slug] = plugin_setting

                    # Add to settings dir
                    InvenTreeSetting.GLOBAL_SETTINGS.update(plugin_setting)

    def deactivate_integration_globalsettings(self):
        from common.models import InvenTreeSetting

        # collect all settings
        plugin_settings = {}
        for _, plugin_setting in settings.INTEGRATION_PLUGIN_GLOBALSETTING.items():
            plugin_settings.update(plugin_setting)

        # remove settings
        for setting in plugin_settings:
            InvenTreeSetting.GLOBAL_SETTINGS.pop(setting)

        # clear cache
        settings.INTEGRATION_PLUGIN_GLOBALSETTING = {}
    # endregion

    # region integration_app
    def activate_integration_app(self, plugins):
        from common.models import InvenTreeSetting

        if settings.PLUGIN_TESTING or InvenTreeSetting.get_setting('ENABLE_PLUGINS_APP'):
            logger.info('Registering IntegrationPlugin apps')
            apps_changed = False

            # add them to the INSTALLED_APPS
            for slug, plugin in plugins:
                if plugin.mixin_enabled('app'):
                    plugin_path = self._get_plugin_path(plugin)
                    if plugin_path not in settings.INSTALLED_APPS:
                        settings.INSTALLED_APPS += [plugin_path]
                        settings.INTEGRATION_APPS_PATHS += [plugin_path]
                        apps_changed = True

            if apps_changed:
                # if apps were changed reload
                if settings.INTEGRATION_APPS_LOADING:
                    settings.INTEGRATION_APPS_LOADING = False
                    self._reload_apps(populate=True)
                self._reload_apps()
                # rediscover models/ admin sites
                self._reload_contrib()
                # update urls - must be last as models must be registered for creating admin routes
                self._update_urls()

    def _reload_contrib(self):
        """fix reloading of contrib apps - models and admin
        this is needed if plugins were loaded earlier and then reloaded as models and admins rely on imports
        those register models and admin in their respective objects (e.g. admin.site for admin)
        """
        for plugin_path in settings.INTEGRATION_APPS_PATHS:
            app_config = apps.get_app_config(plugin_path.split('.')[-1])

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
        """parse plugin path
        the input can be eiter:
        - a local file / dir
        - a package
        """
        try:
            # for local path plugins
            plugin_path = '.'.join(pathlib.Path(plugin.path).relative_to(settings.BASE_DIR).parts)
        except ValueError:
            # plugin is shipped as package
            plugin_path = plugin.PLUGIN_NAME
        return plugin_path

    def deactivate_integration_app(self):
        """deactivate integration app - some magic required"""
        # unregister models from admin
        for plugin_path in settings.INTEGRATION_APPS_PATHS:
            models = []  # the modelrefs need to be collected as poping an item in a iter is not welcomed
            app_name = plugin_path.split('.')[-1]

            # check all models
            for model in apps.get_app_config(app_name).get_models():
                # remove model from admin site
                admin.site.unregister(model)
                models += [model._meta.model_name]

            # unregister the models (yes, models are just kept in multilevel dicts)
            for model in models:
                # remove model from general registry
                apps.all_models[plugin_path].pop(model)

            # clear the registry for that app
             # so that the import trick will work on reloading the same plugin
             # -> the registry is kept for the whole lifecycle
            apps.all_models.pop(app_name)

        # remove plugin from installed_apps
        for plugin in settings.INTEGRATION_APPS_PATHS:
            settings.INSTALLED_APPS.remove(plugin)

        # reset load flag and reload apps
        settings.INTEGRATION_APPS_LOADED = False
        self._reload_apps()

        # update urls to remove the apps from the site admin
        self._update_urls()

    def _update_urls(self):
        from InvenTree.urls import urlpatterns, get_integration_urls

        for index, a in enumerate(urlpatterns):
            if hasattr(a, 'app_name'):
                if a.app_name == 'admin':
                    urlpatterns[index] = url(r'^admin/', admin.site.urls, name='inventree-admin')
                elif a.app_name == 'plugin':
                    integ_urls = get_integration_urls()
                    urlpatterns[index] = url(f'^{settings.PLUGIN_URL}/', include((integ_urls, 'plugin')))
        clear_url_caches()

    def _reload_apps(self, populate: bool = False):
        if populate:
            apps.app_configs = OrderedDict()
            apps.apps_ready = apps.models_ready = apps.loading = apps.ready = False
            apps.clear_cache()
            apps.populate(settings.INSTALLED_APPS)
            return
        settings.INTEGRATION_PLUGINS_RELOADING = True
        apps.set_installed_apps(settings.INSTALLED_APPS)
        settings.INTEGRATION_PLUGINS_RELOADING = False
    # endregion
    # endregion
