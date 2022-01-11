# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from django.apps import AppConfig
from django.conf import settings

from maintenance_mode.core import set_maintenance_mode

from plugin import plugin_registry


logger = logging.getLogger('inventree')


class PluginAppConfig(AppConfig):
    name = 'plugin'

    def ready(self):

        if settings.PLUGINS_ENABLED:
            logger.info('Loading InvenTree plugins')

            if not plugin_registry.is_loading:
                # this is the first startup
                plugin_registry.collect_plugins()
                plugin_registry.load_plugins()

                # drop out of maintenance
                # makes sure we did not have an error in reloading and maintenance is still active
                set_maintenance_mode(False)
