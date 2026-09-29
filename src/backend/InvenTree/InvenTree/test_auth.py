"""Test the sso and auth module functionality."""

from django.conf import settings as django_settings
from django.contrib.auth.models import Group, User
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import RequestFactory, override_settings
from django.test.testcases import TransactionTestCase
from django.urls import reverse

from allauth.socialaccount.models import SocialAccount, SocialLogin

from common.models import InvenTreeSetting
from InvenTree import sso
from InvenTree.auth_overrides import CustomSocialAccountAdapter, RegistrationMixin
from InvenTree.unit_test import InvenTreeAPITestCase


class Dummy:
    """Simulate super class of RegistrationMixin."""

    def save_user(self, _request, user: User, *args) -> User:
        """This method is only used that the super() call of RegistrationMixin does not fail."""
        return user


class MockRegistrationMixin(RegistrationMixin, Dummy):
    """Mocked implementation of the RegistrationMixin."""


class TestSsoGroupSync(TransactionTestCase):
    """Tests for the SSO group sync feature."""

    def setUp(self):
        """Construct sociallogin object for test cases."""
        # configure SSO
        InvenTreeSetting.set_setting('LOGIN_ENABLE_SSO_GROUP_SYNC', True)
        InvenTreeSetting.set_setting('SSO_GROUP_KEY', 'groups')
        InvenTreeSetting.set_setting(
            'SSO_GROUP_MAP', '{"idp_group": "inventree_group"}'
        )
        # configure sociallogin
        extra_data = {'userinfo': {'groups': ['idp_group']}}
        self.group = Group(name='inventree_group')
        self.group.save()
        # ensure default group exists
        user = User(username='testuser', first_name='Test', last_name='User')
        user.save()
        account = SocialAccount(user=user, extra_data=extra_data)
        self.sociallogin = SocialLogin(account=account)

    def test_group_added_to_user(self):
        """Check that a new SSO group is added to the user."""
        user: User = self.sociallogin.account.user
        self.assertEqual(user.groups.count(), 0)
        sso.ensure_sso_groups(None, self.sociallogin)
        self.assertEqual(user.groups.count(), 1)
        self.assertEqual(user.groups.first().name, 'inventree_group')

    def test_group_already_exists(self):
        """Check that existing SSO group is not modified."""
        user: User = self.sociallogin.account.user
        user.groups.add(self.group)
        self.assertEqual(user.groups.count(), 1)
        self.assertEqual(user.groups.first().name, 'inventree_group')
        sso.ensure_sso_groups(None, self.sociallogin)
        self.assertEqual(user.groups.count(), 1)
        self.assertEqual(user.groups.first().name, 'inventree_group')

    @override_settings(SSO_REMOVE_GROUPS=True)
    def test_remove_non_sso_group(self):
        """Check that any group not provided by IDP is removed."""
        user: User = self.sociallogin.account.user
        # group must be saved to database first
        group = Group(name='local_group')
        group.save()
        user.groups.add(group)
        self.assertEqual(user.groups.count(), 1)
        self.assertEqual(user.groups.first().name, 'local_group')
        sso.ensure_sso_groups(None, self.sociallogin)
        self.assertEqual(user.groups.count(), 1)
        self.assertEqual(user.groups.first().name, 'inventree_group')

    def test_override_default_group_with_sso_group(self):
        """The default group should be overridden if SSO groups are available."""
        user: User = self.sociallogin.account.user
        self.assertEqual(user.groups.count(), 0)
        Group(id=42, name='default_group').save()
        InvenTreeSetting.set_setting('SIGNUP_GROUP', 42)
        sso.ensure_sso_groups(None, self.sociallogin)
        MockRegistrationMixin().save_user(None, user, None)
        self.assertEqual(user.groups.count(), 1)
        self.assertEqual(user.groups.first().name, 'inventree_group')

    def test_default_group_without_sso_group(self):
        """If no SSO group is specified, the default group should be applied."""
        self.sociallogin.account.extra_data = {}
        user: User = self.sociallogin.account.user
        self.assertEqual(user.groups.count(), 0)
        Group(id=42, name='default_group').save()
        InvenTreeSetting.set_setting('SIGNUP_GROUP', 42)
        sso.ensure_sso_groups(None, self.sociallogin)
        MockRegistrationMixin().save_user(None, user, None)
        self.assertEqual(user.groups.count(), 1)
        self.assertEqual(user.groups.first().name, 'default_group')

    @override_settings(SSO_REMOVE_GROUPS=True)
    def test_remove_groups_overrides_default_group(self):
        """If no SSO group is specified, the default group should not be added if SSO_REMOVE_GROUPS=True."""
        user: User = self.sociallogin.account.user
        self.sociallogin.account.extra_data = {}
        self.assertEqual(user.groups.count(), 0)
        Group(id=42, name='default_group').save()
        InvenTreeSetting.set_setting('SIGNUP_GROUP', 42)
        sso.ensure_sso_groups(None, self.sociallogin)
        MockRegistrationMixin().save_user(None, user, None)
        # second ensure_sso_groups will be called by signal if social account changes
        sso.ensure_sso_groups(None, self.sociallogin)
        self.assertEqual(user.groups.count(), 0)

    def test_sso_group_created_if_not_exists(self):
        """If the mapped group does not exist, a new group with the same name should be created."""
        self.group.delete()
        self.assertEqual(Group.objects.filter(name='inventree_group').count(), 0)
        sso.ensure_sso_groups(None, self.sociallogin)
        self.assertEqual(Group.objects.filter(name='inventree_group').count(), 1)


