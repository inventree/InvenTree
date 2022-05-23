"""Unit tests for event_sample sample plugins"""

from django.conf import settings
from django.test import TestCase

from plugin import InvenTreePlugin, registry
from plugin.base.event.events import trigger_event
from plugin.helpers import MixinNotImplementedError
from plugin.mixins import EventMixin


class EventPluginSampleTests(TestCase):
    """Tests for EventPluginSample"""

    def test_run_event(self):
        """Check if the event is issued"""
        # Activate plugin
        config = registry.get_plugin('sampleevent').plugin_config()
        config.active = True
        config.save()

        # Enable event testing
        settings.PLUGIN_TESTING_EVENTS = True
        # Check that an event is issued
        with self.assertWarns(Warning) as cm:
            trigger_event('test.event')
        self.assertEqual(cm.warning.args[0], 'Event `test.event` triggered')

        # Disable again
        settings.PLUGIN_TESTING_EVENTS = False

    def test_mixin(self):
        """Test that MixinNotImplementedError is raised"""

        with self.assertRaises(MixinNotImplementedError):
            class Wrong(EventMixin, InvenTreePlugin):
                pass

            plugin = Wrong()
            plugin.process_event('abc')
