"""Tests for middleware functions."""

from unittest.mock import patch

from django.conf import settings
from django.http import Http404
from django.urls import reverse

from error_report.models import Error

from InvenTree.exceptions import log_error
from InvenTree.helpers_mfa import get_codes
from InvenTree.unit_test import InvenTreeTestCase


class MiddlewareTests(InvenTreeTestCase):
    """Test for middleware functions."""

    def check_path(self, url, code=200, auth_header=None, **kwargs):
        """Helper function to run a request."""
        headers = {'accept': 'application/json'}
        if auth_header:
            headers['Authorization'] = auth_header
        response = self.client.get(url, headers=headers, **kwargs)
        self.assertEqual(response.status_code, code)
        return response

    def test_AuthRequiredMiddleware(self):
        """Test the auth middleware."""
        # test that /api/ routes go through
        self.check_path(reverse('api-inventree-info'))

        # logout
        self.client.logout()

        # check that account things are rereouted
        self.check_path(reverse('account_login'), 302)

        # check that frontend code is redirected to login
        response = self.check_path(reverse('index'), 302)
        self.assertEqual(response.url, '/accounts/login/?next=/')

    def test_Check2FAMiddleware(self):
        """Test the 2FA middleware."""
        url = reverse('api-part-list')

        self.assignRole(role='part.view', group=self.group)
        # Ensure that normal access works with mfa enabled
        with self.settings(MFA_ENABLED=True):
            self.check_path(url)
        # Ensure that normal access works with mfa disabled
        with self.settings(MFA_ENABLED=False):
            self.check_path(url)

        # Now enforce MFA for the user
        with self.settings(MFA_ENABLED=True) and patch.dict(
            'os.environ', {'INVENTREE_LOGIN_ENFORCE_MFA': 'True'}
        ):
            # Enforced but not logged in via mfa -> should give 403
            response = self.check_path(url, 401)
            self.assertContains(
                response,
                'You must enable two-factor authentication before doing anything else.',
                status_code=401,
            )

            # Register a token and try again
            rc_codes = get_codes(self.user)[1]
            self.client.logout()
            # Login step 1
            self.client.post(
                reverse('browser:account:login'),
                {'username': self.username, 'password': self.password},
                content_type='application/json',
            )
            # Login step 2
            self.client.post(
                reverse('browser:mfa:authenticate'),
                {'code': rc_codes[0]},
                expected_code=401,
                content_type='application/json',
            )
            rsp3 = self.client.post(
                reverse('browser:mfa:trust'),
                {'trust': False},
                expected_code=200,
                content_type='application/json',
            )
            self.assertEqual(rsp3.status_code, 200)
            self.check_path(url)

    def test_token_auth(self):
        """Test auth with token auth."""
        target = reverse('api-license')

        # get token
        response = self.client.get(reverse('api-token'), format='json', data={})
        token = response.data['token']

        # logout
        self.client.logout()
        # this should raise a 401

        self.check_path(target, 401)

        # Request with broken token
        self.check_path(target, 401, auth_header='Token abcd123')

        # should still fail without token
        self.check_path(target, 401)

        # request with token - should work
        self.check_path(target, auth_header=f'Token {token}')

        # Request something that is not on the API - should still work
        self.check_path(reverse('auth-check'), auth_header=f'Token {token}')

    def test_error_exceptions(self):
        """Test that ignored errors are not logged."""
        self.assignRole('part.view')

        def check(excpected_nbr=0):
            # Check that errors are empty
            errors = Error.objects.all()
            self.assertEqual(len(errors), excpected_nbr)

        # Test normal setup
        check()
        response = self.client.get(reverse('api-part-detail', kwargs={'pk': 9999}))
        self.assertEqual(response.status_code, 404)
        check()

        # Test manual logging
        try:
            raise Http404
        except Http404:
            log_error('testpath')

        # Test setup without ignored errors
        with self.settings(IGNORED_ERRORS=[]):
            try:
                raise Http404
            except Http404:
                log_error('testpath')
            check(1)

    def do_positive_test(self, response):
        """Helper function to check for positive test results."""
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'INVE-E7')
        self.assertContains(response, 'window.INVENTREE_SETTINGS')

    def test_site_url_checks(self):
        """Test that the site URL check is correctly working."""
        # simple setup
        with self.settings(
            SITE_URL='http://testserver', CSRF_TRUSTED_ORIGINS=['http://testserver']
        ):
            response = self.client.get(reverse('web'))
            self.do_positive_test(response)

        # simple setup with wildcard
        with self.settings(
            SITE_URL='http://testserver', CSRF_TRUSTED_ORIGINS=['http://*.testserver']
        ):
            response = self.client.get(reverse('web'))
            self.do_positive_test(response)

    def test_site_lax_protocol(self):
        """Test that the site URL check is correctly working with/without lax protocol check."""
        # Test that a completely different host fails
        with self.settings(
            SITE_URL='https://testserver', CSRF_TRUSTED_ORIGINS=['https://testserver']
        ):
            response = self.client.get(
                reverse('web'), headers={'host': 'otherhost.example.com'}
            )
            self.assertContains(response, 'INVE-E7: The visited path', status_code=500)

        # Simple setup with proxy
        with self.settings(
            SITE_URL='https://testserver', CSRF_TRUSTED_ORIGINS=['https://testserver']
        ):
            response = self.client.get(reverse('web'))
            self.do_positive_test(response)

        # No worky if strong security
        with self.settings(
            SITE_URL='https://testserver',
            CSRF_TRUSTED_ORIGINS=['https://testserver'],
            SITE_LAX_PROTOCOL_CHECK=False,
        ):
            response = self.client.get(reverse('web'))
            self.assertContains(response, 'INVE-E7: The visited path', status_code=500)

    def test_site_url_port(self):
        """URL checks with different ports."""
        with self.settings(
            SITE_URL='https://testserver:8000',
            CSRF_TRUSTED_ORIGINS=['https://testserver:8000'],
        ):
            response = self.client.get(
                reverse('web'), headers={'host': 'testserver:8008'}
            )
            self.do_positive_test(response)

        # Try again with strict protocol check
        with self.settings(
            SITE_URL='https://testserver:8000',
            CSRF_TRUSTED_ORIGINS=['https://testserver:8000'],
            SITE_LAX_PROTOCOL_CHECK=False,
        ):
            response = self.client.get(
                reverse('web'), headers={'host': 'testserver:8008'}
            )
            self.assertContains(response, 'INVE-E7: The visited path', status_code=500)

    def test_site_url_checks_multi(self):
        """Test that the site URL check is correctly working in a multi-site setup."""
        # multi-site setup with trusted origins
        with self.settings(
            SITE_URL='https://testserver.example.com',
            CSRF_TRUSTED_ORIGINS=[
                'http://testserver',
                'https://testserver.example.com',
            ],
        ):
            # this will run with testserver as host by default
            response = self.client.get(reverse('web'))
            self.do_positive_test(response)

            # Now test with the "outside" url name
            response = self.client.get(
                'https://testserver.example.com/web/',
                SERVER_NAME='testserver.example.com',
            )
            self.do_positive_test(response)

            # A non-trusted origin must still fail in multi - origin setup
            response = self.client.get(
                'https://not-my-testserver.example.com/web/',
                SERVER_NAME='not-my-testserver.example.com',
            )
            self.assertEqual(response.status_code, 500)

            # Even if it is a subdomain
            response = self.client.get(
                'https://not-my.testserver.example.com/web/',
                SERVER_NAME='not-my.testserver.example.com',
            )
            self.assertEqual(response.status_code, 500)

    def test_site_url_checks_fails(self):
        """Test that the site URL check is correctly failing.

        Important for security.
        """
        # wrongly set but in debug -> is ignored
        with self.settings(SITE_URL='https://example.com', DEBUG=True):
            response = self.client.get(reverse('web'))
            self.do_positive_test(response)

        # wrongly set cors
        with self.settings(
            SITE_URL='http://testserver',
            CORS_ORIGIN_ALLOW_ALL=False,
            CSRF_TRUSTED_ORIGINS=['https://example.com'],
        ):
            response = self.client.get(reverse('web'))
            self.assertContains(
                response, 'is not in the TRUSTED_ORIGINS', status_code=500
            )
            self.assertNotContains(
                response, 'window.INVENTREE_SETTINGS', status_code=500
            )

        # wrongly set site URL
        with self.settings(
            SITE_URL='https://example.com',
            CSRF_TRUSTED_ORIGINS=['http://localhost:8000'],
        ):
            response = self.client.get(reverse('web'))
            self.assertContains(
                response,
                'INVE-E7: The visited path `http://testserver` ',
                status_code=500,
            )
            self.assertNotContains(
                response, 'window.INVENTREE_SETTINGS', status_code=500
            )

            # Log stuff # TODO remove
            print(
                '###DBG-TST###',
                'site',
                settings.SITE_URL,
                'trusted',
                settings.CSRF_TRUSTED_ORIGINS,
            )

            # Check that the correct step triggers the error message
            self.assertContains(
                response,
                'INVE-E7: The visited path `http://testserver` does not match',
                status_code=500,
            )
