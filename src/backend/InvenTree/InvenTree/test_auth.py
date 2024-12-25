"""Test the sso and auth module functionality."""

from django.conf import settings
from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.test import override_settings
from django.test.testcases import TransactionTestCase

from allauth.socialaccount.models import SocialAccount, SocialLogin

from common.models import InvenTreeSetting
from InvenTree import sso
from InvenTree.auth_overrides import RegistrationMixin
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
        extra_data = {'groups': ['idp_group']}
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


class EmailSettingsContext:
    """Context manager to enable email settings for tests."""

    def __enter__(self):
        """Enable stuff."""
        InvenTreeSetting.set_setting('LOGIN_ENABLE_REG', True)
        settings.EMAIL_HOST = 'localhost'

    def __exit__(self, type, value, traceback):
        """Exit stuff."""
        InvenTreeSetting.set_setting('LOGIN_ENABLE_REG', False)
        settings.EMAIL_HOST = ''


class TestAuth(InvenTreeAPITestCase):
    """Test authentication functionality."""

    def email_args(self, user=None, email=None):
        """Generate registration arguments."""
        return {
            'username': user or 'user1',
            'email': email or 'test@example.com',
            'password1': '#asdf1234',
            'password2': '#asdf1234',
        }

    def test_registration(self):
        """Test the registration process."""
        self.logout()

        # Duplicate username
        resp = self.post(
            '/api/auth/registration/',
            self.email_args(user='testuser'),
            expected_code=400,
        )
        self.assertIn(
            'A user with that username already exists.', resp.data['username']
        )

        # Registration is disabled
        resp = self.post(
            '/api/auth/registration/', self.email_args(), expected_code=400
        )
        self.assertIn('Registration is disabled.', resp.data['non_field_errors'])

        # Enable registration - now it should work
        with EmailSettingsContext():
            resp = self.post(
                '/api/auth/registration/', self.email_args(), expected_code=201
            )
            self.assertIn('key', resp.data)

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
            '/api/auth/registration/',
            self.email_args(email='admin@invenhost.com'),
            expected_code=400,
        )
        self.assertIn('The provided email domain is not approved.', resp.data['email'])

        # Right format should work
        with EmailSettingsContext():
            resp = self.post(
                '/api/auth/registration/', self.email_args(), expected_code=201
            )
            self.assertIn('key', resp.data)
