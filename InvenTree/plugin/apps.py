# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import pathlib
from typing import OrderedDict

from django.apps import AppConfig, apps
from django.conf import settings


class PluginConfig(AppConfig):
    name = 'plugin'

    def ready(self):
        from common.models import InvenTreeSetting
        plugins = settings.INTEGRATION_PLUGINS.items()

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
                    plugin_path = '.'.join(pathlib.Path(plugin.path).relative_to(settings.BASE_DIR).parts)
                    if plugin_path not in  settings.INSTALLED_APPS:
                        settings.INSTALLED_APPS += [plugin_path]
                        apps_changed = True

            # if apps were changed reload
            # TODO this is a bit jankey to be honest
            if apps_changed:
                apps.app_configs = OrderedDict()
                apps.apps_ready = apps.models_ready = apps.loading = apps.ready = False
                apps.clear_cache()
                apps.populate(settings.INSTALLED_APPS)
