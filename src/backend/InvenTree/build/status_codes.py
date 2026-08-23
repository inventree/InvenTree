"""Build status codes."""

from django.utils.translation import gettext_lazy as _

from generic.states import ColorEnum, StatusCode


class BuildStatus(StatusCode):
    """Build status codes."""

    PENDING = 10, _('Pending'), ColorEnum.secondary  # Build is pending / active
    PRODUCTION = 20, _('Production'), ColorEnum.primary  # Build is in production
    ON_HOLD = 25, _('On Hold'), ColorEnum.warning  # Build is on hold
    CANCELLED = 30, _('Cancelled'), ColorEnum.danger  # Build was cancelled
    COMPLETE = 40, _('Complete'), ColorEnum.success  # Build is complete


class BuildStatusGroups:
    """Groups for BuildStatus codes."""

    ACTIVE_CODES = [
        BuildStatus.PENDING.value,
        BuildStatus.ON_HOLD.value,
        BuildStatus.PRODUCTION.value,
    ]

    COMPLETE = [BuildStatus.COMPLETE.value]


class RepairOrderStatus(StatusCode):
    """Defines a set of status codes for a RepairOrder."""

    PENDING = 10, _('Pending'), ColorEnum.secondary  # Repair is pending
    IN_PROGRESS = 20, _('In Progress'), ColorEnum.primary  # Repair is underway
    ON_HOLD = 25, _('On Hold'), ColorEnum.warning  # Repair is on hold
    COMPLETE = 30, _('Complete'), ColorEnum.success  # Repair has been completed
    CANCELLED = 40, _('Cancelled'), ColorEnum.danger  # Repair was cancelled


class RepairOrderStatusGroups:
    """Groups for RepairOrderStatus codes."""

    # Open orders
    OPEN = [
        RepairOrderStatus.PENDING.value,
        RepairOrderStatus.ON_HOLD.value,
        RepairOrderStatus.IN_PROGRESS.value,
    ]

    COMPLETE = [RepairOrderStatus.COMPLETE.value]

    CANCELLED = [RepairOrderStatus.CANCELLED.value]
