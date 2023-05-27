import logging

from django.apps import AppConfig

from InvenTree.ready import (canAppAccessDatabase, isInMainThread,
                             isPluginRegistryLoaded)

logger = logging.getLogger('inventree')


class MachineConfig(AppConfig):
    name = 'machine'

    def ready(self) -> None:
        """Initialization method for the Machine app."""
        if not canAppAccessDatabase(allow_test=True) or not isPluginRegistryLoaded() or not isInMainThread():
            logger.debug("Machine app: Skipping machine loading sequence")
            return

        from machine import registry

        logger.info("Loading InvenTree machines")
        registry.initialize()

        from InvenTree.wsgi import shutdown_signal
        shutdown_signal.connect(self.on_shutdown, dispatch_uid="machine.on_shutdown")

    def on_shutdown(self, **kwargs):
        # gracefully shutdown machines
        from machine import registry

        logger.debug("Shutting down InvenTree machines")
        registry.terminate()

        import time
        time.sleep(3)
        print("### After sleep")
