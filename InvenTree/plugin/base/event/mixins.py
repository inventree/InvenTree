"""Plugin mixin class for events."""

from plugin.helpers import MixinNotImplementedError


class EventMixin:
    """Mixin that provides support for responding to triggered events.

    Implementing classes must provide a "process_event" function:
    """

    def wants_process_event(self, event: str) -> bool:
        """Function to subscribe to events.

        Return true if you're interested in the given event, false if not.
        """
        # Default implementation always returns true (backwards compatibility)
        return True

    def process_event(self, event: str, *args, **kwargs) -> None:
        """Function to handle events.

        Must be overridden by plugin
        """
        # Default implementation does not do anything
        raise MixinNotImplementedError

    class MixinMeta:
        """Meta options for this mixin."""

        MIXIN_NAME = 'Events'

    def __init__(self):
        """Register the mixin."""
        super().__init__()
        self.add_mixin('events', True, __class__)
