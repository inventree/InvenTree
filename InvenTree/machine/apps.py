import logging

from django.apps import AppConfig

from InvenTree.ready import canAppAccessDatabase, isPluginRegistryLoaded

logger = logging.getLogger('inventree')


class MachineConfig(AppConfig):
    name = 'machine'

    def ready(self) -> None:
        """Initialization method for the Machine app."""
        if not canAppAccessDatabase(allow_test=True) or not isPluginRegistryLoaded():
            logger.info("Skipping machine loading sequence")
            return

        from machine.registry import registry

        logger.info("Loading InvenTree machines")
        registry.initialize()
