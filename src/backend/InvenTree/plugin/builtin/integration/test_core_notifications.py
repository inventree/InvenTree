"""Tests for core_notifications."""

from django.core import mail

from common.models import NotificationEntry
from common.notifications import trigger_notification
from InvenTree.unit_test import InvenTreeTestCase
from plugin import registry


class CoreNotificationTestTests(InvenTreeTestCase):
    """Tests for CoreNotificationsPlugin."""

    def setUp(self):
        """Set up the test case."""
        super().setUp()

        # Ensure that the user has an email address set
        self.user.email = 'test.user@demo.inventree.org'
        self.user.is_superuser = True
        self.user.save()

    def notify(self):
        """Send an email notification."""
        # Clear all entries to ensure the notification is sent
        NotificationEntry.objects.all().delete()

        trigger_notification(
            self.user,
            'test_notification',
            targets=[self.user],
            context={
                'name': 'Test Email Notification',
                'message': 'This is a test email notification.',
                'template': {
                    'html': 'email/test_email.html',
                    'subject': 'Test Email Notification',
                },
            },
        )

    def test_email(self):
        """Ensure that the email notifications run."""
        # No email should be send
        self.assertEqual(len(mail.outbox), 0)

        plugin = registry.get_plugin('inventree-email-notification')
        self.assertIsNotNone(plugin, 'Email notification plugin should be available')

        plugin.activate()

        # First, try with setting disabled
        plugin.set_user_setting('NOTIFY_BY_EMAIL', False, self.user)

        self.notify()

        # No email should be sent
        self.assertEqual(len(mail.outbox), 0)

        # Now, enable the setting
        plugin.set_user_setting('NOTIFY_BY_EMAIL', True, self.user)

        self.notify()

        self.assertEqual(len(mail.outbox), 1)
