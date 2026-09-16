"""Helper for deprecating old implementation details."""

from enum import Enum
from typing import Any, Optional

# py (3, 12) does not ship with depreciation decorator, so we need to import it from typing_extensions
try:
    from warnings import deprecated as warn_deprecated  # ty: ignore[unresolved-import]
except ImportError:
    from typing_extensions import deprecated as warn_deprecated


class Deprecations(Enum):
    """Deprecations for states."""

    CAN_PROCEED = 'Use can_proceed directly'


class deprecated(warn_deprecated):  # noqa: N801
    """Deprecation decorator for state transition methods."""

    def __init__(
        self, message: Any | str, version: Optional[str] = None, *args, **kwargs
    ):
        """Initialize the decorator with a deprecation reason."""
        self.version = version
        super().__init__(str(message), *args, **kwargs)
