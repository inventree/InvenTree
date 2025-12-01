"""App config for common app."""

from django.apps import AppConfig

import structlog

import InvenTree.ready
from common.settings import get_global_setting, set_global_setting
from InvenTree.ready import ignore_ready_warning

logger = structlog.get_logger('inventree')


class CommonConfig(AppConfig):
    """AppConfig for common app.

    Clears system wide flags on ready.
    """

    name = 'common'

    def ready(self):
        """Initialize restart flag clearance on startup."""
        from InvenTree.ready import setAppLoaded

        setAppLoaded(self.name)

        if InvenTree.ready.isRunningMigrations():  # pragma: no cover
            return

        self.clear_restart_flag()

    @ignore_ready_warning
    def clear_restart_flag(self):
        """Clear the SERVER_RESTART_REQUIRED setting."""
        try:
            if get_global_setting(
                'SERVER_RESTART_REQUIRED', backup_value=False, create=False, cache=False
            ):
                logger.info('Clearing SERVER_RESTART_REQUIRED flag')

                if not InvenTree.ready.isImportingData():
                    set_global_setting('SERVER_RESTART_REQUIRED', False, None)
        except Exception:  # pragma: no cover
            pass
