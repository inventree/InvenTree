"""Custom backend implementations."""

import datetime
import logging
import time

from django.db.utils import IntegrityError, OperationalError, ProgrammingError

from maintenance_mode.backends import AbstractStateBackend

import common.models

logger = logging.getLogger('inventree')


class InvenTreeMaintenanceModeBackend(AbstractStateBackend):
    """Custom backend for managing state of maintenance mode.

    Stores a timestamp in the database to determine when maintenance mode will elapse.
    """

    SETTING_KEY = '_MAINTENANCE_MODE'

    def get_value(self) -> bool:
        """Get the current state of the maintenance mode.

        Returns:
            bool: True if maintenance mode is active, False otherwise.
        """
        try:
            setting = common.models.InvenTreeSetting.objects.get(key=self.SETTING_KEY)
            value = str(setting.value).strip()
        except common.models.InvenTreeSetting.DoesNotExist:
            # Database is accessible, but setting is not available - assume False
            return False
        except (IntegrityError, OperationalError, ProgrammingError):
            # Database is inaccessible - assume we are not in maintenance mode
            logger.debug('Failed to read maintenance mode state - assuming True')
            return True

        # Extract timestamp from string
        try:
            # If the timestamp is in the past, we are now *out* of maintenance mode
            timestamp = datetime.datetime.fromisoformat(value)
            return timestamp > datetime.datetime.now()
        except ValueError:
            # If the value is not a valid timestamp, assume maintenance mode is not active
            return False

    def set_value(self, value: bool, retries: int = 5, minutes: int = 5):
        """Set the state of the maintenance mode.

        Instead of simply writing "true" or "false" to the setting,
        we write a timestamp to the setting, which is used to determine
        when maintenance mode will elapse.
        This ensures that we will always *exit* maintenance mode after a certain time period.
        """
        logger.debug('Setting maintenance mode state: %s', value)

        if value:
            # Save as isoformat
            timestamp = datetime.datetime.now() + datetime.timedelta(minutes=minutes)
            timestamp = timestamp.isoformat()
        else:
            # Blank timestamp means maintenance mode is not active
            timestamp = ''

        while retries > 0:
            try:
                common.models.InvenTreeSetting.set_setting(self.SETTING_KEY, timestamp)

                # Read the value back to confirm
                if self.get_value() == value:
                    break
            except (IntegrityError, OperationalError, ProgrammingError):
                # In the database is locked, then
                logger.debug(
                    'Failed to set maintenance mode state (%s retries left)', retries
                )
                time.sleep(0.1)

            retries -= 1

            if retries == 0:
                logger.warning('Failed to set maintenance mode state')
