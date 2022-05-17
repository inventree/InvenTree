from plugin.models import NotificationUserSetting
from part.test_part import BaseNotificationIntegrationTest
from plugin.builtin.integration.core_notifications import CoreNotificationsPlugin
from plugin import registry


class CoreNotificationTestTests(BaseNotificationIntegrationTest):

    def test_email(self):
        """
        Ensure that the email notifications run
        """

        # enable plugin and set mail setting to true
        plugin = registry.plugins.get('corenotificationsplugin')
        plugin.set_setting('ENABLE_NOTIFICATION_EMAILS', True)
        NotificationUserSetting.set_setting(
            key='NOTIFICATION_METHOD_MAIL',
            value=True,
            change_user=self.user,
            user=self.user,
            method=CoreNotificationsPlugin.EmailNotification.METHOD_NAME
        )

        # run through
        self._notification_run(CoreNotificationsPlugin.EmailNotification)
