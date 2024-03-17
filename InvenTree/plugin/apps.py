"""Apps file for plugin app.

This initializes the plugin mechanisms and handles reloading throughout the lifecycle.
The main code for plugin special sauce is in the plugin registry in `InvenTree/plugin/registry.py`.
"""

import logging

from django.apps import AppConfig

from maintenance_mode.core import set_maintenance_mode

from InvenTree.ready import canAppAccessDatabase, isInMainThread, isInWorkerThread
from plugin import registry

logger = logging.getLogger('inventree')


class PluginAppConfig(AppConfig):
    """AppConfig for plugins."""

    name = 'plugin'

    def ready(self):
        """The ready method is extended to initialize plugins."""
        # skip loading if we run in a background thread

        if not isInMainThread() and not isInWorkerThread():
            return

        if not canAppAccessDatabase(
            allow_test=True, allow_plugins=True, allow_shell=True
        ):
            logger.info('Skipping plugin loading sequence')  # pragma: no cover
        else:
            logger.info('Loading InvenTree plugins')

            if not registry.is_loading:
                # this is the first startup
                try:
                    from common.models import InvenTreeSetting

                    if InvenTreeSetting.get_setting(
                        'PLUGIN_ON_STARTUP', create=False, cache=False
                    ):
                        # make sure all plugins are installed
                        registry.install_plugin_file()
                except Exception:  # pragma: no cover
                    pass

                # Perform a full reload of the plugin registry
                registry.reload_plugins(
                    full_reload=True, force_reload=True, collect=True
                )

                # drop out of maintenance
                # makes sure we did not have an error in reloading and maintenance is still active
                set_maintenance_mode(False)
