"""Apps file for plugin app.

This initializes the plugin mechanisms and handles reloading throughout the lifecycle.
The main code for plugin special sauce is in the plugin registry in `InvenTree/plugin/registry.py`.
"""

from django.apps import AppConfig

import structlog
from maintenance_mode.core import set_maintenance_mode

from InvenTree.ready import (
    canAppAccessDatabase,
    ignore_ready_warning,
    isInMainThread,
    isInWorkerThread,
)
from plugin import registry

logger = structlog.get_logger('inventree')


class PluginAppConfig(AppConfig):
    """AppConfig for plugins."""

    name = 'plugin'

    def ready(self):
        """The ready method is extended to initialize plugins."""
        self.reload_plugin_registry()

    @ignore_ready_warning
    def reload_plugin_registry(self):
        """Reload the plugin registry."""
        if not isInMainThread() and not isInWorkerThread():
            return

        if not canAppAccessDatabase(
            allow_test=True, allow_plugins=True, allow_shell=True
        ):
            logger.info('Skipping plugin loading sequence')  # pragma: no cover
        else:
            logger.info('Loading InvenTree plugins')

            # Ensure registry ready state is reset for test DB
            registry.set_ready()

            # Always reload plugins
            registry.reload_plugins()

            set_maintenance_mode(False)
