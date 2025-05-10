"""Unit tests for event_sample sample plugins."""

from django.test import TestCase

from common.models import InvenTreeSetting
from plugin import InvenTreePlugin, registry
from plugin.base.mail.mail import process_mail
from plugin.helpers import MixinNotImplementedError
from plugin.mixins import MailMixin


class MailPluginSampleTests(TestCase):
    """Tests for MailPluginSample."""

    def test_run_event(self):
        """Check if the event is issued."""
        # Activate plugin
        config = registry.get_plugin('samplemail').plugin_config()
        config.active = True
        config.save()

        # Disabled -> no processing
        self.assertFalse(process_mail('test.event'))

        InvenTreeSetting.set_setting('ENABLE_PLUGINS_MAILS', True, change_user=None)

        # Check that an event is issued
        with self.assertLogs(logger='inventree', level='DEBUG') as cm:
            process_mail('test.event')
        self.assertIn('Mail `test.event` triggered in sample plugin', str(cm[1]))

    def test_mixin(self):
        """Test that MixinNotImplementedError is raised."""
        with self.assertRaises(MixinNotImplementedError):

            class Wrong(MailMixin, InvenTreePlugin):
                pass

            plugin = Wrong()
            plugin.process_mail('abc')
