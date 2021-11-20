# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.apps import AppConfig
from django.conf import settings

from plugin.registry import plugins


class PluginAppConfig(AppConfig):
    name = 'plugin'

    def ready(self):
        if not settings.INTEGRATION_PLUGINS_RELOADING:
            plugins.collect_plugins()
            plugins.load_plugins()
