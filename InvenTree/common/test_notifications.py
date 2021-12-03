# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from .notifications import NotificationMethod, SingleNotificationMethod, BulkNotificationMethod
from part.test_part import BaseNotificationIntegrationTest


class NotificationTests(BaseNotificationIntegrationTest):

    def test_NotificationMethod(self):
        """ensure the implementation requirements are tested"""

        class FalseNotificationMethod(NotificationMethod):
            pass

        class AnotherFalseNotificationMethod(NotificationMethod):
            def send(self):
                pass

        with self.assertRaises(NotImplementedError):
            FalseNotificationMethod('', '', '')

        with self.assertRaises(NotImplementedError):
            AnotherFalseNotificationMethod('', '', '')

    def test_SingleNotificationMethod(self):
        """ensure the implementation requirements are tested"""

        class WrongImplementation(SingleNotificationMethod):
            pass

        with self.assertRaises(NotImplementedError):
            self._notification_run()

    def test_BulkNotificationMethod(self):
        """ensure the implementation requirements are tested"""

        class WrongImplementation(BulkNotificationMethod):
            pass

        with self.assertRaises(NotImplementedError):
            self._notification_run()


# A integration test for notifications is provided in test_part.PartNotificationTest
