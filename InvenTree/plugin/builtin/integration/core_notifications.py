# -*- coding: utf-8 -*-
"""Core set of Notifications as a Plugin"""
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from allauth.account.models import EmailAddress

from plugin import IntegrationPluginBase, registry
from plugin.mixins import BulkNotificationMethod, SettingsMixin
from common.models import InvenTreeUserSetting
import InvenTree.tasks


class CoreNotificationsPlugin(SettingsMixin, IntegrationPluginBase):
    """
    Core notification methods for InvenTree
    """

    PLUGIN_NAME = "CoreNotificationsPlugin"
    AUTHOR = _('InvenTree contributors')
    DESCRIPTION = _('Integrated outgoing notificaton methods')

    SETTINGS = {
        'ENABLE_NOTIFICATION_EMAILS': {
            'name': _('Enable email notifications'),
            'description': _('Allow sending of emails for event notifications'),
            'default': True,
            'validator': bool,
        },
    }

    class EmailNotification(BulkNotificationMethod):
        METHOD_NAME = 'mail'
        CONTEXT_EXTRA = [
            ('template', ),
            ('template', 'html', ),
            ('template', 'subject', ),
        ]

        def get_targets(self):
            """
            Return a list of target email addresses,
            only for users which allow email notifications
            """

            # Check if method globally enabled
            plg = registry.plugins.get(CoreNotificationsPlugin.PLUGIN_NAME.lower())
            if plg and not plg.get_setting('ENABLE_NOTIFICATION_EMAILS'):
                return

            allowed_users = []

            for user in self.targets:
                allows_emails = InvenTreeUserSetting.get_setting('NOTIFICATION_SEND_EMAILS', user=user)

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
