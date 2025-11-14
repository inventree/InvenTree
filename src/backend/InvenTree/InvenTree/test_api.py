"""Low level tests for the InvenTree API."""

from base64 import b64encode
from pathlib import Path
from tempfile import TemporaryDirectory

from django.urls import reverse

from rest_framework import status

from InvenTree.api import read_license_file
from InvenTree.api_version import INVENTREE_API_VERSION
from InvenTree.unit_test import InvenTreeAPITestCase, InvenTreeTestCase
from InvenTree.version import inventreeApiText, parse_version_text
from users.ruleset import RULESET_NAMES
from users.tasks import update_group_roles


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
        response = self.client.get(url, headers={'accept': 'application/json'})
        self.assertEqual(response.status_code, 200)

    def test_build_api(self):
        """Test that build list is working."""
        url = reverse('api-build-list')

        # Check JSON response
        response = self.client.get(url, headers={'accept': 'application/json'})
        self.assertEqual(response.status_code, 200)

    def test_stock_api(self):
        """Test that stock list is working."""
        url = reverse('api-stock-list')

        # Check JSON response
        response = self.client.get(url, headers={'accept': 'application/json'})
        self.assertEqual(response.status_code, 200)

    def test_company_list(self):
        """Test that company list is working."""
        url = reverse('api-company-list')

        # Check JSON response
        response = self.client.get(url, headers={'accept': 'application/json'})
        self.assertEqual(response.status_code, 200)

    def test_not_found(self):
        """Test that the NotFoundView is working with all available methods."""
        methods = ['options', 'get', 'post', 'patch', 'put', 'delete']
        for method in methods:
            response = getattr(self.client, method)('/api/anc')
            self.assertEqual(response.status_code, 404)


class ApiAccessTests(InvenTreeAPITestCase):
    """Tests for various access scenarios with the InvenTree API."""

    fixtures = ['location', 'category', 'part', 'stock']
    roles = ['part.view']
    token = None
    auto_login = False

    def basicAuth(self):
        """Helper function to use basic auth."""
        # Use basic authentication

        authstring = bytes(f'{self.username}:{self.password}', 'ascii')

        # Use "basic" auth by default
        auth = b64encode(authstring).decode('ascii')
        self.client.credentials(HTTP_AUTHORIZATION=f'Basic {auth}')

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
        self.get(url, expected_code=401)
        self.assertIsNone(self.token)

    def test_token_success(self):
        """Test token auth works."""
        self.tokenAuth()
        self.assertIsNotNone(self.token)

        # Run explicit test with token auth
        url = reverse('api-license')
        response = self.get(
            url, headers={'Authorization': f'Token {self.token}'}, expected_code=200
        )
        self.assertIn('backend', response.json())

    def test_role_view(self):
        """Test that we can access the 'roles' view for the logged in user.

        Also tests that it is *not* accessible if the client is not logged in.
        """
        url = reverse('api-user-roles')

        # Delete all rules
        self.group.rule_sets.all().delete()
        update_group_roles(self.group)

        response = self.get(url, expected_code=401)

        # Not logged in, so cannot access user role data
        self.assertIn(response.status_code, [401, 403])

        # Now log in!
        self.basicAuth()
        self.assignRole('part.view')

        response = self.get(url)

        data = response.data

        self.assertIn('user', data)
        self.assertIn('username', data)
        self.assertIn('is_staff', data)
        self.assertIn('is_superuser', data)
        self.assertIn('roles', data)

        roles = data['roles']

        role_names = roles.keys()

        # By default, no permissions are provided
        for rule in RULESET_NAMES:
            self.assertIn(rule, role_names)

            if roles[rule] is None:
                continue

            if rule == 'part':
                self.assertIn('view', roles[rule])
            else:
                self.assertNotIn('view', roles[rule])
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

        for rule in RULESET_NAMES:
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

        self.assertEqual(len(actions), 3)

        self.assertIn('POST', actions)
        self.assertIn('GET', actions)
        self.assertIn('PUT', actions)  # Fancy bulk-update action

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
    """Unit tests for the BulkDelete endpoints."""

    superuser = True

    def test_errors(self):
        """Test that the correct errors are thrown."""
        url = reverse('api-stock-test-result-list')

        # DELETE without any of the required fields
        response = self.delete(url, {}, expected_code=400)

        self.assertIn(
            'List of items or filters must be provided for bulk operation',
            str(response.data),
        )

        # DELETE with invalid 'items'
        response = self.delete(url, {'items': {'hello': 'world'}}, expected_code=400)

        self.assertIn('Items must be provided as a list', str(response.data))

        # DELETE with invalid 'filters'
        response = self.delete(url, {'filters': [1, 2, 3]}, expected_code=400)

        self.assertIn('Filters must be provided as a dict', str(response.data))


