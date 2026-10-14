"""Core set of Notifications as a Plugin."""

from collections import defaultdict

from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Model
from django.template.loader import render_to_string
from django.utils.translation import gettext, override
from django.utils.translation import gettext_lazy as _

import requests
import structlog

import InvenTree.helpers_email
from common.notifications import get_user_language
from common.settings import get_global_setting
from plugin import InvenTreePlugin
from plugin.mixins import NotificationMixin, SettingsMixin

logger = structlog.get_logger('inventree')


class InvenTreeUINotifications(NotificationMixin, InvenTreePlugin):
    """Plugin mixin class for supporting UI notification methods."""

    NAME = 'InvenTreeUINotifications'
    TITLE = _('InvenTree UI Notifications')
    SLUG = 'inventree-ui-notification'
    AUTHOR = _('InvenTree contributors')
    DESCRIPTION = _('Integrated UI notification methods')
    VERSION = '1.0.0'

    def send_notification(
        self, target: Model, category: str, users: list[User], context: dict
    ) -> bool:
        """Create a UI notification entry for specified users."""
        from common.models import NotificationMessage

        ctx = context if context else {}
        entries = []

        if not users:
            return False

        # Ensure that there is always target object - see https://github.com/inventree/InvenTree/issues/10435
        if not target:
            target = self.plugin_config()

        # Bulk create notification messages for all provided users in their respective language context
        for user in users:
            user_language = get_user_language(user)
            with override(user_language):
                name = ctx.get('name')
                if name is not None:
                    name = gettext(str(name))

                message = ctx.get('message')
                if message is not None:
                    message = gettext(str(message))

            entries.append(
                NotificationMessage(
                    target_object=target,
                    source_object=user,
                    user=user,
                    category=category,
                    name=name,
                    message=message,
                    link=ctx.get('link'),
                )
            )

        NotificationMessage.objects.bulk_create(entries, batch_size=250)

        return True


class InvenTreeEmailNotifications(NotificationMixin, SettingsMixin, InvenTreePlugin):
    """Plugin mixin class for supporting email notification methods."""

    NAME = 'InvenTreeEmailNotifications'
    TITLE = _('InvenTree Email Notifications')
    SLUG = 'inventree-email-notification'
    AUTHOR = _('InvenTree contributors')
    DESCRIPTION = _('Integrated email notification methods')
    VERSION = '1.0.0'

    USER_SETTINGS = {
        'NOTIFY_BY_EMAIL': {
            'name': _('Allow email notifications'),
            'description': _('Allow email notifications to be sent to this user'),
            'default': True,
            'validator': bool,
        }
    }

    def send_notification(
        self, target: Model, category: str, users: list[User], context: dict
    ) -> bool:
        """Send notification to the specified targets."""
        # Ignore if there is no template provided to render
        if not context.get('template'):
            return False

        # Group target users by their preferred language
        language_groups: dict[str, list[str]] = defaultdict(list)

        for user in users:
            # Skip if the user does not want to receive email notifications
            if not self.get_user_setting('NOTIFY_BY_EMAIL', user, backup_value=False):
                continue

            if email := InvenTree.helpers_email.get_email_for_user(user):
                user_language = get_user_language(user)
                language_groups[user_language].append(email)

        if not language_groups:
            # No recipients found, so we cannot send the email
            return False

        instance_title = get_global_setting('INVENTREE_INSTANCE')
        raw_subject = context['template'].get('subject', '')
        template_name = context['template']['html']

        for user_language, recipients in language_groups.items():
            with override(user_language):
                # Translate subject
                subject = gettext(str(raw_subject))
                if instance_title:
                    subject = f'[{instance_title}] {subject}'

                # Build localized context copy so template rendering evaluates strings in user locale
                ctx = dict(context)
                if 'name' in ctx and ctx['name'] is not None:
                    ctx['name'] = gettext(str(ctx['name']))
                if 'message' in ctx and ctx['message'] is not None:
                    ctx['message'] = gettext(str(ctx['message']))

                # Re-render html_message with translated strings and templates
                html_message = render_to_string(template_name, ctx)

                InvenTree.helpers_email.send_email(
                    subject,
                    '',
                    recipients,
                    html_message=html_message,
                    force_async=not settings.TESTING,
                )

        return True


class InvenTreeSlackNotifications(NotificationMixin, SettingsMixin, InvenTreePlugin):
    """Plugin mixin class for supporting Slack notification methods."""

    NAME = 'InvenTreeSlackNotifications'
    TITLE = _('InvenTree Slack Notifications')
    SLUG = 'inventree-slack-notification'
    AUTHOR = _('InvenTree contributors')
    DESCRIPTION = _('Integrated Slack notification methods')
    VERSION = '1.0.0'

    SETTINGS = {
        'NOTIFICATION_SLACK_URL': {
            'name': _('Slack incoming webhook URL'),
            'description': _('URL that is used to send messages to a slack channel'),
            'protected': True,
        }
    }

    def send_notification(
        self, target: Model, category: str, users: list[User], context: dict
    ) -> bool:
        """Send the notifications out via slack."""
        url = self.get_setting('NOTIFICATION_SLACK_URL')

        if not url:
            return False

        ret = requests.post(
            url,
            json={
                'text': str(context['message']),
                'blocks': [
                    {
                        'type': 'section',
                        'text': {'type': 'plain_text', 'text': str(context['name'])},
                    },
                    {
                        'type': 'section',
                        'text': {'type': 'mrkdwn', 'text': str(context['message'])},
                        'accessory': {
                            'type': 'button',
                            'text': {
                                'type': 'plain_text',
                                'text': str(_('Open link')),
                                'emoji': True,
                            },
                            'value': f'{category}_{target.pk}' if target else '',
                            'url': context['link'],
                            'action_id': 'button-action',
                        },
                    },
                ],
            },
            timeout=10,
        )

        return ret.ok
