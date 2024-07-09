"""Build status codes."""

from django.utils.translation import gettext_lazy as _

from generic.states import StatusCode


class BuildStatus(StatusCode):
    """Build status codes."""

    PENDING = 10, _('Pending'), 'secondary'  # Build is pending / active
    PRODUCTION = 20, _('Production'), 'primary'  # BuildOrder is in production
    CANCELLED = 30, _('Cancelled'), 'danger'  # Build was cancelled
    COMPLETE = 40, _('Complete'), 'success'  # Build is complete


class BuildStatusGroups:
    """Groups for BuildStatus codes."""

    ACTIVE_CODES = [BuildStatus.PENDING.value, BuildStatus.PRODUCTION.value]
