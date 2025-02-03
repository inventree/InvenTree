"""App config for common app."""

from django.apps import AppConfig

import structlog

import InvenTree.ready
from common.settings import get_global_setting, set_global_setting

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
        self.build_default_settings()

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

    def build_default_settings(self):
        """Clear the settings cache."""
        if (
            InvenTree.ready.isImportingData()
            or InvenTree.ready.isRunningMigrations()
            or InvenTree.ready.isRebuildingData()
            or InvenTree.ready.isRunningBackup()
            or InvenTree.ready.isInTestMode()
        ):
            return

        try:
            from django.contrib.auth.models import User

            from common.models import InvenTreeSetting, InvenTreeUserSetting

            # Rebuild the settings values
            InvenTreeSetting.build_default_values(cache=False)

            for user in User.objects.all():
                InvenTreeUserSetting.build_default_values(user=user, cache=False)
        except Exception:
            # Database not ready
            pass
