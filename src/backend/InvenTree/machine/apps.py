"""Django machine app config."""

from django.apps import AppConfig
from django.db.utils import OperationalError, ProgrammingError

import structlog

from InvenTree.ready import (
    canAppAccessDatabase,
    isImportingData,
    isInMainThread,
    isPluginRegistryLoaded,
    isRunningMigrations,
)

logger = structlog.get_logger('inventree')


class MachineConfig(AppConfig):
    """AppConfig class for the machine app."""

    name = 'machine'

    def ready(self) -> None:
        """Initialization method for the machine app."""
        if (
            not canAppAccessDatabase(allow_test=True)
            or not isPluginRegistryLoaded()
            or isRunningMigrations()
            or isImportingData()
        ):
            logger.debug('Machine app: Skipping machine loading sequence')
            return

        from machine import registry

        try:
            logger.info('Loading InvenTree machines')
            registry.initialize(main=isInMainThread())
        except (OperationalError, ProgrammingError):
            # Database might not yet be ready
            logger.warn('Database was not ready for initializing machines')
