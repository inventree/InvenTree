# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.apps import AppConfig

from plugin.registry import plugins


class PluginAppConfig(AppConfig):
    name = 'plugin'

    def ready(self):
        if not plugins.is_loading:
            plugins.collect_plugins()
            plugins.load_plugins()
