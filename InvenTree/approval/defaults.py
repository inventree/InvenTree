"""Default Approval Rules for InvenTree."""
from django.utils.translation import gettext_lazy as _

from .rules import ApprovalRule


class GenericMinimumApproversRule(ApprovalRule):
    """Approval Rule that specifies the minimum required number of approvers - set by the database."""
    NAME = _('Minimum Approvers')
    DESCRIPTION = _('Minimum number of approvers required for approval')
    IDENTIFIER = 'schema.inventree.org/rules/generic_minimum_approvers.1-0'
    SETTING = 'APPROVAL_MINIMUM_APPROVERS'

    def check(self, approval, target, decisions):
        """True if minimum number of approvers is reached."""
        positive_decisions = [x for x in decisions if x.decision]
        if len(positive_decisions) == 0:
            return None
        if len(positive_decisions) >= self.settings_value(int):
            return True
        return None


class GenericMaximumDenierRule(ApprovalRule):
    """Approval Rule that specifies the maximum number of deniers - set by the database."""
    NAME = _('Maximum Deniers')
    DESCRIPTION = _('Maximum number of deniers required for rejection')
    IDENTIFIER = 'schema.inventree.org/rules/generic_maximum_deniers.1-0'
    SETTING = 'APPROVAL_MAXIMUM_DENIERS'

    def check(self, approval, target, decisions):
        """True if maximum number of deniers is reached."""
        negative_decisions = [x for x in decisions if not x.decision]
        if len(negative_decisions) == 0:
            return None
        if len(negative_decisions) >= self.settings_value(int):
            return False
        return None


DefaultApprovalRules: list[ApprovalRule] = [
    GenericMinimumApproversRule,
    GenericMaximumDenierRule,
]