class SearchTests(InvenTreeAPITestCase):
    """Unit tests for global search endpoint."""

    fixtures = [
        'category',
        'part',
        'company',
        'location',
        'supplier_part',
        'stock',
        'order',
        'sales_order',
        'build',
    ]
    roles = ['build.view', 'part.view']

    def test_empty(self):
        """Test empty request."""
        data = ['', None, {}]

        for d in data:
            response = self.post(reverse('api-search'), d, expected_code=400)
            self.assertIn('Search term must be provided', str(response.data))

    def test_results(self):
        """Test individual result types."""
        response = self.post(
            reverse('api-search'),
            {'search': 'chair', 'limit': 3, 'part': {}, 'build': {}},
            expected_code=200,
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
            {'search': '01', 'limit': 2, 'purchaseorder': {}, 'salesorder': {}},
            expected_code=200,
        )
        self.assertEqual(
            response.data['purchaseorder'],
            {'error': 'User does not have permission to view this model'},
        )

        # Add permissions and try again
        self.assignRole('purchase_order.view')
        self.assignRole('sales_order.view')
        response = self.post(
            reverse('api-search'),
            {'search': '01', 'limit': 2, 'purchaseorder': {}, 'salesorder': {}},
            expected_code=200,
        )

        self.assertEqual(response.data['purchaseorder']['count'], 1)
        self.assertEqual(response.data['salesorder']['count'], 0)

        self.assertNotIn('stockitem', response.data)
        self.assertNotIn('build', response.data)

    def test_search_filters(self):
        """Test that the regex, whole word, and notes filters are handled correctly."""
        SEARCH_TERM = 'some note'
        RE_SEARCH_TERM = 'some (.*) note'

        response = self.post(
            reverse('api-search'),
            {'search': SEARCH_TERM, 'limit': 10, 'part': {}, 'build': {}},
            expected_code=200,
        )
        # No build or part results
        self.assertEqual(response.data['build']['count'], 0)
        self.assertEqual(response.data['part']['count'], 0)

        # add the search_notes param
        response = self.post(
            reverse('api-search'),
            {
                'search': SEARCH_TERM,
                'limit': 10,
                'search_notes': True,
                'part': {},
                'build': {},
            },
            expected_code=200,
        )
        # now should have some build results
        self.assertEqual(response.data['build']['count'], 4)

        # use the regex term
        response = self.post(
            reverse('api-search'),
            {
                'search': RE_SEARCH_TERM,
                'limit': 10,
                'search_notes': True,
                'part': {},
                'build': {},
            },
            expected_code=200,
        )
        # No results again
        self.assertEqual(response.data['build']['count'], 0)

        # add the regex_search param
        response = self.post(
            reverse('api-search'),
            {
                'search': RE_SEARCH_TERM,
                'limit': 10,
                'search_notes': True,
                'search_regex': True,
                'part': {},
                'build': {},
            },
            expected_code=200,
        )
        # we get our results back!
        self.assertEqual(response.data['build']['count'], 4)

        # add the search_whole param
        response = self.post(
            reverse('api-search'),
            {
                'search': RE_SEARCH_TERM,
                'limit': 10,
                'search_notes': True,
                'search_whole': True,
                'part': {},
                'build': {},
            },
            expected_code=200,
        )
        # No results again
        self.assertEqual(response.data['build']['count'], 0)

    def test_permissions(self):
        """Test that users with insufficient permissions are handled correctly."""
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

        query = {'search': 'c', 'limit': 3}

        for mdl in models:
            query[mdl] = {}

        response = self.post(reverse('api-search'), query, expected_code=200)

        # Check for 'permission denied' error
        for mdl in models:
            self.assertEqual(
                response.data[mdl]['error'],
                'User does not have permission to view this model',
            )

        # Assign view roles for some parts
        self.assignRole('build.view')
        self.assignRole('part.view')

        response = self.post(reverse('api-search'), query, expected_code=200)

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
                self.assertEqual(
                    result['error'], 'User does not have permission to view this model'
                )


