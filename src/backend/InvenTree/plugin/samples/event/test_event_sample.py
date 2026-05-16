"""Unit tests for event_sample sample plugins."""

from django.test import TestCase

from common.models import InvenTreeSetting
from plugin import InvenTreePlugin, registry
from plugin.base.event.events import trigger_event
from plugin.helpers import MixinNotImplementedError
from plugin.mixins import EventMixin


class EventPluginSampleTests(TestCase):
    """Tests for EventPluginSample."""

    def test_run_event(self):
        """Check if the event is issued."""
        # Activate plugin
        registry.set_plugin_state('sampleevent', True)

        InvenTreeSetting.set_setting('ENABLE_PLUGINS_EVENTS', True, change_user=None)

        # Enable event testing
        with self.settings(PLUGIN_TESTING_EVENTS=True):
            # Check that an event is issued
            with self.assertLogs(logger='inventree', level='DEBUG') as cm:
                trigger_event('test.event')
            self.assertIn('Event `test.event` triggered in sample plugin', str(cm[1]))

    def test_mixin(self):
        """Test that MixinNotImplementedError is raised."""
        with self.assertRaises(MixinNotImplementedError):

            class Wrong(EventMixin, InvenTreePlugin):
                pass

            plugin = Wrong()
            plugin.process_event('abc')
