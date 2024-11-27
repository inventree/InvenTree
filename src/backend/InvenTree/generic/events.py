"""Generic event enumerations for InevnTree."""

import enum


class BaseEventEnum(str, enum.Enum):
    """Base class for representing a set of 'events'."""

    def __str__(self):
        """Return the string representation of the event."""
        return str(self.value)
