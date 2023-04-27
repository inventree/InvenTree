"""Configuration for Sentry.io error reporting."""

import logging

from django.core.exceptions import Http404

logger = logging.getLogger('inventree')


def sentry_before_send(event, hint):
    """Run before sending an event to Sentry.io"""

    # Ignore the following error types
    ignore_errors = [
        Http404,
    ]

    if 'exc_info' in hint:
        exc_type, exc_value, tb = hint['exc_info']
        if exc_type in ignore_errors:
            return None

    logger.info('Sending error to Sentry.io: {e}'.format(e=event))

    return event
