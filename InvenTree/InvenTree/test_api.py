"""Low level tests for the InvenTree API."""

from base64 import b64encode

from django.urls import reverse

from rest_framework import status

from InvenTree.unit_test import InvenTreeAPITestCase, InvenTreeTestCase
from users.models import RuleSet, update_group_roles


class HTMLAPITests(InvenTreeTestCase):
    """Test that we can access the REST API endpoints via the HTML interface.

    History: Discovered on 2021-06-28 a bug in InvenTreeModelSerializer,
    which raised an AssertionError when using the HTML API interface,
    while the regular JSON interface continued to work as expected.
    """
    roles = 'all'

    def test_part_api(self):
        """Test that part list is working."""
        url = reverse('api-part-list')

        # Check JSON response
        response = self.client.get(url, HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, 200)

    def test_build_api(self):
        """Test that build list is working."""
        url = reverse('api-build-list')

        # Check JSON response
        response = self.client.get(url, HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, 200)

    def test_stock_api(self):
        """Test that stock list is working."""
        url = reverse('api-stock-list')

        # Check JSON response
        response = self.client.get(url, HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, 200)

    def test_company_list(self):
        """Test that company list is working."""
        url = reverse('api-company-list')

        # Check JSON response
        response = self.client.get(url, HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, 200)

    def test_not_found(self):
        """Test that the NotFoundView is working."""
        response = self.client.get('/api/anc')
        self.assertEqual(response.status_code, 404)


class APITests(InvenTreeAPITestCase):
    """Tests for the InvenTree API."""

    fixtures = [
        'location',
        'category',
        'part',
        'stock'
    ]
    token = None
    auto_login = False

    def basicAuth(self):
        """Helper function to use basic auth."""
        # Use basic authentication

        authstring = bytes("{u}:{p}".format(u=self.username, p=self.password), "ascii")

        # Use "basic" auth by default
        auth = b64encode(authstring).decode("ascii")
        self.client.credentials(HTTP_AUTHORIZATION="Basic {auth}".format(auth=auth))

    def tokenAuth(self):
        """Helper function to use token auth."""
        self.basicAuth()
        token_url = reverse('api-token')
        response = self.client.get(token_url, format='json', data={})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)

        token = response.data['token']
        self.token = token

    def test_token_failure(self):
        """Test token resolve endpoint does not work without basic auth."""
        # Test token endpoint without basic auth
        url = reverse('api-token')
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIsNone(self.token)

    def test_token_success(self):
        """Test token auth works."""
        self.tokenAuth()
        self.assertIsNotNone(self.token)

    def test_info_view(self):
        """Test that we can read the 'info-view' endpoint."""
        url = reverse('api-inventree-info')

        response = self.client.get(url, format='json')

        data = response.json()
        self.assertIn('server', data)
        self.assertIn('version', data)
        self.assertIn('instance', data)

        self.assertEqual('InvenTree', data['server'])

    def test_role_view(self):
        """Test that we can access the 'roles' view for the logged in user.

        Also tests that it is *not* accessible if the client is not logged in.
        """
        url = reverse('api-user-roles')

        # Delete all rules
        self.group.rule_sets.all().delete()
        update_group_roles(self.group)

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
        """Superuser should have *all* roles assigned."""
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
        """Assign some roles to the user."""
        self.basicAuth()

        url = reverse('api-user-roles')

        response = self.get(url)

        self.assignRole('part.delete')
        self.assignRole('build.change')

        response = self.get(url)

        roles = response.data['roles']

        # New role permissions should have been added now
        self.assertIn('delete', roles['part'])
        self.assertIn('change', roles['build'])

    def test_list_endpoint_actions(self):
        """Tests for the OPTIONS method for API endpoints."""
        self.basicAuth()

        # Without any 'part' permissions, we should not see any available actions
        url = reverse('api-part-list')

        actions = self.getActions(url)

        # Even without permissions, GET action is available
        self.assertEqual(len(actions), 1)

        # Assign a new role
        self.assignRole('part.view')
        actions = self.getActions(url)

        # As we don't have "add" permission, there should be only the GET API action
        self.assertEqual(len(actions), 1)

        # But let's make things interesting...
        # Why don't we treat ourselves to some "add" permissions
        self.assignRole('part.add')

        actions = self.getActions(url)

        self.assertEqual(len(actions), 2)
        self.assertIn('POST', actions)
        self.assertIn('GET', actions)

    def test_detail_endpoint_actions(self):
        """Tests for detail API endpoint actions."""
        self.basicAuth()

        url = reverse('api-part-detail', kwargs={'pk': 1})

        actions = self.getActions(url)

        # No actions, as we do not have any permissions!
        self.assertEqual(len(actions), 1)
        self.assertIn('GET', actions.keys())

        # Add a 'add' permission
        # Note: 'add' permission automatically implies 'change' also
        self.assignRole('part.add')

        actions = self.getActions(url)

        self.assertEqual(len(actions), 2)
        self.assertIn('PUT', actions.keys())
        self.assertIn('GET', actions.keys())

        # Add some other permissions
        self.assignRole('part.change')
        self.assignRole('part.delete')

        actions = self.getActions(url)

        self.assertEqual(len(actions), 3)
        self.assertIn('GET', actions.keys())
        self.assertIn('PUT', actions.keys())
        self.assertIn('DELETE', actions.keys())


