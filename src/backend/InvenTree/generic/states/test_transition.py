"""Tests for state transition mechanism."""

from django.core.exceptions import ValidationError

from InvenTree.unit_test import InvenTreeTestCase
from plugin import registry


class TransitionTests(InvenTreeTestCase):
    """Tests for custom state transition logic."""

    fixtures = ['company', 'return_order', 'part', 'stock', 'location', 'category']

    def test_return_order(self):
        """Test transition of a return order."""
        from order.models import ReturnOrder
        from order.status_codes import ReturnOrderStatus

        # Ensure plugin is enabled
        registry.set_plugin_state('sample-transition', True)

        ro = ReturnOrder.objects.get(pk=2)
        self.assertEqual(ro.status, ReturnOrderStatus.IN_PROGRESS.value)

        # Attempt to transition to COMPLETE state
        # This should fail - due to the StateTransitionMixin logic
        with self.assertRaises(ValidationError) as e:
            ro.complete_order()

        self.assertIn(
            'Return order without responsible owner can not be completed',
            str(e.exception),
        )

        # Now disable the plugin
        registry.set_plugin_state('sample-transition', False)

        # Attempt to transition again
        ro.complete_order()
        ro.refresh_from_db()

        self.assertEqual(ro.status, ReturnOrderStatus.COMPLETE.value)
