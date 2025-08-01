"""App config for common app."""

from django.apps import AppConfig

import structlog

import InvenTree.ready
from common.settings import (
    get_global_setting,
    global_setting_overrides,
    set_global_setting,
)

logger = structlog.get_logger('inventree')


class CommonConfig(AppConfig):
    """AppConfig for common app.

    Clears system wide flags on ready.
    """

    name = 'common'

    def ready(self):
        """Initialize restart flag clearance on startup."""
        if InvenTree.ready.isRunningMigrations():
            return

        self.clear_restart_flag()
        self.override_global_settings()

    def clear_restart_flag(self):
        """Clear the SERVER_RESTART_REQUIRED setting."""
        try:
            if get_global_setting(
                'SERVER_RESTART_REQUIRED', backup_value=False, create=False, cache=False
            ):
                logger.info('Clearing SERVER_RESTART_REQUIRED flag')

                if not InvenTree.ready.isImportingData():
                    set_global_setting('SERVER_RESTART_REQUIRED', False, None)
        except Exception:
            pass

    def override_global_settings(self):
        """Update global settings based on environment variables."""
        overrides = global_setting_overrides()

        if not overrides:
            return

        for key, value in overrides.items():
            try:
                current_value = get_global_setting(key, create=False)

                if current_value != value:
                    logger.info(
                        'INVE-I1: Overriding global setting: %s = %s',
                        value,
                        current_value,
                    )
                    set_global_setting(key, value, None, create=True)

            except Exception:
                logger.warning('Failed to override global setting %s -> %s', key, value)
                continue
