"""Rule objects for approval system."""
import logging

import InvenTree.helpers
from common.models import InvenTreeSetting

logger = logging.getLogger('inventree')


class ApprovalRule:
    """Base class for notification methods."""

    NAME = ''
    DESCRIPTION = None
    IDENTIFIER = None
    SETTING = None

    def settings_value(self, cast=None):
        """Return the value of the setting."""
        if self.SETTING is None:
            return None
        sett = InvenTreeSetting.get_setting(self.SETTING)
        return sett

    def check(self, approval, target, decisions: list):
        """Check if the rule is fulfilled.

        Returns:
            bool: True if the approval is accepted, False if the approval is rejected, None if unconclusive.
        """
        raise NotImplementedError('A ApprovalRule must define a `check` method')


class RuleRegistryClass:
    """Class that acts as registry for all available approval rule definitions."""

    items = None

    def collect(self):
        """Collect all classes in the environment that are approval rule definitions."""
        logger.debug('Collecting approval rule definitions')
        rules = InvenTree.helpers.inheritors(ApprovalRule)
        registry.items = {x.IDENTIFIER: x for x in rules}
        logger.debug(f'Found {len(registry.items)} approval rule definitions')


registry = RuleRegistryClass()