class BulkDeleteTests(InvenTreeAPITestCase):
    """Unit tests for the BulkDelete endpoints"""

    superuser = True

    def test_errors(self):
        """Test that the correct errors are thrown"""
        url = reverse('api-stock-test-result-list')

        # DELETE without any of the required fields
        response = self.delete(
            url,
            {},
            expected_code=400
        )

        self.assertIn('List of items or filters must be provided for bulk deletion', str(response.data))

        # DELETE with invalid 'items'
        response = self.delete(
            url,
            {
                'items': {"hello": "world"},
            },
            expected_code=400,
        )

        self.assertIn("'items' must be supplied as a list object", str(response.data))

        # DELETE with invalid 'filters'
        response = self.delete(
            url,
            {
                'filters': [1, 2, 3],
            },
            expected_code=400,
        )

        self.assertIn("'filters' must be supplied as a dict object", str(response.data))


class SearchTests(InvenTreeAPITestCase):
    """Unit tests for global search endpoint"""

    fixtures = [
        'category',
        'part',
        'company',
        'location',
        'supplier_part',
        'stock',
        'order',
        'sales_order',
    ]

    def test_empty(self):
        """Test empty request"""
        data = [
            '',
            None,
            {},
        ]

        for d in data:
            response = self.post(reverse('api-search'), d, expected_code=400)
            self.assertIn('Search term must be provided', str(response.data))

    def test_results(self):
        """Test individual result types"""
        response = self.post(
            reverse('api-search'),
            {
                'search': 'chair',
                'limit': 3,
                'part': {},
                'build': {},
            },
            expected_code=200
        )

        # No build results
        self.assertEqual(response.data['build']['count'], 0)

        # 3 (of 5) part results
        self.assertEqual(response.data['part']['count'], 5)
        self.assertEqual(len(response.data['part']['results']), 3)

        # Other results not included
        self.assertNotIn('purchaseorder', response.data)
        self.assertNotIn('salesorder', response.data)

        # Search for orders
        response = self.post(
            reverse('api-search'),
            {
                'search': '01',
                'limit': 2,
                'purchaseorder': {},
                'salesorder': {},
            },
            expected_code=200,
        )

        self.assertEqual(response.data['purchaseorder']['count'], 1)
        self.assertEqual(response.data['salesorder']['count'], 0)

        self.assertNotIn('stockitem', response.data)
        self.assertNotIn('build', response.data)

    def test_permissions(self):
        """Test that users with insufficient permissions are handled correctly"""
        # First, remove all roles
        for ruleset in self.group.rule_sets.all():
            ruleset.can_view = False
            ruleset.can_change = False
            ruleset.can_delete = False
            ruleset.can_add = False
            ruleset.save()

        models = [
            'build',
            'company',
            'manufacturerpart',
            'supplierpart',
            'part',
            'partcategory',
            'purchaseorder',
            'stockitem',
            'stocklocation',
            'salesorder',
        ]

        query = {
            'search': 'c',
            'limit': 3,
        }

        for mdl in models:
            query[mdl] = {}

        response = self.post(
            reverse('api-search'),
            query,
            expected_code=200
        )

        # Check for 'permission denied' error
        for mdl in models:
            self.assertEqual(response.data[mdl]['error'], 'User does not have permission to view this model')

        # Assign view roles for some parts
        self.assignRole('build.view')
        self.assignRole('part.view')

        response = self.post(
            reverse('api-search'),
            query,
            expected_code=200
        )

        # Check for expected results, based on permissions
        # We expect results to be returned for the following model types
        has_permission = [
            'build',
            'manufacturerpart',
            'supplierpart',
            'part',
            'partcategory',
            'stocklocation',
            'stockitem',
        ]

        for mdl in models:
            result = response.data[mdl]
            if mdl in has_permission:
                self.assertIn('count', result)
            else:
                self.assertIn('error', result)
                self.assertEqual(result['error'], 'User does not have permission to view this model')
