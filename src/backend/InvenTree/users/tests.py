"""Unit tests for the 'users' app."""

from django.apps import apps
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from common.settings import set_global_setting
from InvenTree.unit_test import AdminTestCase, InvenTreeAPITestCase, InvenTreeTestCase
from users.models import ApiToken, Owner, RuleSet


class RuleSetModelTest(TestCase):
    """Some simplistic tests to ensure the RuleSet model is setup correctly."""

    def test_ruleset_models(self):
        """Test that the role rulesets work as intended."""
        keys = RuleSet.get_ruleset_models().keys()

        # Check if there are any rulesets which do not have models defined

        missing = [name for name in RuleSet.RULESET_NAMES if name not in keys]

        if len(missing) > 0:  # pragma: no cover
            print('The following rulesets do not have models assigned:')
            for m in missing:
                print('-', m)

        # Check if models have been defined for a ruleset which is incorrect
        extra = [name for name in keys if name not in RuleSet.RULESET_NAMES]

        if len(extra) > 0:  # pragma: no cover
            print(
                'The following rulesets have been improperly added to get_ruleset_models():'
            )
            for e in extra:
                print('-', e)

        # Check that each ruleset has models assigned
        empty = [key for key in keys if len(RuleSet.get_ruleset_models()[key]) == 0]

        if len(empty) > 0:  # pragma: no cover
            print('The following rulesets have empty entries in get_ruleset_models():')
            for e in empty:
                print('-', e)

        self.assertEqual(len(missing), 0)
        self.assertEqual(len(extra), 0)
        self.assertEqual(len(empty), 0)

    def test_model_names(self):
        """Test that each model defined in the rulesets is valid, based on the database schema!"""
        available_models = apps.get_models()

        available_tables = set()

        # Extract each available database model and construct a formatted string
        for model in available_models:
            label = model.objects.model._meta.label
            label = label.replace('.', '_').lower()
            available_tables.add(label)

        assigned_models = set()

        # Now check that each defined model is a valid table name
        for key in RuleSet.get_ruleset_models():
            models = RuleSet.get_ruleset_models()[key]

            for m in models:
                assigned_models.add(m)

        missing_models = set()

        for model in available_tables:
            if (
                model not in assigned_models
                and model not in RuleSet.get_ruleset_ignore()
            ):  # pragma: no cover
                missing_models.add(model)

        if len(missing_models) > 0:  # pragma: no cover
            print(
                'The following database models are not covered by the defined RuleSet permissions:'
            )
            for m in missing_models:
                print('-', m)

        extra_models = set()

        defined_models = set()

        for model in assigned_models:
            defined_models.add(model)

        for model in RuleSet.get_ruleset_ignore():
            defined_models.add(model)

        for model in defined_models:  # pragma: no cover
            if model not in available_tables:
                extra_models.add(model)

        if len(extra_models) > 0:  # pragma: no cover
            print('The following RuleSet permissions do not match a database model:')
            for m in extra_models:
                print('-', m)

        self.assertEqual(len(missing_models), 0)
        self.assertEqual(len(extra_models), 0)

    def test_permission_assign(self):
        """Test that the permission assigning works!"""
        # Create a new group
        group = Group.objects.create(name='Test group')

        rulesets = group.rule_sets.all()

        # Rulesets should have been created automatically for this group
        self.assertEqual(rulesets.count(), len(RuleSet.RULESET_CHOICES))

        # Check that all permissions have been assigned permissions?
        permission_set = set()

        for models in RuleSet.get_ruleset_models().values():
            for model in models:
                permission_set.add(model)

        # By default no permissions should be assigned
        self.assertEqual(group.permissions.count(), 0)

        # Add some more rules
        for rule in rulesets:
            rule.can_view = True
            rule.can_add = True
            rule.can_change = True

            rule.save()

        # update_fields is required to trigger permissions update
        group.save(update_fields=['name'])

        # There should now be three permissions for each rule set
        self.assertEqual(group.permissions.count(), 3 * len(permission_set))

        # Now remove *all* permissions
        for rule in rulesets:
            rule.can_view = False
            rule.can_add = False
            rule.can_change = False
            rule.can_delete = False

            rule.save()

        # update_fields is required to trigger permissions update
        group.save(update_fields=['name'])

        # There should now not be any permissions assigned to this group
        self.assertEqual(group.permissions.count(), 0)


