"""Event definitions and triggers for the build app."""

from generic.events import BaseEventEnum


class BuildEvents(BaseEventEnum):
    """Event enumeration for the Build app."""

    # Build order events
    HOLD = 'build.hold'
    ISSUED = 'build.issued'
    CANCELLED = 'build.cancelled'
    COMPLETED = 'build.completed'
    OVERDUE = 'build.overdue_build_order'

    STOCK_REQUIRED = 'build.stock_required'

    # Build output events
    OUTPUT_CREATED = 'buildoutput.created'
    OUTPUT_COMPLETED = 'buildoutput.completed'

    # Non-conformance report (NCR) events
    NCR_RAISED = 'ncr.raised'
    NCR_INVESTIGATING = 'ncr.investigating'
    NCR_DISPOSITIONED = 'ncr.dispositioned'
    NCR_CLOSED = 'ncr.closed'
    NCR_CANCELLED = 'ncr.cancelled'
    NCR_REOPENED = 'ncr.reopened'
