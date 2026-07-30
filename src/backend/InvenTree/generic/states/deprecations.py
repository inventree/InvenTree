"""Helper for deprecating old implementation details."""

from enum import Enum
from warnings import deprecated as warn_deprecated


class Deprecations(Enum):
    """Deprecations for states."""

    CAN_PROCEED = 'Use can_proceed directly'


deprecated = warn_deprecated
