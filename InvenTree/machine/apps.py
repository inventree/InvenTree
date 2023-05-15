import logging

from django.apps import AppConfig

from InvenTree.ready import canAppAccessDatabase
from plugin import registry as plg_registry

logger = logging.getLogger('inventree')


class MachineConfig(AppConfig):
    name = 'machine'

    def ready(self) -> None:
        """Initialization method for the Machine app."""
        if not canAppAccessDatabase(allow_test=True) or plg_registry.is_loading:
            logger.info("Skipping machine loading sequence")
            return

        from machine.registry import registry

        logger.info("Loading InvenTree machines")
        registry.initialize()
