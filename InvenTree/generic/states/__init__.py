"""States are used to track the logical state of an object.

The logic value of a state is stored in the database as an integer. The logic value is used for business logic and should not be easily changed therefore.
There is a rendered state for each state value. The rendered state is used for display purposes and can be changed easily.

States can be extended with custom options for each InvenTree instance - those options are stored in the database and need to link back to state values.
"""

from .states import StatusCode
from .transition import StateTransitionMixin, TransitionMethod, storage

__all__ = [StatusCode, storage, TransitionMethod, StateTransitionMixin]
