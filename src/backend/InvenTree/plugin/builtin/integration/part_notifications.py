"""Core set of Notifications as a Plugin."""

from django.utils.translation import gettext_lazy as _

import structlog

import common.notifications
import InvenTree.helpers_model
from part.models import Part
from plugin import InvenTreePlugin
from plugin.mixins import EventMixin, SettingsMixin

logger = structlog.get_logger('inventree')


class PartNotificationsPlugin(SettingsMixin, EventMixin, InvenTreePlugin):
    """Core notification methods for InvenTree."""

    NAME = 'PartNotificationsPlugin'
    TITLE = _('Part Notifications')
    AUTHOR = _('InvenTree contributors')
    DESCRIPTION = _('Notify users about part changes')
    VERSION = '1.0.0'

    SETTINGS = {
        'ENABLE_PART_NOTIFICATIONS': {
            'name': _('Send notifications'),
            'description': _('Send notifications for part changes to subscribed users'),
            'default': False,
            'validator': bool,
        }
    }

    def wants_process_event(self, event):
        """Return whether given event should be processed or not."""
        return event.startswith('part_part.')

    def process_event(self, event, *args, **kwargs):
        """Custom event processing."""
        if not self.get_setting('ENABLE_PART_NOTIFICATIONS'):
            return
        part = Part.objects.get(pk=kwargs['id'])
        part_action = event.split('.')[-1]

        name = _('Changed part notification')
        common.notifications.trigger_notification(
            part,
            'part.notification',
            target_fnc=part.get_subscribers,
            check_recent=False,
            context={
                'part': part,
                'name': name,
                'message': _(
                    f'The part `{part.name}` has been triggered with a `{part_action}` event'
                ),
                'link': InvenTree.helpers_model.construct_absolute_url(
                    part.get_absolute_url()
                ),
                'template': {
                    'html': 'email/part_event_notification.html',
                    'subject': name,
                },
            },
        )