class OwnerModelTest(InvenTreeTestCase):
    """Some simplistic tests to ensure the Owner model is setup correctly."""

    def do_request(self, endpoint, filters, status_code=200):
        """Perform an API request."""
        response = self.client.get(endpoint, filters, format='json')
        self.assertEqual(response.status_code, status_code)
        return response.data

    def test_owner(self):
        """Tests for the 'owner' model."""
        # Check that owner was created for user
        user_as_owner = Owner.get_owner(self.user)
        self.assertEqual(type(user_as_owner), Owner)

        # Check that owner was created for group
        group_as_owner = Owner.get_owner(self.group)
        self.assertEqual(type(group_as_owner), Owner)

        # Check name
        self.assertEqual(str(user_as_owner), 'testuser (user)')

        # Get related owners (user + group)
        related_owners = group_as_owner.get_related_owners(include_group=True)
        self.assertIn(user_as_owner, related_owners)
        self.assertIn(group_as_owner, related_owners)

        # Get related owners (only user)
        related_owners = group_as_owner.get_related_owners(include_group=False)
        self.assertIn(user_as_owner, related_owners)
        self.assertNotIn(group_as_owner, related_owners)

        # Get related owners on user
        related_owners = user_as_owner.get_related_owners()
        self.assertEqual(related_owners, [user_as_owner])

        # Check owner matching
        owners = Owner.get_owners_matching_user(self.user)
        self.assertEqual(owners, [user_as_owner, group_as_owner])

        # Delete user and verify owner was deleted too
        self.user.delete()
        user_as_owner = Owner.get_owner(self.user)
        self.assertEqual(user_as_owner, None)

        # Delete group and verify owner was deleted too
        self.group.delete()
        group_as_owner = Owner.get_owner(self.group)
        self.assertEqual(group_as_owner, None)

    def test_api(self):
        """Test user APIs."""
        self.client.logout()

        # not authed
        self.do_request(reverse('api-owner-list'), {}, 401)
        self.do_request(
            reverse('api-owner-detail', kwargs={'pk': self.user.id}), {}, 401
        )

        self.client.login(username=self.username, password=self.password)
        # user list
        self.do_request(reverse('api-owner-list'), {})

        # user list with 'is_active' filter
        self.do_request(reverse('api-owner-list'), {'is_active': False})

        # user list with search
        self.do_request(reverse('api-owner-list'), {'search': 'user'})

        # # owner detail - user
        # response = self.do_request(reverse('api-owner-detail', kwargs={'pk': 1}), {})
        # self.assertEqual(response['name'], self.username)
        # self.assertEqual(response['label'], 'user')
        # self.assertEqual(response['owner_id'], self.user.id)

        # # owner detail - group
        # group = self.user.groups.first()
        # response = self.do_request(reverse('api-owner-detail', kwargs={'pk': 2}), {})
        # self.assertEqual(response['name'], group.name)
        # self.assertEqual(response['label'], 'group')
        # self.assertEqual(response['owner_id'], group.pk)

        # own user detail
        response_detail = self.do_request(
            reverse('api-user-detail', kwargs={'pk': self.user.id}), {}, 200
        )
        self.assertEqual(response_detail['username'], self.username)

        response_me = self.do_request(reverse('api-user-me'), {}, 200)
        self.assertEqual(response_detail, response_me)

    def test_token(self):
        """Test token mechanisms."""
        self.client.logout()

        token = ApiToken.objects.filter(user=self.user)

        # not authed
        self.do_request(reverse('api-token'), {}, 401)

        self.client.login(username=self.username, password=self.password)
        # token get
        response = self.do_request(reverse('api-token'), {})
        self.assertEqual(response['token'], token.first().key)

        # test user is associated with token
        response = self.do_request(
            reverse('api-user-me'), {'name': 'another-token'}, 200
        )
        self.assertEqual(response['username'], self.username)

    def test_display_name(self):
        """Test the display name for the owner."""
        owner = Owner.get_owner(self.user)
        self.assertEqual(owner.name(), 'testuser')
        self.assertEqual(str(owner), 'testuser (user)')

        # Change setting
        set_global_setting('DISPLAY_FULL_NAMES', True)
        self.user.first_name = 'first'
        self.user.last_name = 'last'
        self.user.save()
        owner = Owner.get_owner(self.user)

        # Now first / last should be used
        self.assertEqual(owner.name(), 'first last')
        self.assertEqual(str(owner), 'first last (user)')

        # Reset
        set_global_setting('DISPLAY_FULL_NAMES', False)
        self.user.first_name = ''
        self.user.last_name = ''
        self.user.save()


class MFALoginTest(InvenTreeAPITestCase):
    """Some simplistic tests to ensure that MFA is working."""

    def test_api(self):
        """Test that the API is working."""
        auth_data = {'username': self.username, 'password': self.password}
        login_url = reverse('api-login')

        # Normal login
        response = self.post(login_url, auth_data, expected_code=200)
        self.assertIn('key', response.data)
        self.client.logout()

        # Add MFA
        totp_model = self.user.totpdevice_set.create()

        # Login with MFA enabled but not provided
        response = self.post(login_url, auth_data, expected_code=403)
        self.assertContains(response, 'MFA required for this user', status_code=403)

        # Login with MFA enabled and provided - should redirect to MFA page
        auth_data['mfa'] = 'anything'
        response = self.post(login_url, auth_data, expected_code=302)
        self.assertEqual(response.url, reverse('two-factor-authenticate'))
        # MFA not finished - no access allowed
        self.get(reverse('api-token'), expected_code=401)

        # Login with MFA enabled and provided - but incorrect pwd
        auth_data['password'] = 'wrong'
        self.post(login_url, auth_data, expected_code=401)
        auth_data['password'] = self.password

        # Remove MFA
        totp_model.delete()

        # Login with MFA disabled but correct credentials provided
        response = self.post(login_url, auth_data, expected_code=200)
        self.assertIn('key', response.data)

        # Wrong login should not work
        auth_data['password'] = 'wrong'
        self.post(login_url, auth_data, expected_code=401)


class AdminTest(AdminTestCase):
    """Tests for the admin interface integration."""

    def test_admin(self):
        """Test the admin URL."""
        my_token = self.helper(
            model=ApiToken, model_kwargs={'user': self.user, 'name': 'test-token'}
        )
        # Additionally test str fnc
        self.assertEqual(str(my_token), my_token.token)
