"""Sample plugin which responds to events."""

from django.conf import settings

import structlog

from plugin import InvenTreePlugin
from plugin.mixins import MailMixin

logger = structlog.get_logger('inventree')


class MailPluginSample(MailMixin, InvenTreePlugin):
    """A sample plugin which provides supports for processing mails."""

    NAME = 'MailPlugin'
    SLUG = 'samplemail'
    TITLE = 'Sample Mail Plugin'

    def process_mail_out(self, mail, *args, **kwargs):
        """Custom mail processing."""
        print(f"Processing outgoing mail: '{mail}'")
        print('args:', str(args))
        print('kwargs:', str(kwargs))

        # Issue warning that we can test for
        if settings.PLUGIN_TESTING:
            logger.debug('Mail `%s` triggered in sample plugin going out', mail)

    def process_mail_in(self, mail, *args, **kwargs):
        """Custom mail processing."""
        print(f"Processing incoming mail: '{mail}'")
        print('args:', str(args))
        print('kwargs:', str(kwargs))

        # Issue warning that we can test for
        if settings.PLUGIN_TESTING:
            logger.debug('Mail `%s` triggered in sample plugin coming in', mail)
