"""Apps file for plugin app.

This initializes the plugin mechanisms and handles reloading throughout the lifecycle.
The main code for plugin special sauce is in the plugin registry in `InvenTree/plugin/registry.py`.
"""

import logging
import pathlib
import sys

from django.apps import AppConfig
from django.conf import settings

from maintenance_mode.core import set_maintenance_mode

from InvenTree.config import get_plugin_dir
from InvenTree.ready import canAppAccessDatabase, isInMainThread, isInWorkerThread
from plugin import registry

logger = logging.getLogger('inventree')


class PluginAppConfig(AppConfig):
    """AppConfig for plugins."""

    name = 'plugin'

    def ready(self):
        """The ready method is extended to initialize plugins."""
        self.update_python_path()

        if not isInMainThread() and not isInWorkerThread():
            return

        if not canAppAccessDatabase(
            allow_test=True, allow_plugins=True, allow_shell=True
        ):
            logger.info('Skipping plugin loading sequence')  # pragma: no cover
        else:
            logger.info('Loading InvenTree plugins')

            if not registry.is_loading:
                # Perform a full reload of the plugin registry
                registry.reload_plugins(
                    full_reload=True, force_reload=True, collect=True
                )

                # drop out of maintenance
                # makes sure we did not have an error in reloading and maintenance is still active
                set_maintenance_mode(False)

    def update_python_path(self):
        """Update the PYTHONPATH to include the plugin directory."""
        if not settings.PLUGINS_ENABLED:
            # Custom plugins disabled - no need to update PYTHONPATH
            logger.info('Custom plugins are not enabled')
            return

        plugin_dir = get_plugin_dir()

        if not plugin_dir:
            logger.warning('Plugins directory not specified')
            return

        if plugin_dir := get_plugin_dir():
            path = pathlib.Path(plugin_dir)

            if not path.exists():
                try:
                    path.mkdir(parents=True, exist_ok=True)
                except Exception:
                    logger.error(f'Failed to create plugin directory: {plugin_dir}')
                    return

            if plugin_dir not in sys.path:
                sys.path.append(plugin_dir)
