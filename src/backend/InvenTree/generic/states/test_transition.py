"""Tests for state transition mechanism."""

from django.core.exceptions import ValidationError

from generic.states import can_proceed
from InvenTree.unit_test import InvenTreeTestCase
from order.models import PurchaseOrder, ReturnOrder, SalesOrder, TransferOrder
from order.status_codes import (
    PurchaseOrderStatus,
    ReturnOrderStatus,
    SalesOrderStatus,
    TransferOrderStatus,
)
from plugin import registry
from users.models import Owner


class TransitionTests(InvenTreeTestCase):
    """Tests for custom state transition logic."""

    def setUp(self):
        """Set up the test environment."""
        super().setUp()
        self.ensurePluginsLoaded()

    fixtures = [
        'company',
        'supplier_part',
        'category',
        'part',
        'location',
        'stock',
        'order',
        'sales_order',
        'return_order',
        'transfer_order',
    ]

    def test_fsm_decorator_applied_to_purchase_order(self):
        """Verify @inventree_transition metadata is attached to PurchaseOrder methods."""
        # Methods decorated with @inventree_transition expose _django_fsm metadata
        self.assertTrue(hasattr(PurchaseOrder.place_order, '_django_fsm'))
        self.assertTrue(hasattr(PurchaseOrder.complete_order, '_django_fsm'))
        self.assertTrue(hasattr(PurchaseOrder.hold_order, '_django_fsm'))
        self.assertTrue(hasattr(PurchaseOrder.cancel_order, '_django_fsm'))

    def test_fsm_can_proceed_purchase_order(self):
        """Test can_proceed() reflects current state correctly for PurchaseOrder."""
        po = PurchaseOrder.objects.filter(
            status=PurchaseOrderStatus.PENDING.value
        ).first()
        assert po

        # A PENDING order can be placed or cancelled, but not completed
        self.assertTrue(po.can_issue)
        self.assertTrue(po.can_cancel)
        self.assertFalse(can_proceed(po.complete_order))
        self.assertTrue(po.is_open)

        # depreceted methods
        self.assertTrue(po.can_hold)

    def test_fsm_purchase_order_transitions(self):
        """Test that PurchaseOrder transitions work correctly via @inventree_transition."""
        po = PurchaseOrder.objects.filter(
            status=PurchaseOrderStatus.PENDING.value
        ).first()
        assert po

        # Place the order (PENDING → PLACED)
        result = po.place_order()
        self.assertTrue(result)
        po.refresh_from_db()
        self.assertEqual(po.status, PurchaseOrderStatus.PLACED.value)

        # Hold the order (PLACED → ON_HOLD)
        result = po.hold_order()
        self.assertTrue(result)
        po.refresh_from_db()
        self.assertEqual(po.status, PurchaseOrderStatus.ON_HOLD.value)

        # Place again from ON_HOLD (ON_HOLD → PLACED)
        result = po.place_order()
        self.assertTrue(result)
        po.refresh_from_db()
        self.assertEqual(po.status, PurchaseOrderStatus.PLACED.value)

        # Cancel the order (PLACED → CANCELLED)
        result = po.cancel_order()
        self.assertTrue(result)
        po.refresh_from_db()
        self.assertEqual(po.status, PurchaseOrderStatus.CANCELLED.value)

    def test_fsm_sale_order_transitions(self):
        """Test that SaleOrder transitions work correctly via @inventree_transition."""
        so = SalesOrder.objects.filter(status=SalesOrderStatus.PENDING.value).first()
        assert so

        # deprecated methods
        self.assertTrue(so.can_issue)
        self.assertTrue(so.can_hold)
        self.assertTrue(so.can_cancel)

    def test_fsm_invalid_transition_returns_false(self):
        """Test that an invalid transition returns False (backward-compatible behaviour)."""
        po = PurchaseOrder.objects.filter(
            status=PurchaseOrderStatus.CANCELLED.value
        ).first()
        assert po

        # Attempting to place a cancelled order must raise
        with self.assertRaises(ValidationError):
            po.place_order()

        # The order status must remain CANCELLED
        po.refresh_from_db()
        self.assertEqual(po.status, PurchaseOrderStatus.CANCELLED.value)

    def test_fsm_return_order_transitions(self):
        """Test that ReturnOrder transitions work correctly via @inventree_transition."""
        ro = ReturnOrder.objects.filter(
            status=ReturnOrderStatus.IN_PROGRESS.value
        ).first()
        assert ro

        # Can complete an IN_PROGRESS return order
        self.assertTrue(can_proceed(ro.complete_order))

        # Cannot issue an IN_PROGRESS return order (already issued)
        self.assertFalse(can_proceed(ro.issue_order))

        # deprecated methods
        self.assertTrue(ro.can_hold)
        self.assertTrue(ro.can_cancel)
        self.assertFalse(ro.can_issue)

    def test_fsm_transferorder(self):
        """Test that TransferOrder transitions work correctly via @inventree_transition."""
        to = TransferOrder.objects.filter(
            status=TransferOrderStatus.PENDING.value
        ).first()
        assert to

        self.assertTrue(to.can_issue)
        self.assertTrue(to.can_hold)
        self.assertTrue(to.can_cancel)

    def test_fsm_can_issue_property(self):
        """Test the can_issue property delegates to can_proceed."""
        po = PurchaseOrder.objects.filter(
            status=PurchaseOrderStatus.PENDING.value
        ).first()
        assert po

        self.assertEqual(po.can_issue, can_proceed(po.place_order))

    def test_return_order(self):
        """Test transition of a return order."""
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

        ro.responsible = Owner.create(obj=self.user)
        ro.save()
        result = ro.complete_order()
        self.assertEqual(result, '123#abc!')
        # There should be no change in the status of the return order
        self.assertEqual(ro.status, ReturnOrderStatus.IN_PROGRESS.value)

        # Now disable the plugin
        registry.set_plugin_state('sample-transition', False)

        # Attempt to transition again
        ro.complete_order()
        ro.refresh_from_db()

        self.assertEqual(ro.status, ReturnOrderStatus.COMPLETE.value)

    def test_broken_transition_plugin(self):
        """Test handling of an intentionally broken transition plugin.

        This test uses a custom plugin which is designed to fail in various ways.
        """
        from error_report.models import Error

        Error.objects.all().delete()

        # Ensure the correct plugin is enabled
        registry.set_plugin_state('sample-transition', False)
        registry.set_plugin_state('sample-broken-transition', True)

        ro = ReturnOrder.objects.get(pk=2)
        self.assertEqual(ro.status, ReturnOrderStatus.IN_PROGRESS.value)

        # Ensure plugin starts in a known state
        plugin = registry.get_plugin('sample-broken-transition')
        plugin.set_setting('BROKEN_GET_METHOD', False)
        plugin.set_setting('WRONG_RETURN_TYPE', False)
        plugin.set_setting('WRONG_RETURN_VALUE', False)

        # Expect a "warning" message on each run
        # This assures us that the transition handler is being called
        msg = 'get_transition_handlers is intentionally broken in this plugin'

        with self.assertWarnsMessage(UserWarning, msg):
            # No error should occur here
            ro.hold_order()
            self.assertEqual(ro.status, ReturnOrderStatus.ON_HOLD.value)

        # No error should be logged
        self.assertEqual(0, Error.objects.count())

        # Now, enable the "WRONG_RETURN_VALUE" setting
        plugin.set_setting('WRONG_RETURN_VALUE', True)

        with self.assertLogs('inventree', level='ERROR') as cm:
            with self.assertWarnsMessage(UserWarning, msg):
                # No error should occur here
                ro.issue_order()
                self.assertEqual(ro.status, ReturnOrderStatus.IN_PROGRESS.value)

            # Ensure correct error was logged
            self.assertIn('Invalid transition handler type: 1', str(cm.output[0]))

        # Now, enable the "WRONG_RETURN_TYPE" setting
        plugin.set_setting('WRONG_RETURN_TYPE', True)

        with self.assertLogs('inventree', level='ERROR') as cm:
            with self.assertWarnsMessage(UserWarning, msg):
                # No error should occur here
                ro.hold_order()
                self.assertEqual(ro.status, ReturnOrderStatus.ON_HOLD.value)

            # Ensure correct error was logged
            self.assertIn(
                'Plugin sample-broken-transition returned invalid type for transition handlers',
                str(cm.output[0]),
            )

        # Now, enable the "BROKEN_GET_METHOD" setting
        plugin.set_setting('BROKEN_GET_METHOD', True)

        with self.assertLogs('inventree', level='ERROR') as cm:
            with self.assertWarnsMessage(UserWarning, msg):
                ro.issue_order()
                self.assertEqual(ro.status, ReturnOrderStatus.IN_PROGRESS.value)

            # Ensure correct error was logged
            self.assertIn(
                "ValueError('This is a broken transition plugin!')", str(cm.output[0])
            )

        # Ensure the plugin is now disabled
        registry.set_plugin_state('sample-transition', False)
        registry.set_plugin_state('sample-broken-transition', False)
