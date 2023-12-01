"""Classes and functions for plugin controlled object state transitions."""
import InvenTree.helpers


class TransitionMethod:
    """Base class for all transition classes.

    Must implement a method called `transition` that takes both args and kwargs.
    """
    ...


class TransitionMethodStorageClass:
    """Class that works as registry for all available transition methods in InvenTree.

    Is initialized on startup as one instance named `storage` in this file.
    """

    list = None

    def collect(self):
        """Collect all classes in the environment that are transition methods."""
        filtered_list = {}
        for item in InvenTree.helpers.inheritors(TransitionMethod):
            filtered_list[f'{item.__module__}.{item.__qualname__}'] = item

        self.list = list(filtered_list.values())

        # Ensure the list has items
        if not self.list:
            self.list = []


storage = TransitionMethodStorageClass()


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

    def handle_transition(self, current_state, target_state, instance, default_action, **kwargs):
        """Handle a state transition for an object.

        Args:
            current_state: Current state of instance
            target_state: Target state of instance
            instance: Object instance
            default_action: Default action to be taken if none of the transitions returns a boolean true value
        """
        # Check if there is a custom override function for this transition
        for override in storage.list:
            rslt = override.transition(current_state, target_state, instance, default_action, **kwargs)
            if rslt:
                return rslt

        # Default action
        return default_action(current_state, target_state, instance, **kwargs)
