"""Plugin mixin for handling state transitions."""

from typing import TYPE_CHECKING

import structlog

from generic.states.transition import TransitionMethod
from plugin import PluginMixinEnum

logger = structlog.get_logger('inventree')

if TYPE_CHECKING:
    ...


class StateTransitionMixin:
    """Mixin class for handling state transitions.

    - This mixin allows plugins to define custom state transition methods.
    - These methods can be used to apply custom logic when an object transitions from one state to another.
    """

    # List of transition methods that can be used by plugins
    TRANSITION_HANDLERS: list[TransitionMethod] = []

    class MixinMeta:
        """Meta class for the StateTransitionMixin."""

        MIXIN_NAME = 'StateTransition'

    def __init__(self):
        """Initialize the mixin and register it."""
        super().__init__()
        self.add_mixin(
            PluginMixinEnum.STATE_TRANSITION, 'has_transition_handlers', __class__
        )

    @property
    def has_transition_handlers(self) -> bool:
        """Check if there are any transition handlers defined."""
        try:
            result = bool(self.get_transition_handlers())
            return result
        except Exception:
            return False

    def get_transition_handlers(self) -> list[TransitionMethod]:
        """Get the list of transition methods available in this mixin.

        The default implementation returns the TRANSITION_HANDLERS list.
        """
        handlers = getattr(self, 'TRANSITION_HANDLERS', None) or []

        if not isinstance(handlers, list):
            raise TypeError(
                'TRANSITION_HANDLERS must be a list of TransitionMethod instances'
            )

        handler_methods = []

        for handler in handlers:
            if not isinstance(handler, TransitionMethod):
                logger.error('Invalid transition handler type: %s', handler)
                continue

            handler_methods.append(handler)

        return handler_methods
