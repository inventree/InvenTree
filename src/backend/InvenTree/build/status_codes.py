"""Build status codes."""

from django.utils.translation import gettext_lazy as _

from generic.states import ColorEnum, StatusCode


class BuildStatus(StatusCode):
    """Build status codes.

    Attributes:
        PENDING: Build is pending / active
        PRODUCTION: Build is in production
        ON_HOLD: Build is on hold
        CANCELLED: Build was cancelled
        COMPLETE: Build is complete
    """

    PENDING = 10, _('Pending'), ColorEnum.secondary
    PRODUCTION = 20, _('Production'), ColorEnum.primary
    ON_HOLD = 25, _('On Hold'), ColorEnum.warning
    CANCELLED = 30, _('Cancelled'), ColorEnum.danger
    COMPLETE = 40, _('Complete'), ColorEnum.success


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
