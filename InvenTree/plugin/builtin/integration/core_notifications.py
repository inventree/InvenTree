# -*- coding: utf-8 -*-
"""Core set of Notifications as a Plugin"""
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from allauth.account.models import EmailAddress

import InvenTree.tasks
from plugin import InvenTreePlugin
from plugin.mixins import BulkNotificationMethod, SettingsMixin


class PlgMixin:
    def get_plugin(self):
        return CoreNotificationsPlugin


class CoreNotificationsPlugin(SettingsMixin, InvenTreePlugin):
    """
    Core notification methods for InvenTree
    """

    NAME = "CoreNotificationsPlugin"
    AUTHOR = _('InvenTree contributors')
    DESCRIPTION = _('Integrated outgoing notificaton methods')

    SETTINGS = {
        'ENABLE_NOTIFICATION_EMAILS': {
            'name': _('Enable email notifications'),
            'description': _('Allow sending of emails for event notifications'),
            'default': False,
            'validator': bool,
        },
    }

    class EmailNotification(PlgMixin, BulkNotificationMethod):
        METHOD_NAME = 'mail'
        METHOD_ICON = 'fa-envelope'
        CONTEXT_EXTRA = [
            ('template', ),
            ('template', 'html', ),
            ('template', 'subject', ),
        ]
        GLOBAL_SETTING = 'ENABLE_NOTIFICATION_EMAILS'
        USER_SETTING = {
            'name': _('Enable email notifications'),
            'description': _('Allow sending of emails for event notifications'),
            'default': True,
            'validator': bool,
        }

        def get_targets(self):
            """
            Return a list of target email addresses,
            only for users which allow email notifications
            """

            allowed_users = []

            for user in self.targets:
                allows_emails = self.usersetting(user)

                if allows_emails:
                    allowed_users.append(user)

            return EmailAddress.objects.filter(
                user__in=allowed_users,
            )

        def send_bulk(self):
            html_message = render_to_string(self.context['template']['html'], self.context)
            targets = self.targets.values_list('email', flat=True)

            InvenTree.tasks.send_email(self.context['template']['subject'], '', targets, html_message=html_message)

            return True
