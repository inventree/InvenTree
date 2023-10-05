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

            existing_keys = common.models.InvenTreeSetting.objects.values_list('key', flat=True)
            settings_keys = common.models.InvenTreeSetting.SETTINGS.keys()

            missing_keys = set(settings_keys) - set(existing_keys)

            common.models.InvenTreeSetting.objects.bulk_create([
                common.models.InvenTreeSetting(
                    key=key,
                    value=common.models.InvenTreeSetting.get_setting_default(key)
                ) for key in missing_keys if not key.startswith('_')
            ])

        except Exception as exc:
            logger.info("Failed to fill default values for global settings: %s", str(type(exc)))
            pass

        try:
            # Fill in default values for user settings
            logger.debug("Filling default values for user settings")
            settings_keys = common.models.InvenTreeUserSetting.SETTINGS.keys()

            for user in get_user_model().objects.all():
                existing_keys = common.models.InvenTreeUserSetting.objects.filter(user=user).values_list('key', flat=True)
                missing_keys = set(settings_keys) - set(existing_keys)

                common.models.InvenTreeUserSetting.objects.bulk_create([
                    common.models.InvenTreeUserSetting(
                        user=user,
                        key=key,
                        value=common.models.InvenTreeUserSetting.get_setting_default(key)
                    ) for key in missing_keys if not key.startswith('_')
                ])

        except Exception as exc:
            logger.info("Failed to fill default values for user settings: %s", str(type(exc)))
            pass
