"""Unit tests for event_sample sample plugins."""

from django.conf import settings
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
        config = registry.get_plugin('sampleevent').plugin_config()
        config.active = True
        config.save()

        InvenTreeSetting.set_setting('ENABLE_PLUGINS_EVENTS', True, change_user=None)

        # Enable event testing
        settings.PLUGIN_TESTING_EVENTS = True
        # Check that an event is issued
        with self.assertLogs(logger='inventree', level='DEBUG') as cm:
            trigger_event('test.event')
        self.assertIn('Event `test.event` triggered in sample plugin', str(cm[1]))

        # Disable again
        settings.PLUGIN_TESTING_EVENTS = False

    def test_mixin(self):
        """Test that MixinNotImplementedError is raised."""
        with self.assertRaises(MixinNotImplementedError):

            class Wrong(EventMixin, InvenTreePlugin):
                pass

            plugin = Wrong()
            plugin.process_event('abc')
