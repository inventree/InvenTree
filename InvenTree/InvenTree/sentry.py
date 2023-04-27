"""Configuration for Sentry.io error reporting."""

import logging

from django.core.exceptions import Http404

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

logger = logging.getLogger('inventree')


def default_sentry_dsn():
    """Return the default Sentry.io DSN for InvenTree"""

    return 'https://3928ccdba1d34895abde28031fd00100@o378676.ingest.sentry.io/6494600'


def sentry_before_send(event, hint):
    """Run before sending an event to Sentry.io"""

    # Ignore the following error types
    ignore_errors = [
        Http404,
    ]

    if 'exc_info' in hint:
        exc_type, exc_value, tb = hint['exc_info']
        if exc_type in ignore_errors:
            logger.debug("sentry_before_send: Ignoring error type '{exc_type}'")
            return None

    logger.info(f'Sending error to sentry.io: {event}')

    return event


def init_sentry(dsn, sample_rate, tags):
    """Initialize sentry.io error reporting"""

    logger.info("Initializing sentry.io integration")

    sentry_sdk.init(
        dsn=dsn,
        integrations=[DjangoIntegration()],
        traces_sample_rate=sample_rate,
        send_default_pii=True,
        before_send=sentry_before_send,
    )

    for key, val in tags.items():
        sentry_sdk.set_tag(f'inventree_{key}', val)
