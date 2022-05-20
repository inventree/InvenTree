from django.apps import apps
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from rest_framework.authtoken.models import Token

from users.models import Owner, RuleSet


class RuleSetModelTest(TestCase):
    """
    Some simplistic tests to ensure the RuleSet model is setup correctly.
    """

    def test_ruleset_models(self):

        keys = RuleSet.RULESET_MODELS.keys()

        # Check if there are any rulesets which do not have models defined

        missing = [name for name in RuleSet.RULESET_NAMES if name not in keys]

        if len(missing) > 0:  # pragma: no cover
            print("The following rulesets do not have models assigned:")
            for m in missing:
                print("-", m)

        # Check if models have been defined for a ruleset which is incorrect
        extra = [name for name in keys if name not in RuleSet.RULESET_NAMES]

        if len(extra) > 0:  # pragma: no cover
            print("The following rulesets have been improperly added to RULESET_MODELS:")
            for e in extra:
                print("-", e)

        # Check that each ruleset has models assigned
        empty = [key for key in keys if len(RuleSet.RULESET_MODELS[key]) == 0]

        if len(empty) > 0:  # pragma: no cover
            print("The following rulesets have empty entries in RULESET_MODELS:")
            for e in empty:
                print("-", e)

        self.assertEqual(len(missing), 0)
        self.assertEqual(len(extra), 0)
        self.assertEqual(len(empty), 0)

    def test_model_names(self):
        """
        Test that each model defined in the rulesets is valid,
        based on the database schema!
        """

        available_models = apps.get_models()

        available_tables = set()

        # Extract each available database model and construct a formatted string
        for model in available_models:
            label = model.objects.model._meta.label
            label = label.replace('.', '_').lower()
            available_tables.add(label)

        assigned_models = set()

        # Now check that each defined model is a valid table name
        for key in RuleSet.RULESET_MODELS.keys():

            models = RuleSet.RULESET_MODELS[key]

            for m in models:

                assigned_models.add(m)

        missing_models = set()

        for model in available_tables:
            if model not in assigned_models and model not in RuleSet.RULESET_IGNORE:  # pragma: no cover
                missing_models.add(model)

        if len(missing_models) > 0:  # pragma: no cover
            print("The following database models are not covered by the defined RuleSet permissions:")
            for m in missing_models:
                print("-", m)

        extra_models = set()

        defined_models = set()

        for model in assigned_models:
            defined_models.add(model)

        for model in RuleSet.RULESET_IGNORE:
            defined_models.add(model)

        for model in defined_models:  # pragma: no cover
            if model not in available_tables:
                extra_models.add(model)

        if len(extra_models) > 0:  # pragma: no cover
            print("The following RuleSet permissions do not match a database model:")
            for m in extra_models:
                print("-", m)

        self.assertEqual(len(missing_models), 0)
        self.assertEqual(len(extra_models), 0)

    def test_permission_assign(self):
        """
        Test that the permission assigning works!
        """

        # Create a new group
        group = Group.objects.create(name="Test group")

        rulesets = group.rule_sets.all()

        # Rulesets should have been created automatically for this group
        self.assertEqual(rulesets.count(), len(RuleSet.RULESET_CHOICES))

        # Check that all permissions have been assigned permissions?
        permission_set = set()

        for models in RuleSet.RULESET_MODELS.values():

            for model in models:
                permission_set.add(model)

        # Every ruleset by default sets one permission, the "view" permission set
        self.assertEqual(group.permissions.count(), len(permission_set))

        # Add some more rules
        for rule in rulesets:
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


class OwnerModelTest(TestCase):
    """
    Some simplistic tests to ensure the Owner model is setup correctly.
    """

    def setUp(self):
        """ Add users and groups """

        # Create a new user
        self.user = get_user_model().objects.create_user('username', 'user@email.com', 'password')
        # Put the user into a new group
        self.group = Group.objects.create(name='new_group')
        self.user.groups.add(self.group)

    def do_request(self, endpoint, filters, status_code=200):
        response = self.client.get(endpoint, filters, format='json')
        self.assertEqual(response.status_code, status_code)
        return response.data

    def test_owner(self):

        # Check that owner was created for user
        user_as_owner = Owner.get_owner(self.user)
        self.assertEqual(type(user_as_owner), Owner)

        # Check that owner was created for group
        group_as_owner = Owner.get_owner(self.group)
        self.assertEqual(type(group_as_owner), Owner)

        # Get related owners (user + group)
        related_owners = group_as_owner.get_related_owners(include_group=True)
        self.assertTrue(user_as_owner in related_owners)
        self.assertTrue(group_as_owner in related_owners)

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
        """
        Test user APIs
        """
        # not authed
        self.do_request(reverse('api-owner-list'), {}, 401)
        self.do_request(reverse('api-owner-detail', kwargs={'pk': self.user.id}), {}, 401)

        self.client.login(username='username', password='password')
        # user list
        self.do_request(reverse('api-owner-list'), {})
        # user list with search
        self.do_request(reverse('api-owner-list'), {'search': 'user'})
        # user detail
        # TODO fix this test
        # self.do_request(reverse('api-owner-detail', kwargs={'pk': self.user.id}), {})

    def test_token(self):
        """
        Test token mechanisms
        """
        token = Token.objects.filter(user=self.user)

        # not authed
        self.do_request(reverse('api-token'), {}, 401)

        self.client.login(username='username', password='password')
        # token get
        response = self.do_request(reverse('api-token'), {})
        self.assertEqual(response['token'], token.first().key)

        # token delete
        response = self.client.delete(reverse('api-token'), {}, format='json')
        self.assertEqual(response.status_code, 202)
        self.assertEqual(len(token), 0)

        # token second delete
        response = self.client.delete(reverse('api-token'), {}, format='json')
        self.assertEqual(response.status_code, 400)
