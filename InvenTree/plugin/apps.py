# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.apps import AppConfig
from django.conf import settings


class PluginConfig(AppConfig):
    name = 'plugin'

    def ready(self):
        from common.models import InvenTreeSetting

        if InvenTreeSetting.get_setting('ENABLE_PLUGINS_SETTING'):
            for slug, plugin in settings.INTEGRATION_PLUGIN_LIST.items():
                if plugin.mixin_enabled('settings'):
                    plugin_setting = plugin.settingspatterns
                    settings.INTEGRATION_PLUGIN_SETTING[slug] = plugin_setting
                    settings.INTEGRATION_PLUGIN_SETTINGS.update(plugin_setting)