class TestSocialAccountAdapter(TransactionTestCase):
    """Tests for CustomSocialAccountAdapter, used for all SSO logins."""

    def setUp(self):
        """Construct a fresh adapter for each test."""
        self.adapter = CustomSocialAccountAdapter()

    def test_pre_social_login_blocked_when_sso_disabled(self):
        """SSO logins (new or existing accounts) must be rejected outright when SSO is disabled."""
        InvenTreeSetting.set_setting('LOGIN_ENABLE_SSO', False)
        with self.assertRaises(PermissionDenied):
            self.adapter.pre_social_login(None, None)

    def test_pre_social_login_allowed_when_sso_enabled(self):
        """A normal SSO login attempt should pass through untouched when SSO is enabled."""
        InvenTreeSetting.set_setting('LOGIN_ENABLE_SSO', True)
        # Should not raise - the default super() implementation is a no-op
        self.adapter.pre_social_login(None, None)

    def test_is_auto_signup_allowed(self):
        """Auto-signup must be blockable independently of whether SSO registration is open."""
        InvenTreeSetting.set_setting('LOGIN_SIGNUP_SSO_AUTO', False)
        self.assertFalse(self.adapter.is_auto_signup_allowed(None, None))

        # When enabled, defers to allauth's own default (SOCIALACCOUNT_AUTO_SIGNUP)
        InvenTreeSetting.set_setting('LOGIN_SIGNUP_SSO_AUTO', True)
        self.assertTrue(self.adapter.is_auto_signup_allowed(None, None))

    def test_is_open_for_signup(self):
        """SSO self-registration is gated by LOGIN_ENABLE_SSO_REG (and a configured mail backend)."""
        InvenTreeSetting.set_setting('LOGIN_ENABLE_SSO_REG', False)
        self.assertFalse(self.adapter.is_open_for_signup(None, None))

        with self.settings(EMAIL_HOST='localhost', TESTING_BYPASS_MAILCHECK=True):
            InvenTreeSetting.set_setting('LOGIN_ENABLE_SSO_REG', True)
            self.assertTrue(self.adapter.is_open_for_signup(None, None))

    def test_get_connect_redirect_url(self):
        """Connecting an SSO account should redirect back to the frontend root."""
        request = RequestFactory().get('/')
        url = self.adapter.get_connect_redirect_url(request, None)
        self.assertTrue(url.endswith(f'/{django_settings.FRONTEND_URL_BASE}/'))

    def test_authentication_error_does_not_raise(self):
        """A provider-side authentication error should be logged, not raised further."""
        request = RequestFactory().get(
            '/', data={'error': 'access_denied', 'error_description': 'Cancelled'}
        )
        # Should not raise, regardless of whether error/exception are passed explicitly
        self.adapter.authentication_error(request, 'mock')
        self.adapter.authentication_error(
            request, 'mock', error='denied', exception='User cancelled'
        )


