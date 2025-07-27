"""Classes and functions for plugin controlled object state transitions."""

import structlog

logger = structlog.get_logger('inventree')


class TransitionMethod:
    """Base class for all transition classes.

    Must implement a method called `transition` that takes both args and kwargs.
    """

    def __init__(self) -> None:
        """Check that the method is defined correctly.

        This checks that:
        - The needed functions are implemented
        """
        # Check if a sending fnc is defined
        if not hasattr(self, 'transition'):
            raise NotImplementedError(
                'A TransitionMethod must define a `transition` method'
            )


class StateTransitionMixin:
    """Mixin class to enable state transitions.

    This mixin is used to add state transitions handling to a model. With this you can apply custom logic to state transitions via plugins.
    ```python
    class MyModel(StateTransitionMixin, models.Model):
        def some_dummy_function(self, *args, **kwargs):
            pass

        def action(self, *args, **kwargs):
            self.handle_transition(0, 1, self, self.some_dummy_function)
    ```
    """

    def handle_transition(
        self, current_state, target_state, instance, default_action, **kwargs
    ):
        """Handle a state transition for an object.

        Args:
            current_state: Current state of instance
            target_state: Target state of instance
            instance: Object instance
            default_action: Default action to be taken if none of the transitions returns a boolean true value
        """
        from InvenTree.exceptions import log_error
        from plugin import PluginMixinEnum, registry

        transition_plugins = registry.with_mixin(PluginMixinEnum.STATE_TRANSITION)

        for plugin in transition_plugins:
            try:
                handlers = plugin.get_transition_handlers()
            except Exception:
                log_error('get_transition_handlers', plugin=plugin)
                continue

            if type(handlers) is not list:
                logger.error(
                    'Plugin %s return invalid type for transition handlers', plugin.slug
                )
                continue

            for handler in handlers:
                if not isinstance(handler, TransitionMethod):
                    logger.error('Invalid transition handler type: %s', handler)
                    continue

                # Call the transition method
                result = handler.transition(
                    current_state, target_state, instance, default_action, **kwargs
                )

                if result:
                    return result

        # Default action
        return default_action(current_state, target_state, instance, **kwargs)
