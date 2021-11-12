# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import importlib
import pathlib
import logging
from typing import OrderedDict

from django.apps import AppConfig, apps
from django.conf import settings
from django.db.utils import OperationalError, ProgrammingError

try:
    from importlib import metadata
except:
    import importlib_metadata as metadata

from plugin import plugins as inventree_plugins
from plugin.integration import IntegrationPluginBase

logger = logging.getLogger('inventree')


class PluginConfig(AppConfig):
    name = 'plugin'

    def ready(self):
        from common.models import InvenTreeSetting
        from plugin.models import PluginConfig

        # Collect plugins from paths
        for plugin in settings.PLUGIN_DIRS:
            modules = inventree_plugins.get_plugins(importlib.import_module(plugin), IntegrationPluginBase, True)
            if modules:
                [settings.PLUGINS.append(item) for item in modules]

        # Collect plugins from setup entry points
        for entry in metadata.entry_points().get('inventree_plugins', []):
            plugin = entry.load()
            plugin.is_package = True
            settings.PLUGINS.append(plugin)

        # Log found plugins
        logger.info(f'Found {len(settings.PLUGINS)} plugins!')
        logger.info(", ".join([a.__module__ for a in settings.PLUGINS]))

        # Initialize integration plugins
        for plugin in inventree_plugins.load_integration_plugins():
            # check if package
            was_packaged = getattr(plugin, 'is_package', False)

            # check if activated
            # these checks only use attributes - never use plugin supplied functions -> that would lead to arbitrary code execution!!
            plug_name = plugin.PLUGIN_NAME
            plug_key = plugin.PLUGIN_SLUG if getattr(plugin, 'PLUGIN_SLUG', None) else plug_name
            plugin_db_setting, _ = PluginConfig.objects.get_or_create(key=plug_key, name=plug_name)

            if plugin_db_setting.active:
                # init package
                # now we can be sure that an admin has activated the plugin -> as of Nov 2021 there are not many checks in place
                # but we could enhance those to check signatures, run the plugin against a whitelist etc.
                logger.info(f'Loading integration plugin {plugin.PLUGIN_NAME}')
                plugin = plugin()
                logger.info(f'Loaded integration plugin {plugin.slug}')
                plugin.is_package = was_packaged
                # safe reference
                settings.INTEGRATION_PLUGINS[plugin.slug] = plugin

        # activate integrations
        plugins = settings.INTEGRATION_PLUGINS.items()

        try:
            # if plugin settings are enabled enhance the settings
            if settings.TESTING or InvenTreeSetting.get_setting('ENABLE_PLUGINS_SETTING'):
                for slug, plugin in plugins:
                    if plugin.mixin_enabled('settings'):
                        plugin_setting = plugin.settingspatterns
                        settings.INTEGRATION_PLUGIN_SETTING[slug] = plugin_setting

                        # Add to settings dir
                        InvenTreeSetting.GLOBAL_SETTINGS.update(plugin_setting)

            # if plugin apps are enabled
            if settings.TESTING or ((not settings.INTEGRATION_APPS_LOADED) and InvenTreeSetting.get_setting('ENABLE_PLUGINS_APP')):
                settings.INTEGRATION_APPS_LOADED = True  # ensure this section will not run again
                apps_changed = False

                # add them to the INSTALLED_APPS
                for slug, plugin in plugins:
                    if plugin.mixin_enabled('app'):
                        try:
                            # for local path plugins
                            plugin_path = '.'.join(pathlib.Path(plugin.path).relative_to(settings.BASE_DIR).parts)
                        except ValueError:
                            # plugin is shipped as package
                            plugin_path = plugin.PLUGIN_NAME
                        if plugin_path not in settings.INSTALLED_APPS:
                            settings.INSTALLED_APPS += [plugin_path]
                            apps_changed = True

                # if apps were changed reload
                # TODO this is a bit jankey to be honest
                if apps_changed:
                    apps.app_configs = OrderedDict()
                    apps.apps_ready = apps.models_ready = apps.loading = apps.ready = False
                    apps.clear_cache()
                    apps.populate(settings.INSTALLED_APPS)
        except (OperationalError, ProgrammingError):
            # Exception if the database has not been migrated yet
            pass