class EmailSettingsContext:
    """Context manager to enable email settings for tests."""

    def __enter__(self):
        """Enable stuff."""
        InvenTreeSetting.set_setting('LOGIN_ENABLE_REG', True)

    def __exit__(self, type, value, traceback):
        """Exit stuff."""
        InvenTreeSetting.set_setting('LOGIN_ENABLE_REG', False)


class TestAuth(InvenTreeAPITestCase):
    """Test authentication functionality."""

    reg_url = '/api/auth/v1/auth/signup'
    login_url = '/api/auth/v1/auth/login'
    test_email = 'tester@example.com'

    def test_buildin_token(self):
        """Test the built-in token authentication."""
        self.logout()

        response = self.post(
            self.login_url,
            {'username': self.username, 'password': self.password},
            expected_code=200,
        )
        data = response.json()
        self.assertIn('meta', data)
        self.assertTrue(data['meta']['is_authenticated'])

        # Test for conflicting login
        self.post(
            self.login_url,
            {'username': self.username, 'password': self.password},
            expected_code=409,
        )

    def email_args(self, user=None, email=None):
        """Generate registration arguments."""
        return {
            'username': user or 'user2',
            'email': email or self.test_email,
            'password': '#asdf1234',
        }

    def test_registration(self):
        """Test the registration process."""
        self.logout()

        # Duplicate username
        resp = self.post(
            self.reg_url, self.email_args(user='testuser'), expected_code=400
        )
        self.assertIn('A user with that username already exists.', str(resp.json()))

        # Registration is disabled
        self.post(self.reg_url, self.email_args(), expected_code=403)

        # Enable registration - now it should work
        with (
            self.settings(EMAIL_HOST='localhost', TESTING_BYPASS_MAILCHECK=True) as _,
            EmailSettingsContext() as _,
        ):
            resp = self.post(self.reg_url, self.email_args(), expected_code=200)
            self.assertEqual(resp.json()['data']['user']['email'], self.test_email)

    def test_registration_email(self):
        """Test that LOGIN_SIGNUP_MAIL_RESTRICTION works."""
        self.logout()

        # Check the setting validation is working
        with self.assertRaises(ValidationError):
            InvenTreeSetting.set_setting(
                'LOGIN_SIGNUP_MAIL_RESTRICTION', 'example.com,inventree.org'
            )

        # Setting setting correctly
        correct_setting = '@example.com,@inventree.org'
        InvenTreeSetting.set_setting('LOGIN_SIGNUP_MAIL_RESTRICTION', correct_setting)
        self.assertEqual(
            InvenTreeSetting.get_setting('LOGIN_SIGNUP_MAIL_RESTRICTION'),
            correct_setting,
        )

        # Wrong email format
        resp = self.post(
            self.reg_url,
            self.email_args(email='admin@invenhost.com'),
            expected_code=400,
        )
        self.assertIn('The provided email domain is not approved.', str(resp.json()))

        # Right format should work
        with (
            self.settings(EMAIL_HOST='localhost', TESTING_BYPASS_MAILCHECK=True) as _,
            EmailSettingsContext() as _,
        ):
            resp = self.post(self.reg_url, self.email_args(), expected_code=200)
            self.assertEqual(resp.json()['data']['user']['email'], self.test_email)

    def test_auth_request(self):
        """Test the auth_request view."""
        url = reverse('auth-check')

        # Logged in user
        self.get(url)

        # Inactive user
        # TODO @matmair - this part of auth_request is not triggering currently
        # self.user.is_active = False
        # self.user.save()
        # self.get(url, expected_code=403)
        # self.user.is_active = True
        # self.user.save()

        # Logged out user
        self.client.logout()
        self.get(url, expected_code=401)

    def test_server_info_sso_enabled(self):
        """The server info endpoint should reflect the LOGIN_ENABLE_SSO setting."""
        url = reverse('api-inventree-info')

        InvenTreeSetting.set_setting('LOGIN_ENABLE_SSO', True)
        resp = self.get(url, expected_code=200)
        self.assertTrue(resp.json()['settings']['sso_enabled'])

        InvenTreeSetting.set_setting('LOGIN_ENABLE_SSO', False)
        resp = self.get(url, expected_code=200)
        self.assertFalse(resp.json()['settings']['sso_enabled'])
