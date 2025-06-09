"""Generic enum type definitions."""

import enum


class StringEnum(str, enum.Enum):
    """Base class for string-based enumerations."""

    def __str__(self):
        """Return the string representation of the enumeration value."""
        return str(self.value)

    def __repr__(self):
        """Return the string representation of the enumeration value."""
        return str(self.value)
