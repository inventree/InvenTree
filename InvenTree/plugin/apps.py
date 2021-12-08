# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.apps import AppConfig
from maintenance_mode.core import set_maintenance_mode

from plugin.registry import plugins


class PluginAppConfig(AppConfig):
    name = 'plugin'

    def ready(self):
        if not plugins.is_loading:
            # this is the first startup
            plugins.collect_plugins()
            plugins.load_plugins()

            # drop out of maintenance
            # makes sure we did not have an error in reloading and maintenance is still active
            set_maintenance_mode(False)
