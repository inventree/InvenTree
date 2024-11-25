"""Test the sso module functionality."""

from django.contrib.auth.models import Group, User
from django.test import override_settings
from django.test.testcases import TransactionTestCase

from allauth.socialaccount.models import SocialAccount, SocialLogin

from common.models import InvenTreeSetting
from InvenTree import sso
from InvenTree.forms import RegistratonMixin


class Dummy:
    """Simulate super class of RegistratonMixin."""

    def save_user(self, _request, user: User, *args) -> User:
        """This method is only used that the super() call of RegistrationMixin does not fail."""
        return user


class MockRegistrationMixin(RegistratonMixin, Dummy):
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
