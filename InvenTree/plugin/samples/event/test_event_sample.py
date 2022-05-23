"""Unit tests for event_sample sample plugins"""

from django.test import TestCase

from plugin import registry
from plugin.base.event.events import trigger_event


class EventPluginSampleTests(TestCase):
    """Tests for EventPluginSample"""

    def test_run_event(self):
        """Check if the event is issued"""
        # Activate plugin
        config = registry.get_plugin('sampleevent').plugin_config()
        config.active = True
        config.save()

        # Check that an event is issued
        with self.assertWarns(Warning) as cm:
            trigger_event('test.event')
        self.assertEqual(cm.warning.args[0], 'Event `test.event` triggered')
