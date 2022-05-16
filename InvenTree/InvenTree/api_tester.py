"""
Helper functions for performing API unit tests
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APITestCase


class InvenTreeAPITestCase(APITestCase):
    """
    Base class for running InvenTree API tests
    """

    # User information
    username = 'testuser'
    password = 'mypassword'
    email = 'test@testing.com'

    superuser = False
    is_staff = True
    auto_login = True

    # Set list of roles automatically associated with the user
    roles = []

    def setUp(self):

        super().setUp()

        # Create a user to log in with
        self.user = get_user_model().objects.create_user(
            username=self.username,
            password=self.password,
            email=self.email
        )

        # Create a group for the user
        self.group = Group.objects.create(name='my_test_group')
        self.user.groups.add(self.group)

        if self.superuser:
            self.user.is_superuser = True

        if self.is_staff:
            self.user.is_staff = True

        self.user.save()

        for role in self.roles:
            self.assignRole(role)

        if self.auto_login:
            self.client.login(username=self.username, password=self.password)

    def assignRole(self, role):
        """
        Set the user roles for the registered user
        """

        # role is of the format 'rule.permission' e.g. 'part.add'

        rule, perm = role.split('.')

        for ruleset in self.group.rule_sets.all():

            if ruleset.name == rule:

                if perm == 'view':
                    ruleset.can_view = True
                elif perm == 'change':
                    ruleset.can_change = True
                elif perm == 'delete':
                    ruleset.can_delete = True
                elif perm == 'add':
                    ruleset.can_add = True

                ruleset.save()
                break

    def getActions(self, url):
        """
        Return a dict of the 'actions' available at a given endpoint.
        Makes use of the HTTP 'OPTIONS' method to request this.
        """

        response = self.client.options(url)
        self.assertEqual(response.status_code, 200)

        actions = response.data.get('actions', None)

        if not actions:
            actions = {}

        return actions

    def get(self, url, data={}, expected_code=200):
        """
        Issue a GET request
        """

        response = self.client.get(url, data, format='json')

        if expected_code is not None:
            self.assertEqual(response.status_code, expected_code)

        return response

    def post(self, url, data, expected_code=None, format='json'):
        """
        Issue a POST request
        """

        response = self.client.post(url, data=data, format=format)

        if expected_code is not None:
            self.assertEqual(response.status_code, expected_code)

        return response

    def delete(self, url, expected_code=None):
        """
        Issue a DELETE request
        """

        response = self.client.delete(url)

        if expected_code is not None:
            self.assertEqual(response.status_code, expected_code)

        return response

    def patch(self, url, data, expected_code=None, format='json'):
        """
        Issue a PATCH request
        """

        response = self.client.patch(url, data=data, format=format)

        if expected_code is not None:
            self.assertEqual(response.status_code, expected_code)

        return response

    def put(self, url, data, expected_code=None, format='json'):
        """
        Issue a PUT request
        """

        response = self.client.put(url, data=data, format=format)

        if expected_code is not None:
            self.assertEqual(response.status_code, expected_code)

        return response

    def options(self, url, expected_code=None):
        """
        Issue an OPTIONS request
        """

        response = self.client.options(url, format='json')

        if expected_code is not None:
            self.assertEqual(response.status_code, expected_code)

        return response
