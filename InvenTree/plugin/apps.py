# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.apps import AppConfig
from maintenance_mode.core import set_maintenance_mode

from plugin import plugin_registry


class PluginAppConfig(AppConfig):
    name = 'plugin'

    def ready(self):
        if not plugin_registry.is_loading:
            # this is the first startup
            plugin_registry.collect_plugins()
            plugin_registry.load_plugins()

            # drop out of maintenance
            # makes sure we did not have an error in reloading and maintenance is still active
            set_maintenance_mode(False)
