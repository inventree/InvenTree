"""Custom backend implementations."""

import logging
import time

from django.db.utils import IntegrityError, OperationalError, ProgrammingError

from maintenance_mode.backends import AbstractStateBackend

import common.models
import InvenTree.helpers

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
        value = InvenTree.helpers.str2bool(
            common.models.InvenTreeSetting.get_setting(
                self.SETTING_KEY, backup_value=False, create=False, cache=False
            )
        )

        logger.debug('Maintenance mode state: {state}'.format(state=value))

        return value

    def set_value(self, value: bool, retries: int = 5):
        """Set the state of the maintenance mode."""
        logger.debug('Setting maintenance mode state: {state}'.format(state=value))

        while retries > 0:
            try:
                common.models.InvenTreeSetting.set_setting(self.SETTING_KEY, value)

                # Read the value back to confirm
                if self.get_value() == value:
                    break
            except (IntegrityError, OperationalError, ProgrammingError):
                logger.warning(
                    'Failed to set maintenance mode state in database (%s retries left)',
                    retries,
                )
                time.sleep(0.1)

            retries -= 1
