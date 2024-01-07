"""Tests for core_notifications."""

from django.core import mail

from part.test_part import BaseNotificationIntegrationTest
from plugin import registry
from plugin.builtin.integration.core_notifications import (
    InvenTreeCoreNotificationsPlugin,
)
from plugin.models import NotificationUserSetting


class CoreNotificationTestTests(BaseNotificationIntegrationTest):
    """Tests for CoreNotificationsPlugin."""

    def test_email(self):
        """Ensure that the email notifications run."""
        # No email should be send
        self.assertEqual(len(mail.outbox), 0)

        # enable plugin and set mail setting to true
        plugin = registry.plugins.get('inventreecorenotificationsplugin')
        plugin.set_setting('ENABLE_NOTIFICATION_EMAILS', True)
        NotificationUserSetting.set_setting(
            key='NOTIFICATION_METHOD_MAIL',
            value=True,
            change_user=self.user,
            user=self.user,
            method=InvenTreeCoreNotificationsPlugin.EmailNotification.METHOD_NAME,
        )

        # run through
        self._notification_run(InvenTreeCoreNotificationsPlugin.EmailNotification)

        # Now one mail should be send
        self.assertEqual(len(mail.outbox), 1)
