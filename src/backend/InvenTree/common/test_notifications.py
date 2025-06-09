"""Tests for basic notification methods and functions in InvenTree."""

from part.test_part import BaseNotificationIntegrationTest


# TODO: Remove these, hacky
class NotificationMethod:
    """Dummy class to be removed."""


class SingleNotificationMethod:
    """Dummy class to be removed."""


class BulkNotificationMethod:
    """Dummy class to be removed."""


class BaseNotificationTests(BaseNotificationIntegrationTest):
    """Tests for basic NotificationMethod."""

    def test_NotificationMethod(self):
        """Ensure the implementation requirements are tested."""

        class FalseNotificationMethod(NotificationMethod):
            METHOD_NAME = 'FalseNotification'

        class AnotherFalseNotificationMethod(NotificationMethod):
            METHOD_NAME = 'AnotherFalseNotification'

            def send(self):
                """A comment so we do not need a pass."""

        class NoNameNotificationMethod(NotificationMethod):
            def send(self):
                """A comment so we do not need a pass."""

        class WrongContextNotificationMethod(NotificationMethod):
            METHOD_NAME = 'WrongContextNotification'
            CONTEXT_EXTRA = ['aa', ('aa', 'bb'), ('templates', 'ccc'), (123,)]

            def send(self):
                """A comment so we do not need a pass."""

        # no send / send bulk
        with self.assertRaises(NotImplementedError):
            FalseNotificationMethod('', '', '', '')

        # no METHOD_NAME
        with self.assertRaises(NotImplementedError):
            NoNameNotificationMethod('', '', '', '')

        # a not existent context check
        with self.assertRaises(NotImplementedError):
            WrongContextNotificationMethod('', '', '', '')

        # no get_targets
        with self.assertRaises(NotImplementedError):
            AnotherFalseNotificationMethod('', '', '', {'name': 1, 'message': 2})

    def test_failing_passing(self):
        """Ensure that an error in one deliverymethod is not blocking all mehthods."""
        # cover failing delivery
        self._notification_run()

    def test_errors_passing(self):
        """Ensure that errors do not kill the whole delivery."""

        class ErrorImplementation(SingleNotificationMethod):
            METHOD_NAME = 'ErrorImplementation'

            def get_targets(self):
                return [1]

            def send(self, target):
                raise KeyError('This could be any error')

        self._notification_run(ErrorImplementation)


class BulkNotificationMethodTests(BaseNotificationIntegrationTest):
    """Tests for BulkNotificationMethod classes specifically.

    General tests for NotificationMethods are in BaseNotificationTests.
    """

    def test_BulkNotificationMethod(self):
        """Ensure the implementation requirements are tested.

        MixinNotImplementedError needs to raise if the send_bulk() method is not set.
        """

        class WrongImplementation(BulkNotificationMethod):
            METHOD_NAME = 'WrongImplementationBulk'

            def get_targets(self):
                return [1]

        with self.assertLogs(logger='inventree', level='ERROR'):
            self._notification_run(WrongImplementation)


class SingleNotificationMethodTests(BaseNotificationIntegrationTest):
    """Tests for SingleNotificationMethod classes specifically.

    General tests for NotificationMethods are in BaseNotificationTests.
    """

    def test_SingleNotificationMethod(self):
        """Ensure the implementation requirements are tested.

        MixinNotImplementedError needs to raise if the send() method is not set.
        """

        class WrongImplementation(SingleNotificationMethod):
            METHOD_NAME = 'WrongImplementationSingle'

            def get_targets(self):
                return [1]

        with self.assertLogs(logger='inventree', level='ERROR'):
            self._notification_run(WrongImplementation)
