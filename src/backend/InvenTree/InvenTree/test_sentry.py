"""Tests for sentry.io error reporting integration."""

from unittest import mock

from django.core.exceptions import ValidationError
from django.http import Http404
from django.test import SimpleTestCase, override_settings

import InvenTree.sentry as sentry


class SentryIgnoreErrorsTest(SimpleTestCase):
    """Tests for sentry_ignore_errors()."""

    def test_known_error_types_are_ignored(self):
        """Http404 and DRF/Django validation errors must be in the ignore list."""
        ignored = sentry.sentry_ignore_errors()
        self.assertIn(Http404, ignored)
        self.assertIn(ValidationError, ignored)


class InitSentryTest(SimpleTestCase):
    """Tests for init_sentry()."""

    def call_init_sentry(self, **kwargs):
        """Call init_sentry with sentry_sdk mocked out, and return the mocked sentry_sdk.init call."""
        with (
            mock.patch('InvenTree.sentry.sentry_sdk.init') as mock_init,
            mock.patch('InvenTree.sentry.sentry_sdk.set_tag'),
        ):
            sentry.init_sentry('https://example.test/1', 0.1, {}, **kwargs)

        return mock_init

    def test_pii_disabled_by_default(self):
        """Regression test: send_default_pii must default to False.

        Previously init_sentry hard-coded send_default_pii=True, meaning enabling
        sentry.io reporting - which by default reports to InvenTree's own DSN -
        would always attach the reporting user's id/email, IP address and request
        data to every event, with no way to opt out.
        """
        mock_init = self.call_init_sentry()
        self.assertFalse(mock_init.call_args.kwargs['send_default_pii'])

    def test_pii_can_be_enabled(self):
        """An administrator can still explicitly opt in to sending PII."""
        mock_init = self.call_init_sentry(send_pii=True)
        self.assertTrue(mock_init.call_args.kwargs['send_default_pii'])


class ReportExceptionTest(SimpleTestCase):
    """Tests for report_exception()."""

    def call_report_exception(self, exc, enabled=True, dsn='https://example.test/1'):
        """Call report_exception with the given sentry settings, and sentry_sdk mocked out."""
        with (
            override_settings(TESTING=False, SENTRY_ENABLED=enabled, SENTRY_DSN=dsn),
            mock.patch('InvenTree.sentry.sentry_sdk.capture_exception') as mock_capture,
        ):
            sentry.report_exception(exc)

        return mock_capture

    def test_skipped_if_sentry_not_enabled(self):
        """No exception should be reported if sentry is not enabled."""
        mock_capture = self.call_report_exception(ValueError('boom'), enabled=False)
        mock_capture.assert_not_called()

    def test_skipped_if_dsn_not_configured(self):
        """No exception should be reported if no DSN is configured."""
        mock_capture = self.call_report_exception(ValueError('boom'), dsn='')
        mock_capture.assert_not_called()

    def test_ignored_error_type_is_not_reported(self):
        """Error types in the ignore list must not be reported."""
        mock_capture = self.call_report_exception(Http404())
        mock_capture.assert_not_called()

    def test_other_errors_are_reported(self):
        """An error type not in the ignore list must be reported."""
        exc = ValueError('boom')
        mock_capture = self.call_report_exception(exc)
        mock_capture.assert_called_once_with(exc, scope=None)

    def test_capture_failure_is_swallowed(self):
        """report_exception must not raise if sentry_sdk itself fails."""
        with (
            override_settings(
                TESTING=False, SENTRY_ENABLED=True, SENTRY_DSN='https://example.test/1'
            ),
            mock.patch(
                'InvenTree.sentry.sentry_sdk.capture_exception',
                side_effect=RuntimeError('sentry is down'),
            ),
        ):
            sentry.report_exception(ValueError('boom'))
