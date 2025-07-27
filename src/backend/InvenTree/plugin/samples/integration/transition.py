"""Sample implementation of state transition implementation."""

from django.core.exceptions import ValidationError

from common.notifications import trigger_notification
from generic.states import TransitionMethod
from order.models import ReturnOrder
from order.status_codes import ReturnOrderStatus
from plugin import InvenTreePlugin
from plugin.mixins import TransitionMixin


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
