"""Custom backend implementations."""

import logging
import time

from django.db.utils import IntegrityError, OperationalError, ProgrammingError

from maintenance_mode.backends import AbstractStateBackend

import common.models
import InvenTree.ready

logger = logging.getLogger('inventree')


class InvenTreeMaintenanceModeBackend(AbstractStateBackend):
    """Custom backend for managing state of maintenance mode.

    Stores the current state of the maintenance mode in the database,
    using an InvenTreeSetting object.
    """

    SETTING_KEY = '_MAINTENANCE_MODE'

    def get_value(self) -> bool:
        """Get the current state of the maintenance mode.

        Returns:
            bool: True if maintenance mode is active, False otherwise.
        """
        try:
            setting = common.models.InvenTreeSetting.objects.get(key=self.SETTING_KEY)
            value = InvenTree.helpers.str2bool(setting.value)
        except common.models.InvenTreeSetting.DoesNotExist:
            # Database is accessible, but setting is not available - assume False
            value = False
        except (IntegrityError, OperationalError, ProgrammingError):
            # Database is inaccessible - assume we are not in maintenance mode
            logger.warning('Failed to read maintenance mode state - assuming True')
            value = True

        logger.debug('Maintenance mode state: %s', value)

        return value

    def set_value(self, value: bool, retries: int = 5):
        """Set the state of the maintenance mode."""
        logger.debug('Setting maintenance mode state: %s', value)

        while retries > 0:
            try:
                common.models.InvenTreeSetting.set_setting(self.SETTING_KEY, value)

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
