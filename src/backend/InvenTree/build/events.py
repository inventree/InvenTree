"""Event definitions and triggers for the build app."""

from generic.events import BaseEventEnum


class BuildEvents(BaseEventEnum):
    """Event enumeration for the Build app."""

    # Build order events
    BUILD_HOLD = 'build.hold'
    BUILD_ISSUED = 'build.issued'
    BUILD_CANCELLED = 'build.cancelled'
    BUILD_COMPLETED = 'build.completed'
    BUILD_OVERDUE = 'build.overdue_build_order'

    # Build output events
    OUTPUT_CREATED = 'buildoutput.created'
    OUTPUT_COMPLETED = 'buildoutput.completed'
