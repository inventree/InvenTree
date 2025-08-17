"""Unit tests for event_sample sample plugins."""

from django.test import TestCase

from common.models import InvenTreeSetting
from plugin import InvenTreePlugin
from plugin.base.mail.mail import process_mail_in, process_mail_out
from plugin.helpers import MixinNotImplementedError
from plugin.mixins import MailMixin
from plugin.registry import registry


class MailPluginSampleTests(TestCase):
    """Tests for MailPluginSample."""

    def activate_plugin(self):
        """Activate the sample mail plugin."""
        config = registry.get_plugin('samplemail', active=None).plugin_config()
        config.active = True
        config.save()

    def test_run_event_out(self):
        """Check if the event on send mails is issued."""
        self.activate_plugin()

        # Disabled -> no processing
        self.assertFalse(process_mail_out('test.event'))

        InvenTreeSetting.set_setting('ENABLE_PLUGINS_MAILS', True, change_user=None)

        # Check that an event is issued
        with self.assertLogs(logger='inventree', level='DEBUG') as cm:
            process_mail_out('test.event')
        self.assertIn('Mail `test.event` triggered in sample plugin', str(cm[1]))

    def test_run_event_in(self):
        """Check if the event on received is issued."""
        self.activate_plugin()

        # Disabled -> no processing
        self.assertFalse(process_mail_in('test.event'))

        InvenTreeSetting.set_setting('ENABLE_PLUGINS_MAILS', True, change_user=None)

        # Check that an event is issued
        with self.assertLogs(logger='inventree', level='DEBUG') as cm:
            process_mail_in('test.event')
        self.assertIn('Mail `test.event` triggered in sample plugin', str(cm[1]))

    def test_mixin(self):
        """Test that MixinNotImplementedError is raised."""
        with self.assertRaises(MixinNotImplementedError):

            class Wrong(MailMixin, InvenTreePlugin):
                pass

            plugin = Wrong()
            plugin.process_mail_out('abc')
