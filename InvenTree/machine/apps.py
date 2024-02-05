"""Django machine app config."""

import logging

from django.apps import AppConfig

from InvenTree.ready import (
    canAppAccessDatabase,
    isInMainThread,
    isPluginRegistryLoaded,
    isRunningMigrations,
)

logger = logging.getLogger('inventree')


class MachineConfig(AppConfig):
    """AppConfig class for the machine app."""

    name = 'machine'

    def ready(self) -> None:
        """Initialization method for the machine app."""
        if (
            not canAppAccessDatabase(allow_test=True)
            or not isPluginRegistryLoaded()
            or not isInMainThread()
            or isRunningMigrations()
        ):
            logger.debug('Machine app: Skipping machine loading sequence')
            return

        from machine import registry

        logger.info('Loading InvenTree machines')
        registry.initialize()
