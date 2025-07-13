"""Configuration for Sentry.io error reporting."""

from typing import Optional

from django.conf import settings
from django.core.exceptions import ValidationError
from django.http import Http404
from django.template.exceptions import TemplateSyntaxError

import rest_framework.exceptions
import sentry_sdk
import structlog
from djmoney.contrib.exchange.exceptions import MissingRate
from sentry_sdk.integrations.django import DjangoIntegration

import InvenTree.version

logger = structlog.get_logger('inventree')


def default_sentry_dsn():
    """Return the default Sentry.io DSN for InvenTree."""
    return 'https://3928ccdba1d34895abde28031fd00100@o378676.ingest.sentry.io/6494600'


def sentry_ignore_errors():
    """Return a list of error types to ignore.

    These error types will *not* be reported to sentry.io.
    """
    return [
        Http404,
        MissingRate,
        TemplateSyntaxError,
        ValidationError,
        rest_framework.exceptions.AuthenticationFailed,
        rest_framework.exceptions.NotAuthenticated,
        rest_framework.exceptions.PermissionDenied,
        rest_framework.exceptions.ValidationError,
    ]


def init_sentry(dsn, sample_rate, tags):
    """Initialize sentry.io error reporting."""
    logger.info('Initializing sentry.io integration')

    sentry_sdk.init(
        dsn=dsn,
        integrations=[DjangoIntegration()],
        traces_sample_rate=sample_rate,
        send_default_pii=True,
        ignore_errors=sentry_ignore_errors(),
        release=InvenTree.version.INVENTREE_SW_VERSION,
        environment='development'
        if InvenTree.version.isInvenTreeDevelopmentVersion()
        else 'production',
    )

    for key, val in tags.items():
        sentry_sdk.set_tag(f'inventree_{key}', val)

    sentry_sdk.set_tag('api', InvenTree.version.inventreeApiVersion())
    sentry_sdk.set_tag('platform', InvenTree.version.inventreePlatform())
    sentry_sdk.set_tag('git_branch', InvenTree.version.inventreeBranch())
    sentry_sdk.set_tag('git_commit', InvenTree.version.inventreeCommitHash())
    sentry_sdk.set_tag('git_date', InvenTree.version.inventreeCommitDate())


def report_exception(exc, scope: Optional[dict] = None):
    """Report an exception to sentry.io."""
    assert settings.TESTING == False, (
        'report_exception should not be called in testing mode'
    )

    if settings.SENTRY_ENABLED and settings.SENTRY_DSN:
        if not any(isinstance(exc, e) for e in sentry_ignore_errors()):
            logger.info('Reporting exception to sentry.io: %s', exc)

            try:
                sentry_sdk.capture_exception(exc, scope=scope)
            except Exception:
                logger.warning('Failed to report exception to sentry.io')
