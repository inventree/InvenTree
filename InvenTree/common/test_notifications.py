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
        print('TESTING SingleNotificationMethod')

        class WrongImplementation(SingleNotificationMethod):
            def setup(self):
                print('running setup on WrongImplementation')
                return super().setup()

        with self.assertRaises(NotImplementedError):
            self._notification_run()

    def test_BulkNotificationMethod(self):
        """ensure the implementation requirements are tested"""
        print('TESTING BulkNotificationMethod')

        class WrongImplementation(BulkNotificationMethod):
            def setup(self):
                print('running setup on WrongImplementation')
                return super().setup()

        with self.assertRaises(NotImplementedError):
            self._notification_run()


# A integration test for notifications is provided in test_part.PartNotificationTest
