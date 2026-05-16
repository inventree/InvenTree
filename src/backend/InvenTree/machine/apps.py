"""Django machine app config."""

from django.apps import AppConfig
from django.db.utils import OperationalError, ProgrammingError

import structlog

from InvenTree.ready import (
    canAppAccessDatabase,
    ignore_ready_warning,
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

        try:
            self.initialize_registry()
        except (OperationalError, ProgrammingError):
            # Database might not yet be ready
            logger.warn('Database was not ready for initializing machines')

    @ignore_ready_warning
    def initialize_registry(self):
        """Initialize the machine registry."""
        from machine import registry

        if not registry.is_ready:
            logger.info('Loading InvenTree machines')
            registry.initialize(main=isInMainThread())
