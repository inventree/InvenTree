"""Sample implementation of state transition implementation."""

import warnings

from django.core.exceptions import ValidationError

from common.notifications import trigger_notification
from generic.states import TransitionMethod
from order.models import ReturnOrder
from order.status_codes import ReturnOrderStatus
from plugin import InvenTreePlugin
from plugin.mixins import SettingsMixin, TransitionMixin


class SampleTransitionPlugin(TransitionMixin, InvenTreePlugin):
    """A sample plugin which shows how state transitions might be implemented."""

    NAME = 'SampleTransitionPlugin'
    SLUG = 'sample-transition'

    class ReturnChangeHandler(TransitionMethod):
        """Transition method for ReturnOrder objects."""

        def transition(
            self, current_state, target_state, instance, default_action, **kwargs
        ) -> bool:
            """Example override function for state transition."""
            # Only act on ReturnOrders that should be completed
            if (
                not isinstance(instance, ReturnOrder)
                or target_state != ReturnOrderStatus.COMPLETE.value
            ):
                return False

            # Only allow proceeding if the return order has a responsible user assigned
            if not instance.responsible:
                msg = 'Return order without responsible owner can not be completed!'

                # Trigger whoever created the return order
                instance.created_by
                trigger_notification(
                    instance,
                    'sampel_123_456',
                    targets=[instance.created_by],
                    context={'message': msg},
                )

                raise ValidationError(msg)

            return False  # Do not act

    TRANSITION_HANDLERS = [ReturnChangeHandler()]


class BrokenTransitionPlugin(SettingsMixin, TransitionMixin, InvenTreePlugin):
    """An intentionally broken plugin to test error handling."""

    NAME = 'BrokenTransitionPlugin'
    SLUG = 'sample-broken-transition'

    SETTINGS = {
        'BROKEN_GET_METHOD': {
            'name': 'Broken Get Method',
            'description': 'If set, the get_transition_handlers method will raise an error.',
            'validator': bool,
            'default': False,
        },
        'WRONG_RETURN_TYPE': {
            'name': 'Wrong Return Type',
            'description': 'If set, the get_transition_handlers method will return an incorrect type.',
            'validator': bool,
            'default': False,
        },
        'WRONG_RETURN_VALUE': {
            'name': 'Wrong Return Value',
            'description': 'If set, the get_transition_handlers method will return an incorrect value.',
            'validator': bool,
            'default': False,
        },
    }

    @property
    def has_transition_handlers(self) -> bool:
        """Ensure that this plugin always has handlers."""
        return True

    def get_transition_handlers(self) -> list[TransitionMethod]:
        """Return transition handlers for the given instance."""
        warnings.warn(
            'get_transition_handlers is intentionally broken in this plugin',
            stacklevel=2,
        )

        if self.get_setting('BROKEN_GET_METHOD', backup_value=False, cache=False):
            raise ValueError('This is a broken transition plugin!')

        if self.get_setting('WRONG_RETURN_TYPE', backup_value=False, cache=False):
            return 'This is not a list of handlers!'

        if self.get_setting('WRONG_RETURN_VALUE', backup_value=False, cache=False):
            return [1, 2, 3]

        # Return a valid handler list (empty)
        return []
