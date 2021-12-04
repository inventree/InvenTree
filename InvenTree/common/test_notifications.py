# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from .notifications import NotificationMethod, SingleNotificationMethod, BulkNotificationMethod
from part.test_part import BaseNotificationIntegrationTest


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

    def test_errors_passing(self):
        """ensure that errors do not kill the whole delivery"""

        class ErrorImplementation(SingleNotificationMethod):
            METHOD_NAME = 'ErrorImplementation'

            def get_targets(self):
                return [1, ]

            def send(self, target):
                raise KeyError('This could be any error')

        self._notification_run()


class ClassNotificationTests(BaseNotificationIntegrationTest):

    def test_SingleNotificationMethod(self):
        """ensure the implementation requirements are tested"""

        class WrongImplementation(SingleNotificationMethod):
            METHOD_NAME = 'WrongImplementation1'

            def get_targets(self):
                return [1, ]

        with self.assertRaises(NotImplementedError):
            self._notification_run()

    def test_BulkNotificationMethod(self):
        """ensure the implementation requirements are tested"""

        class WrongImplementation(BulkNotificationMethod):
            METHOD_NAME = 'WrongImplementation2'

            def get_targets(self):
                return [1, ]

        with self.assertRaises(NotImplementedError):
            self._notification_run()


# A integration test for notifications is provided in test_part.PartNotificationTest
