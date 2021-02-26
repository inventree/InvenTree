""" Low level tests for the InvenTree API """

from rest_framework import status

from django.urls import reverse

from InvenTree.api_tester import InvenTreeAPITestCase

from users.models import RuleSet

from base64 import b64encode


class APITests(InvenTreeAPITestCase):
    """ Tests for the InvenTree API """

    fixtures = [
        'location',
        'stock',
        'part',
        'category',
    ]

    token = None

    auto_login = False

    def setUp(self):

        super().setUp()

    def basicAuth(self):
        # Use basic authentication

        authstring = bytes("{u}:{p}".format(u=self.username, p=self.password), "ascii")

        # Use "basic" auth by default
        auth = b64encode(authstring).decode("ascii")
        self.client.credentials(HTTP_AUTHORIZATION="Basic {auth}".format(auth=auth))

    def tokenAuth(self):

        self.basicAuth()
        token_url = reverse('api-token')
        response = self.client.get(token_url, format='json', data={})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)

        token = response.data['token']
        self.token = token

    def token_failure(self):
        # Test token endpoint without basic auth
        url = reverse('api-token')
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIsNone(self.token)

    def token_success(self):

        self.tokenAuth()
        self.assertIsNotNone(self.token)

    def test_info_view(self):
        """
        Test that we can read the 'info-view' endpoint.
        """

        url = reverse('api-inventree-info')

        response = self.client.get(url, format='json')

        data = response.json()
        self.assertIn('server', data)
        self.assertIn('version', data)
        self.assertIn('instance', data)

        self.assertEquals('InvenTree', data['server'])

    def test_role_view(self):
        """
        Test that we can access the 'roles' view for the logged in user.

        Also tests that it is *not* accessible if the client is not logged in.
        """

        url = reverse('api-user-roles')

        response = self.client.get(url, format='json')

        # Not logged in, so cannot access user role data
        self.assertTrue(response.status_code in [401, 403])

        # Now log in!
        self.basicAuth()

        response = self.get(url)

        data = response.data

        self.assertIn('user', data)
        self.assertIn('username', data)
        self.assertIn('is_staff', data)
        self.assertIn('is_superuser', data)
        self.assertIn('roles', data)

        roles = data['roles']

        role_names = roles.keys()

        # By default, 'view' permissions are provided
        for rule in RuleSet.RULESET_NAMES:
            self.assertIn(rule, role_names)

            self.assertIn('view', roles[rule])

            self.assertNotIn('add', roles[rule])
            self.assertNotIn('change', roles[rule])
            self.assertNotIn('delete', roles[rule])
    
    def test_with_superuser(self):
        """
        Superuser should have *all* roles assigned
        """

        self.user.is_superuser = True
        self.user.save()

        self.basicAuth()

        response = self.get(reverse('api-user-roles'))

        roles = response.data['roles']

        for rule in RuleSet.RULESET_NAMES:
            self.assertIn(rule, roles.keys())

            for perm in ['view', 'add', 'change', 'delete']:
                self.assertIn(perm, roles[rule])

    def test_with_roles(self):
        """
        Assign some roles to the user
        """

        self.basicAuth()
        response = self.get(reverse('api-user-roles'))

        self.assignRole('part.delete')
        self.assignRole('build.change')
        response = self.get(reverse('api-user-roles'))

        roles = response.data['roles']

        # New role permissions should have been added now
        self.assertIn('delete', roles['part'])
        self.assertIn('change', roles['build'])
