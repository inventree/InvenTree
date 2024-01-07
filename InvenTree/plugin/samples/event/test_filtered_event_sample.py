"""Unit tests for event_sample sample plugins."""

from django.conf import settings
from django.test import TestCase

from common.models import InvenTreeSetting
from plugin import registry
from plugin.base.event.events import trigger_event

from .filtered_event_sample import logger


class FilteredEventPluginSampleTests(TestCase):
    """Tests for EventPluginSample."""

    def test_run_event(self):
        """Check if the event is issued."""
        # Activate plugin
        config = registry.get_plugin('filteredsampleevent').plugin_config()
        config.active = True
        config.save()

        InvenTreeSetting.set_setting('ENABLE_PLUGINS_EVENTS', True, change_user=None)

        # Enable event testing
        settings.PLUGIN_TESTING_EVENTS = True
        # Check that an event is issued
        with self.assertLogs(logger=logger, level="DEBUG") as cm:
            trigger_event('test.event')
        self.assertIn(
            'DEBUG:inventree:Event `test.event` triggered in sample plugin', cm[1]
        )

        # Disable again
        settings.PLUGIN_TESTING_EVENTS = False

    def test_ignore_event(self):
        """Check if the event is issued."""
        # Activate plugin
        config = registry.get_plugin('filteredsampleevent').plugin_config()
        config.active = True
        config.save()

        InvenTreeSetting.set_setting('ENABLE_PLUGINS_EVENTS', True, change_user=None)

        # Enable event testing
        settings.PLUGIN_TESTING_EVENTS = True
        # Check that an event is issued
        with self.assertLogs(logger=logger, level="DEBUG") as cm:
            trigger_event('test.some.other.event')
        self.assertNotIn(
            'DEBUG:inventree:Event `test.some.other.event` triggered in sample plugin',
            cm[1],
        )

        # Disable again
        settings.PLUGIN_TESTING_EVENTS = False
