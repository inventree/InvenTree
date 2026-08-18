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


class NonConformanceStatus(StatusCode):
    """Status codes for a NonConformance report (NCR)."""

    OPEN = (
        10,
        _('Open'),
        ColorEnum.secondary,
    )  # NCR has been raised, not yet investigated
    INVESTIGATING = (
        20,
        _('Investigating'),
        ColorEnum.primary,
    )  # Root cause investigation underway
    DISPOSITIONED = (
        30,
        _('Dispositioned'),
        ColorEnum.warning,
    )  # Disposition has been decided
    CLOSED = 40, _('Closed'), ColorEnum.success  # NCR has been closed out
    CANCELLED = (
        50,
        _('Cancelled'),
        ColorEnum.danger,
    )  # NCR was raised in error / withdrawn


class NonConformanceStatusGroups:
    """Groups for NonConformanceStatus codes."""

    OPEN_CODES = [
        NonConformanceStatus.OPEN.value,
        NonConformanceStatus.INVESTIGATING.value,
        NonConformanceStatus.DISPOSITIONED.value,
    ]

    CLOSED_CODES = [
        NonConformanceStatus.CLOSED.value,
        NonConformanceStatus.CANCELLED.value,
    ]


class NonConformanceDisposition(StatusCode):
    """Disposition codes for a NonConformance report (NCR).

    Tracked separately from NonConformanceStatus - status is "where is this NCR in its
    lifecycle", disposition is "what did we decide to do with the affected material".
    """

    PENDING = 10, _('Pending'), ColorEnum.secondary
    USE_AS_IS = 20, _('Use As Is'), ColorEnum.warning
    REWORK = 30, _('Rework'), ColorEnum.primary
    REPAIR = 40, _('Repair'), ColorEnum.primary
    SCRAP = 50, _('Scrap'), ColorEnum.danger
    RETURN_TO_SUPPLIER = 60, _('Return to Supplier'), ColorEnum.danger
