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

    # Build output events
    OUTPUT_CREATED = 'buildoutput.created'
    OUTPUT_COMPLETED = 'buildoutput.completed'
