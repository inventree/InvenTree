"""Configuration for Sentry.io error reporting."""

import logging

from django.core.exceptions import Http404

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

from InvenTree.version import INVENTREE_SW_VERSION

logger = logging.getLogger('inventree')


def default_sentry_dsn():
    """Return the default Sentry.io DSN for InvenTree"""

    return 'https://3928ccdba1d34895abde28031fd00100@o378676.ingest.sentry.io/6494600'


def sentry_ignore_errors():
    """Return a list of error types to ignore"""

    return [
        Http404,
    ]


def init_sentry(dsn, sample_rate, tags):
    """Initialize sentry.io error reporting"""

    logger.info("Initializing sentry.io integration")

    sentry_sdk.init(
        dsn=dsn,
        integrations=[DjangoIntegration()],
        traces_sample_rate=sample_rate,
        send_default_pii=True,
        ignore_errors=sentry_ignore_errors(),
        release=INVENTREE_SW_VERSION,
    )

    for key, val in tags.items():
        sentry_sdk.set_tag(f'inventree_{key}', val)
