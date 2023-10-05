"""App config for common app."""

import logging

from django.apps import AppConfig

from InvenTree.ready import canAppAccessDatabase, isImportingData

logger = logging.getLogger('inventree')


class CommonConfig(AppConfig):
    """AppConfig for common app.

    Clears system wide flags on ready.
    """

    name = 'common'

    def ready(self):
        """Initialize restart flag clearance on startup."""
        self.clear_restart_flag()
        self.fill_default_settings()

    def clear_restart_flag(self):
        """Clear the SERVER_RESTART_REQUIRED setting."""
        try:
            import common.models

            if common.models.InvenTreeSetting.get_setting('SERVER_RESTART_REQUIRED', backup_value=False, create=False, cache=False):
                logger.info("Clearing SERVER_RESTART_REQUIRED flag")

                if not isImportingData():
                    common.models.InvenTreeSetting.set_setting('SERVER_RESTART_REQUIRED', False, None)
        except Exception:
            pass

    def fill_default_settings(self):
        """Fill in default values for settings where they don't exist"""

        if isImportingData():
            return

        if not canAppAccessDatabase(allow_test=True):
            return

        try:
            from django.contrib.auth import get_user_model

            import common.models
        except Exception:
            return

        try:
            # Fill in default values for global settings
            logger.debug("Filling default values for global settings")
            for key in common.models.InvenTreeSetting.SETTINGS.keys():
                common.models.InvenTreeSetting.get_setting(key, create=True, cache=False)
        except Exception as exc:
            logger.info("Failed to fill default values for global settings: %s", str(type(exc)))
            pass

        try:
            # Fill in default values for user settings
            logger.debug("Filling default values for user settings")
            for user in get_user_model().objects.all():
                for key in common.models.UserSetting.SETTINGS.keys():
                    common.models.UserSetting.get_setting(key, user=user, create=True, cache=False)

        except Exception as exc:
            logger.info("Failed to fill default values for user settings: %s", str(type(exc)))
            pass
