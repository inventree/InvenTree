from common.notifications import NotificationMethod, SingleNotificationMethod, BulkNotificationMethod, storage
from plugin.models import NotificationUserSetting
from part.test_part import BaseNotificationIntegrationTest
import plugin.templatetags.plugin_extras as plugin_tags


class BaseNotificationTests(BaseNotificationIntegrationTest):

    def test_NotificationMethod(self):
        """ensure the implementation requirements are tested"""

        class FalseNotificationMethod(NotificationMethod):
            METHOD_NAME = 'FalseNotification'

        class AnotherFalseNotificationMethod(NotificationMethod):
            METHOD_NAME = 'AnotherFalseNotification'

            def send(self):
                """a comment so we do not need a pass"""

        class NoNameNotificationMethod(NotificationMethod):

            def send(self):
                """a comment so we do not need a pass"""

        class WrongContextNotificationMethod(NotificationMethod):
            METHOD_NAME = 'WrongContextNotification'
            CONTEXT_EXTRA = [
                'aa',
                ('aa', 'bb', ),
                ('templates', 'ccc', ),
                (123, )
            ]

            def send(self):
                """a comment so we do not need a pass"""

        # no send / send bulk
        with self.assertRaises(NotImplementedError):
            FalseNotificationMethod('', '', '', '', )

        # no METHOD_NAME
        with self.assertRaises(NotImplementedError):
            NoNameNotificationMethod('', '', '', '', )

        # a not existant context check
        with self.assertRaises(NotImplementedError):
            WrongContextNotificationMethod('', '', '', '', )

        # no get_targets
        with self.assertRaises(NotImplementedError):
            AnotherFalseNotificationMethod('', '', '', {'name': 1, 'message': 2, }, )

    def test_failing_passing(self):
        # cover failing delivery
        self._notification_run()

    def test_errors_passing(self):
        """ensure that errors do not kill the whole delivery"""

        class ErrorImplementation(SingleNotificationMethod):
            METHOD_NAME = 'ErrorImplementation'

            def get_targets(self):
                return [1, ]

            def send(self, target):
                raise KeyError('This could be any error')

        self._notification_run(ErrorImplementation)


class BulkNotificationMethodTests(BaseNotificationIntegrationTest):

    def test_BulkNotificationMethod(self):
        """
        Ensure the implementation requirements are tested.
        NotImplementedError needs to raise if the send_bulk() method is not set.
        """

        class WrongImplementation(BulkNotificationMethod):
            METHOD_NAME = 'WrongImplementationBulk'

            def get_targets(self):
                return [1, ]

        with self.assertRaises(NotImplementedError):
            self._notification_run(WrongImplementation)


class SingleNotificationMethodTests(BaseNotificationIntegrationTest):

    def test_SingleNotificationMethod(self):
        """
        Ensure the implementation requirements are tested.
        NotImplementedError needs to raise if the send() method is not set.
        """

        class WrongImplementation(SingleNotificationMethod):
            METHOD_NAME = 'WrongImplementationSingle'

            def get_targets(self):
                return [1, ]

        with self.assertRaises(NotImplementedError):
            self._notification_run(WrongImplementation)

# A integration test for notifications is provided in test_part.PartNotificationTest


class NotificationUserSettingTests(BaseNotificationIntegrationTest):
    """ Tests for NotificationUserSetting """

    def setUp(self):
        super().setUp()
        self.client.login(username=self.user.username, password='password')

    def test_setting_attributes(self):
        """check notification method plugin methods: usersettings and tags """

        class SampleImplementation(BulkNotificationMethod):
            METHOD_NAME = 'test'
            GLOBAL_SETTING = 'ENABLE_NOTIFICATION_TEST'
            USER_SETTING = {
                'name': 'Enable test notifications',
                'description': 'Allow sending of test for event notifications',
                'default': True,
                'validator': bool,
                'units': 'alpha',
            }

            def get_targets(self):
                return [1, ]

            def send_bulk(self):
                return True

        # run thorugh notification
        self._notification_run(SampleImplementation)
        # make sure the array fits
        array = storage.get_usersettings(self.user)
        setting = NotificationUserSetting.objects.all().first()

        # assertions for settings
        self.assertEqual(setting.name, 'Enable test notifications')
        self.assertEqual(setting.default_value, True)
        self.assertEqual(setting.description, 'Allow sending of test for event notifications')
        self.assertEqual(setting.units, 'alpha')

        # test tag and array
        self.assertEqual(plugin_tags.notification_settings_list({'user': self.user}), array)
        self.assertEqual(array[0]['key'], 'NOTIFICATION_METHOD_TEST')
        self.assertEqual(array[0]['method'], 'test')
