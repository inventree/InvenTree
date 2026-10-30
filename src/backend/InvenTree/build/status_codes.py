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


class NonConformanceStatus(StatusCode):
    """Status codes for a NonConformance report (NCR).

    Attributes:
        PENDING: The NCR has been raised, but not yet investigated
        IN_PROGRESS: Root cause investigation is underway
        CANCELLED: The NCR was raised in error, or withdrawn
        COMPLETE: The NCR has been closed out
    """

    PENDING = 10, _('Pending'), ColorEnum.secondary
    IN_PROGRESS = 20, _('In Progress'), ColorEnum.primary
    CANCELLED = 30, _('Cancelled'), ColorEnum.danger
    COMPLETE = 40, _('Complete'), ColorEnum.success


class NonConformanceStatusGroups:
    """Groups for NonConformanceStatus codes."""

    OPEN_CODES = [
        NonConformanceStatus.PENDING.value,
        NonConformanceStatus.IN_PROGRESS.value,
    ]

    CLOSED_CODES = [
        NonConformanceStatus.COMPLETE.value,
        NonConformanceStatus.CANCELLED.value,
    ]


class NonConformanceDisposition(StatusCode):
    """Disposition codes for a NonConformance report (NCR).

    Tracked separately from NonConformanceStatus - status is "where is this NCR in its
    lifecycle", disposition is "what did we decide to do with the affected material".

    Attributes:
        PENDING: No disposition has been decided yet (default value for a newly-linked item)
        USE_AS_IS: The item is acceptable to use without further action
        REWORK: The item is to be reworked to meet requirements
        REPAIR: The item is to be repaired
        SCRAP: The item is to be scrapped
        RETURN_TO_SUPPLIER: The item is to be returned to the supplier
    """

    PENDING = 10, _('Pending'), ColorEnum.secondary
    USE_AS_IS = 20, _('Use As Is'), ColorEnum.warning
    REWORK = 30, _('Rework'), ColorEnum.primary
    REPAIR = 40, _('Repair'), ColorEnum.primary
    SCRAP = 50, _('Scrap'), ColorEnum.danger
    RETURN_TO_SUPPLIER = 60, _('Return to Supplier'), ColorEnum.danger