class GeneralApiTests(InvenTreeAPITestCase):
    """Tests for various api endpoints."""

    def test_api_version(self):
        """Test that the API text is correct."""
        url = reverse('api-version-text')
        response = self.get(url, format='json')
        data = response.json()

        self.assertEqual(len(data), 10)

        response = self.get(reverse('api-version')).json()
        self.assertIn('version', response)
        self.assertIn('dev', response)
        self.assertIn('up_to_date', response)

    def test_inventree_api_text_fnc(self):
        """Test that the inventreeApiText function works expected."""
        latest_version = f'v{INVENTREE_API_VERSION}'

        # Normal run
        resp = inventreeApiText()
        self.assertEqual(len(resp), 10)
        self.assertIn(latest_version, resp)

        # More responses
        resp = inventreeApiText(20)
        self.assertEqual(len(resp), 20)
        self.assertIn(latest_version, resp)

        # Specific version
        resp = inventreeApiText(start_version=5)
        self.assertEqual(list(resp)[0], 'v5')
        self.assertEqual(list(resp)[-1], 'v14')

    def test_parse_version_text_fnc(self):
        """Test that api version text is correctly parsed."""
        resp = parse_version_text()

        latest_version = INVENTREE_API_VERSION
        self.assertTrue(resp[f'v{latest_version}']['latest'])

        # All fields except github link should exist for every version
        latest_count = 0
        for k, v in resp.items():
            self.assertEqual('v', k[0], f'Version should start with v: {k}')
            self.assertEqual(k, v['version'])
            self.assertGreater(len(v['date']), 0, f'Date is missing from {v}')
            self.assertGreater(len(v['text']), 0, f'Text is missing from {v}')
            self.assertIsNotNone(v['latest'])
            latest_count = latest_count + (1 if v['latest'] else 0)
        self.assertEqual(1, latest_count, 'Should have a single version marked latest')

        # Check that all texts are parsed: v1 and v2 are missing
        self.assertEqual(len(resp), INVENTREE_API_VERSION - 2)

    def test_api_license(self):
        """Test that the license endpoint is working."""
        response = self.get(reverse('api-license')).json()
        self.assertIn('backend', response)
        self.assertIn('frontend', response)

        # Various problem cases
        # File does not exist
        with self.assertLogs(logger='inventree', level='ERROR') as log:
            respo = read_license_file(Path('does not exsist'))
            self.assertEqual(respo, [])

            self.assertIn('License file not found at', str(log.output))

        with TemporaryDirectory() as tmp:  # type: ignore[no-matching-overload]
            sample_file = Path(tmp, 'temp.txt')
            sample_file.write_text('abc', 'utf-8')

            # File is not a json
            with self.assertLogs(logger='inventree', level='ERROR') as log:
                respo = read_license_file(sample_file)
                self.assertEqual(respo, [])

                self.assertIn('Failed to parse license file', str(log.output))

    def test_info_view(self):
        """Test that we can read the 'info-view' endpoint."""
        from plugin import PluginMixinEnum
        from plugin.models import PluginConfig
        from plugin.registry import registry

        self.ensurePluginsLoaded()

        url = reverse('api-inventree-info')

        response = self.get(url, max_query_count=20, expected_code=200)

        data = response.json()
        self.assertIn('server', data)
        self.assertIn('version', data)
        self.assertIn('instance', data)

        self.assertEqual('InvenTree', data['server'])

        # Test with token
        token = self.get(url=reverse('api-token'), max_query_count=20).data['token']
        self.client.logout()

        # Anon
        response = self.get(url, max_query_count=20)
        data = response.json()
        self.assertEqual(data['database'], None)
        self.assertIsNotNone(data.get('active_plugins'))

        # Staff
        response = self.get(
            url, headers={'Authorization': f'Token {token}'}, max_query_count=20
        )
        self.assertGreater(len(response.json()['database']), 4)

        data = response.json()

        # Check for active plugin list
        self.assertIn('active_plugins', data)
        plugins = data['active_plugins']

        # Check that all active plugins are listed
        N = len(plugins)
        self.assertGreater(N, 0, 'No active plugins found')
        self.assertLess(N, PluginConfig.objects.count(), 'Too many plugins found')
        self.assertEqual(
            N,
            len(registry.with_mixin(PluginMixinEnum.BASE, active=True)),
            'Incorrect number of active plugins found',
        )

        keys = [plugin['slug'] for plugin in plugins]

        self.assertIn('bom-exporter', keys)
        self.assertIn('inventree-ui-notification', keys)
        self.assertIn('inventreelabel', keys)
