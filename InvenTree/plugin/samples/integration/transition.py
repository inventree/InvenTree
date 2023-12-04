"""Sample implementation of state transition implementation."""

from common.notifications import trigger_notification
from generic.states import TransitionMethod
from InvenTree.status_codes import ReturnOrderStatus
from order.models import ReturnOrder
from plugin import InvenTreePlugin


class SampleTransitionPlugin(InvenTreePlugin):
    """A sample plugin which shows how state transitions might be implemented."""

    NAME = "SampleTransitionPlugin"

    class ReturnChangeHandler(TransitionMethod):
        """Transition method for PurchaseOrder objects."""

        def transition(current_state, target_state, instance, default_action, **kwargs):  # noqa: N805
            """Example override function for state transition."""
            # Only act on ReturnOrders that should be completed
            if not isinstance(instance, ReturnOrder) or not (target_state == ReturnOrderStatus.COMPLETE.value):
                return False

            # Only allow proceeding if the return order has a responsible user assigned
            if not instance.responsible:
                # Trigger whoever created the return order
                instance.created_by
                trigger_notification(
                    instance,
                    'sampel_123_456',
                    targets=[instance.created_by, ],
                    context={'message': "Return order without responsible owner can not be completed!"},
                )
                return True  # True means nothing will happen
            return False  # Do not act
