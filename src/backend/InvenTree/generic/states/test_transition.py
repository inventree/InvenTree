"""Tests for state transition mechanism."""

from django.core.exceptions import ValidationError

from InvenTree.unit_test import InvenTreeTestCase
from order.models import ReturnOrder
from order.status_codes import ReturnOrderStatus
from plugin import registry


class TransitionTests(InvenTreeTestCase):
    """Tests for custom state transition logic."""

    fixtures = ['company', 'return_order', 'part', 'stock', 'location', 'category']

    def setUp(self):
        """Set up the test environment."""
        super().setUp()
        self.ensurePluginsLoaded()

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

        # Transition to "ON HOLD" state
        ro.hold_order()

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
            ro.complete_order()
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

            # Ensure correct eroror was logged
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
