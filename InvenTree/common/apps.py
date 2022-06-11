"""App config for common app."""

import logging

from django.apps import AppConfig

logger = logging.getLogger('inventree')


class CommonConfig(AppConfig):
    """AppConfig for common app.

    Clears system wide flags on ready.
    """

    name = 'common'

    def ready(self):
        """Initialize restart flag clearance on startup."""
        self.clear_restart_flag()

    def clear_restart_flag(self):
        """Clear the SERVER_RESTART_REQUIRED setting."""
        try:
            import common.models

            if common.models.InvenTreeSetting.get_setting('SERVER_RESTART_REQUIRED', backup_value=False, create=False, cache=False):
                logger.info("Clearing SERVER_RESTART_REQUIRED flag")
                common.models.InvenTreeSetting.set_setting('SERVER_RESTART_REQUIRED', False, None)
        except Exception:
            pass
