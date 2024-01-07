"""Configuration for Sentry.io error reporting."""

import logging

from django.conf import settings
from django.core.exceptions import ValidationError
from django.http import Http404

import rest_framework.exceptions
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

import InvenTree.version

logger = logging.getLogger('inventree')


def default_sentry_dsn():
    """Return the default Sentry.io DSN for InvenTree"""
    return 'https://3928ccdba1d34895abde28031fd00100@o378676.ingest.sentry.io/6494600'


def sentry_ignore_errors():
    """Return a list of error types to ignore.

    These error types will *not* be reported to sentry.io.
    """
    return [
        Http404,
        ValidationError,
        rest_framework.exceptions.AuthenticationFailed,
        rest_framework.exceptions.NotAuthenticated,
        rest_framework.exceptions.PermissionDenied,
        rest_framework.exceptions.ValidationError,
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


def report_exception(exc):
    """Report an exception to sentry.io"""
    if settings.SENTRY_ENABLED and settings.SENTRY_DSN:
        if not any(isinstance(exc, e) for e in sentry_ignore_errors()):
            logger.info("Reporting exception to sentry.io: %s", exc)

            try:
                sentry_sdk.capture_exception(exc)
            except Exception:
                logger.warning("Failed to report exception to sentry.io")
