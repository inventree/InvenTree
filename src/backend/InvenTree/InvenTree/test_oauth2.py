"""Tests for the enforcement of OAuth2 token scopes."""

import json
import re
from datetime import timedelta
from http.cookies import SimpleCookie

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import override_settings
from django.urls import Resolver404, resolve, reverse
from django.utils import timezone

from allauth.account.models import EmailAddress
from drf_spectacular.generators import EndpointEnumerator
from oauth2_provider.contrib.rest_framework.authentication import OAuth2Authentication
from oauth2_provider.models import AccessToken, Application
from rest_framework import permissions
from rest_framework.test import APIClient

from InvenTree.permissions import IsAuthenticatedOrReadScope, OASTokenMixin
from InvenTree.schema import combine_scope_alternatives
from InvenTree.unit_test import InvenTreeAPITestCase
from users.authentication import ExtendedOAuth2Authentication
from users.models import ApiToken
from users.oauth2_scopes import DEFAULT_READ, DEFAULT_STAFF, oauth2_scopes

# Any client which is not a browser can set a matching CSRF cookie and header
CSRF_TOKEN = 'A' * 32


@override_settings(
    SITE_URL='http://testserver', CSRF_TRUSTED_ORIGINS=['http://testserver']
)
class OAuth2ScopeTests(InvenTreeAPITestCase):
    """Tests that OAuth2 tokens can only be used within their scopes."""

    roles = ['admin.view', 'admin.change', 'part_category.view', 'part_category.add']
    auto_login = False

    @classmethod
    def setUpTestData(cls):
        """Create an OAuth2 application to issue tokens for."""
        super().setUpTestData()

        cls.application = Application.objects.create(
            name='Scope test application',
            client_type=Application.CLIENT_CONFIDENTIAL,
            authorization_grant_type=Application.GRANT_AUTHORIZATION_CODE,
            redirect_uris='https://example.com/callback',
        )

    def get_token(self, scope: str, user=None) -> AccessToken:
        """Issue an OAuth2 access token with the provided scopes."""
        return AccessToken.objects.create(
            user=user or self.user,
            application=self.application,
            token=f'oauth2-test-token-{AccessToken.objects.count()}',
            expires=timezone.now() + timedelta(hours=1),
            scope=scope,
        )

    def oauth2_request(self, token: AccessToken, method: str, url: str, data=None):
        """Perform an API request with an OAuth2 token, the way a non-browser client can.

        CSRF checks are enforced, but the client provides a matching CSRF cookie and header.

        The client is reused, as constructing a new one reloads the middleware chain
        (including a full WhiteNoise static file scan) on every request. Cookies are
        reset for each request, so no session state carries over between requests.
        """
        client = getattr(self, '_oauth2_client', None)
        if client is None:
            client = APIClient(enforce_csrf_checks=True, raise_request_exception=False)
            self._oauth2_client = client

        client.cookies = SimpleCookie({'csrftoken': CSRF_TOKEN})

        return client.generic(
            method,
            url,
            data=json.dumps(data or {}),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {token.token}',
            HTTP_X_CSRFTOKEN=CSRF_TOKEN,
        )

    def test_reported_user_escalation(self):
        """A read-only token of a staff user must not be able to modify users or their groups."""
        victim = get_user_model().objects.create_user('victim', password='password')
        admin_group = Group.objects.create(name='Administrators')
        url = reverse('api-user-detail', kwargs={'pk': victim.pk})
        data = {'is_staff': True, 'group_ids': [admin_group.pk]}

        token = self.get_token(f'openid {DEFAULT_READ}')

        response = self.oauth2_request(token, 'GET', url)
        self.assertEqual(response.status_code, 200)

        for method in ['PATCH', 'PUT', 'DELETE']:
            response = self.oauth2_request(token, method, url, data)
            self.assertEqual(response.status_code, 403, method)

        victim.refresh_from_db()
        self.assertFalse(victim.is_staff)
        self.assertFalse(victim.groups.exists())

        # With the staff scope, the token can perform the action (as the user has the permissions)
        token = self.get_token(f'openid {DEFAULT_READ} {DEFAULT_STAFF}')
        response = self.oauth2_request(token, 'PATCH', url, data)
        self.assertEqual(response.status_code, 200)

        victim.refresh_from_db()
        self.assertTrue(victim.is_staff)

    def test_write_requires_role_scope(self):
        """Creating an object requires the 'add' scopes for the associated roles."""
        url = reverse('api-part-category-list')

        token = self.get_token(f'openid {DEFAULT_READ}')
        response = self.oauth2_request(token, 'POST', url, {'name': 'Category'})
        self.assertEqual(response.status_code, 403)

        token = self.get_token('openid r:add:build r:add:part_category')
        response = self.oauth2_request(token, 'POST', url, {'name': 'Category'})
        self.assertEqual(response.status_code, 201)

    def test_scopes_do_not_extend_user_permissions(self):
        """A token can never do more than the user is allowed to do - regardless of the scopes."""
        token = self.get_token(' '.join(oauth2_scopes))

        # Superuser scope, but the user is not a superuser
        url = reverse('api-user-set-password', kwargs={'pk': self.user.pk})
        response = self.oauth2_request(token, 'PUT', url, {'password': 'new-pw'})
        self.assertEqual(response.status_code, 403)

        # Part scope, but the user does not have the part role
        response = self.oauth2_request(
            token, 'POST', reverse('api-part-list'), {'name': 'Part'}
        )
        self.assertEqual(response.status_code, 403)

    def test_token_cannot_issue_credentials(self):
        """An OAuth2 token must not be exchanged for an API token or a session."""
        token = self.get_token(' '.join(oauth2_scopes))
        n_tokens = ApiToken.objects.count()

        response = self.oauth2_request(token, 'GET', reverse('api-token'))
        self.assertEqual(response.status_code, 403)
        self.assertNotIn('sessionid', response.cookies)

        response = self.oauth2_request(
            token, 'POST', reverse('api-token-list'), {'name': 'token'}
        )
        self.assertEqual(response.status_code, 403)

        self.assertEqual(ApiToken.objects.count(), n_tokens)

    def test_token_only_accepted_by_api(self):
        """OAuth2 tokens are only handled by the API, not by the session based views."""
        self.assertNotIn(
            'oauth2_provider.middleware.OAuth2TokenMiddleware', settings.MIDDLEWARE
        )
        self.assertNotIn(
            'oauth2_provider.backends.OAuth2Backend', settings.AUTHENTICATION_BACKENDS
        )

        token = self.get_token(' '.join(oauth2_scopes))

        response = self.oauth2_request(token, 'GET', '/api/auth/v1/auth/session')
        self.assertEqual(response.status_code, 401)

        response = self.oauth2_request(
            token, 'POST', '/api/auth/v1/account/email', {'email': 'new@example.com'}
        )
        self.assertNotEqual(response.status_code, 200)
        self.assertFalse(EmailAddress.objects.filter(email='new@example.com').exists())

    def test_scope_check_cannot_be_bypassed(self):
        """Permission classes which override `has_permission` still enforce the token scopes."""

        class AllowEverything(OASTokenMixin, permissions.BasePermission):
            def has_permission(self, request, view):
                return True

            def get_required_alternate_scopes(self, request, view):
                return {'GET': [[DEFAULT_READ]]}

        class AllowAnyFirst(permissions.AllowAny, IsAuthenticatedOrReadScope):
            pass

        class OAuth2Request:
            def __init__(self, token):
                self.user = token.user
                self.auth = token
                self.method = 'GET'
                self.successful_authenticator = OAuth2Authentication()

        no_scope = OAuth2Request(self.get_token('openid'))
        read_scope = OAuth2Request(self.get_token(f'openid {DEFAULT_READ}'))

        for permission in [AllowEverything(), AllowAnyFirst()]:
            self.assertFalse(permission.has_permission(no_scope, None))
            self.assertTrue(permission.has_permission(read_scope, None))

    def test_combine_scope_alternatives(self):
        """The schema combines the scopes of all permission classes of a view."""
        self.assertEqual(
            combine_scope_alternatives([['a', 'b']], [['b', 'c']]), [['a', 'b', 'c']]
        )
        self.assertEqual(
            combine_scope_alternatives([['a'], ['b']], [['c']]),
            [['a', 'c'], ['b', 'c']],
        )
        self.assertEqual(combine_scope_alternatives([['a']], []), [])

    def test_api_endpoints(self):
        """Check the scope enforcement of all API endpoints, using tokens of a superuser.

        - A token without any scope can not access any endpoint
        - A token with the read scope can not perform any write operation
        - A token with all scopes can read from all endpoints (unless excluded from OAuth2)
        """
        admin = get_user_model().objects.create_superuser(
            'oauth2_admin', 'admin@example.com', 'password'
        )
        no_scope = self.get_token('openid', admin)
        read_scope = self.get_token(f'openid {DEFAULT_READ}', admin)
        all_scopes = self.get_token(' '.join(oauth2_scopes), admin)

        # Path parameters which are validated before the permission checks
        parameters = {
            'model': 'part',
            'lookup_field': 'pk',
            'statusmodel': 'StockStatus',
        }

        errors = []
        checked = 0

        for path, _regex, method, callback in EndpointEnumerator().get_api_endpoints():
            if not path.startswith('/api/'):
                continue

            # Views which do not use OAuth2 authentication ignore the token
            authentication_classes = getattr(callback, 'initkwargs', {}).get(
                'authentication_classes', callback.cls.authentication_classes
            )
            if ExtendedOAuth2Authentication not in authentication_classes:
                continue

            # Fill in the path parameters - the permission checks run before any lookup
            url = re.sub(
                r'{([^}]+)}', lambda match: parameters.get(match[1], '1'), path
            )

            try:
                if resolve(url).func != callback:
                    continue
            except Resolver404:
                continue

            checked += 1
            excluded = (
                f'{path.replace("{pk}", "{id}")}:{method.lower()}'
                in settings.OAUTH2_CHECK_EXCLUDED
            )

            response = self.oauth2_request(no_scope, method, url)
            if response.status_code != 403:
                errors.append(f'{method} {path}: no scope -> {response.status_code}')

            if method not in permissions.SAFE_METHODS:
                response = self.oauth2_request(read_scope, method, url)
                if response.status_code != 403:
                    errors.append(
                        f'{method} {path}: read scope -> {response.status_code}'
                    )

            elif method == 'GET' and not excluded:
                response = self.oauth2_request(all_scopes, method, url)
                if response.status_code in [401, 403]:
                    errors.append(
                        f'{method} {path}: all scopes -> {response.status_code}'
                    )

        self.assertGreater(checked, 500)
        self.assertEqual(errors, [], '\n'.join(errors))
