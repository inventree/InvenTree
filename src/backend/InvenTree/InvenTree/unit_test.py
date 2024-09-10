"""Helper functions for unit testing / CI."""

import csv
import io
import json
import re
import time
from contextlib import contextmanager
from pathlib import Path

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.db import connections, models
from django.http.response import StreamingHttpResponse
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from djmoney.contrib.exchange.models import ExchangeBackend, Rate
from rest_framework.test import APITestCase

from plugin import registry
from plugin.models import PluginConfig


def addUserPermission(user, permission):
    """Shortcut function for adding a certain permission to a user."""
    perm = Permission.objects.get(codename=permission)
    user.user_permissions.add(perm)


def addUserPermissions(user, permissions):
    """Shortcut function for adding multiple permissions to a user."""
    for permission in permissions:
        addUserPermission(user, permission)


def getMigrationFileNames(app):
    """Return a list of all migration filenames for provided app."""
    local_dir = Path(__file__).parent
    files = local_dir.joinpath('..', app, 'migrations').iterdir()

    # Regex pattern for migration files
    regex = re.compile(r'^[\d]+_.*\.py$')

    migration_files = []

    for f in files:
        if regex.match(f.name):
            migration_files.append(f.name)

    return migration_files


def getOldestMigrationFile(app, exclude_extension=True, ignore_initial=True):
    """Return the filename associated with the oldest migration."""
    oldest_num = -1
    oldest_file = None

    for f in getMigrationFileNames(app):
        if ignore_initial and f.startswith('0001_initial'):
            continue

        num = int(f.split('_')[0])

        if oldest_file is None or num < oldest_num:
            oldest_num = num
            oldest_file = f

    if exclude_extension:
        oldest_file = oldest_file.replace('.py', '')

    return oldest_file


def getNewestMigrationFile(app, exclude_extension=True):
    """Return the filename associated with the newest migration."""
    newest_file = None
    newest_num = -1

    for f in getMigrationFileNames(app):
        num = int(f.split('_')[0])

        if newest_file is None or num > newest_num:
            newest_num = num
            newest_file = f

    if not newest_file:  # pragma: no cover
        return newest_file

    if exclude_extension:
        newest_file = newest_file.replace('.py', '')

    return newest_file


class UserMixin:
    """Mixin to setup a user and login for tests.

    Use parameters to set username, password, email, roles and permissions.
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

    @classmethod
    def setUpTestData(cls):
        """Run setup for all tests in a given class."""
        super().setUpTestData()

        # Create a user to log in with
        cls.user = get_user_model().objects.create_user(
            username=cls.username, password=cls.password, email=cls.email
        )

        # Create a group for the user
        cls.group = Group.objects.create(name='my_test_group')
        cls.user.groups.add(cls.group)

        if cls.superuser:
            cls.user.is_superuser = True

        if cls.is_staff:
            cls.user.is_staff = True

        cls.user.save()

        # Assign all roles if set
        if cls.roles == 'all':
            cls.assignRole(group=cls.group, assign_all=True)

        # else filter the roles
        else:
            for role in cls.roles:
                cls.assignRole(role=role, group=cls.group)

    def setUp(self):
        """Run setup for individual test methods."""
        if self.auto_login:
            self.login()

    def login(self):
        """Login with the current user credentials."""
        self.client.login(username=self.username, password=self.password)

    def logout(self):
        """Lougout current user."""
        self.client.logout()

    @classmethod
    def clearRoles(cls):
        """Remove all user roles from the registered user."""
        for ruleset in cls.group.rule_sets.all():
            ruleset.can_view = False
            ruleset.can_change = False
            ruleset.can_delete = False
            ruleset.can_add = False

            ruleset.save()

    @classmethod
    def assignRole(cls, role=None, assign_all: bool = False, group=None):
        """Set the user roles for the registered user.

        Arguments:
            role: Role of the format 'rule.permission' e.g. 'part.add'
            assign_all: Set to True to assign *all* roles
            group: The group to assign roles to (or leave None to use the group assigned to this class)
        """
        if group is None:
            group = cls.group

        if type(assign_all) is not bool:
            # Raise exception if common mistake is made!
            raise TypeError(
                'assignRole: assign_all must be a boolean value'
            )  # pragma: no cover

        if not role and not assign_all:
            raise ValueError(
                'assignRole: either role must be provided, or assign_all must be set'
            )  # pragma: no cover

        if not assign_all and role:
            rule, perm = role.split('.')

        for ruleset in group.rule_sets.all():
            if assign_all or ruleset.name == rule:
                if assign_all or perm == 'view':
                    ruleset.can_view = True
                elif assign_all or perm == 'change':
                    ruleset.can_change = True
                elif assign_all or perm == 'delete':
                    ruleset.can_delete = True
                elif assign_all or perm == 'add':
                    ruleset.can_add = True

                ruleset.save()
                if not assign_all:
                    break


class PluginMixin:
    """Mixin to ensure that all plugins are loaded for tests."""

    def setUp(self):
        """Setup for plugin tests."""
        super().setUp()

        # Load plugin configs
        self.plugin_confs = PluginConfig.objects.all()
        # Reload if not present
        if not self.plugin_confs:
            registry.reload_plugins()
            self.plugin_confs = PluginConfig.objects.all()


class ExchangeRateMixin:
    """Mixin class for generating exchange rate data."""

    def generate_exchange_rates(self):
        """Helper function which generates some exchange rates to work with."""
        rates = {'AUD': 1.5, 'CAD': 1.7, 'GBP': 0.9, 'USD': 1.0}

        # Create a dummy backend
        ExchangeBackend.objects.create(name='InvenTreeExchange', base_currency='USD')

        backend = ExchangeBackend.objects.get(name='InvenTreeExchange')

        items = []

        for currency, rate in rates.items():
            items.append(Rate(currency=currency, value=rate, backend=backend))

        Rate.objects.bulk_create(items)


class InvenTreeTestCase(ExchangeRateMixin, UserMixin, TestCase):
    """Testcase with user setup build in."""


class InvenTreeAPITestCase(ExchangeRateMixin, UserMixin, APITestCase):
    """Base class for running InvenTree API tests."""

    # Default query count threshold value
    # TODO: This value should be reduced
    MAX_QUERY_COUNT = 250

    WARNING_QUERY_THRESHOLD = 100

    # Default query time threshold value
    # TODO: This value should be reduced
    # Note: There is a lot of variability in the query time in unit testing...
    MAX_QUERY_TIME = 7.5

    @contextmanager
    def assertNumQueriesLessThan(self, value, using='default', verbose=None, url=None):
        """Context manager to check that the number of queries is less than a certain value.

        Example:
        with self.assertNumQueriesLessThan(10):
            # Do some stuff
        Ref: https://stackoverflow.com/questions/1254170/django-is-there-a-way-to-count-sql-queries-from-an-unit-test/59089020#59089020
        """
        with CaptureQueriesContext(connections[using]) as context:
            yield  # your test will be run here

        n = len(context.captured_queries)

        if url and n >= value:
            print(
                f'Query count exceeded at {url}: Expected < {value} queries, got {n}'
            )  # pragma: no cover

        if verbose or n >= value:
            msg = f'\r\n{json.dumps(context.captured_queries, indent=4)}'  # pragma: no cover
        else:
            msg = None

        if url and n > self.WARNING_QUERY_THRESHOLD:
            print(f'Warning: {n} queries executed at {url}')

        self.assertLess(n, value, msg=msg)

    def check_response(self, url, response, expected_code=None):
        """Debug output for an unexpected response."""
        # Check that the response returned the expected status code

        if expected_code is not None:
            if expected_code != response.status_code:  # pragma: no cover
                print(
                    f"Unexpected response at '{url}': status_code = {response.status_code} (expected {expected_code})"
                )

                if hasattr(response, 'data'):
                    print('data:', response.data)
                if hasattr(response, 'body'):
                    print('body:', response.body)
                if hasattr(response, 'content'):
                    print('content:', response.content)

            self.assertEqual(response.status_code, expected_code)

    def getActions(self, url):
        """Return a dict of the 'actions' available at a given endpoint.

        Makes use of the HTTP 'OPTIONS' method to request this.
        """
        response = self.client.options(url)
        self.assertEqual(response.status_code, 200)

        actions = response.data.get('actions', {})
        return actions

    def query(self, url, method, data=None, **kwargs):
        """Perform a generic API query."""
        if data is None:
            data = {}

        kwargs['format'] = kwargs.get('format', 'json')

        expected_code = kwargs.pop('expected_code', None)
        max_queries = kwargs.pop('max_query_count', self.MAX_QUERY_COUNT)
        max_query_time = kwargs.pop('max_query_time', self.MAX_QUERY_TIME)

        t1 = time.time()

        with self.assertNumQueriesLessThan(max_queries, url=url):
            response = method(url, data, **kwargs)

        t2 = time.time()
        dt = t2 - t1

        self.check_response(url, response, expected_code=expected_code)

        if dt > max_query_time:
            print(
                f'Query time exceeded at {url}: Expected {max_query_time}s, got {dt}s'
            )

        self.assertLessEqual(dt, max_query_time)

        return response

    def get(self, url, data=None, expected_code=200, **kwargs):
        """Issue a GET request."""
        kwargs['data'] = data

        return self.query(url, self.client.get, expected_code=expected_code, **kwargs)

    def post(self, url, data=None, expected_code=201, **kwargs):
        """Issue a POST request."""
        # Default query limit is higher for POST requests, due to extra event processing
        kwargs['max_query_count'] = kwargs.get(
            'max_query_count', self.MAX_QUERY_COUNT + 100
        )

        kwargs['data'] = data

        return self.query(url, self.client.post, expected_code=expected_code, **kwargs)

    def delete(self, url, data=None, expected_code=204, **kwargs):
        """Issue a DELETE request."""
        kwargs['data'] = data

        return self.query(
            url, self.client.delete, expected_code=expected_code, **kwargs
        )

    def patch(self, url, data, expected_code=200, **kwargs):
        """Issue a PATCH request."""
        kwargs['data'] = data

        return self.query(url, self.client.patch, expected_code=expected_code, **kwargs)

    def put(self, url, data, expected_code=200, **kwargs):
        """Issue a PUT request."""
        kwargs['data'] = data

        return self.query(url, self.client.put, expected_code=expected_code, **kwargs)

    def options(self, url, expected_code=None, **kwargs):
        """Issue an OPTIONS request."""
        kwargs['data'] = kwargs.get('data', None)

        return self.query(
            url, self.client.options, expected_code=expected_code, **kwargs
        )

    def download_file(
        self, url, data, expected_code=None, expected_fn=None, decode=True, **kwargs
    ):
        """Download a file from the server, and return an in-memory file."""
        response = self.client.get(url, data=data, format='json')

        self.check_response(url, response, expected_code=expected_code)

        # Check that the response is of the correct type
        if not isinstance(response, StreamingHttpResponse):
            raise ValueError(
                'Response is not a StreamingHttpResponse object as expected'
            )

        # Extract filename
        disposition = response.headers['Content-Disposition']

        result = re.search(r'attachment; filename="([\w\d\-.]+)"', disposition)

        fn = result.groups()[0]

        if expected_fn is not None:
            self.assertRegex(fn, expected_fn)

        if decode:
            # Decode data and return as StringIO file object
            file = io.StringIO()
            file.name = file
            file.write(response.getvalue().decode('UTF-8'))
        else:
            # Return a a BytesIO file object
            file = io.BytesIO()
            file.name = fn
            file.write(response.getvalue())

        file.seek(0)

        return file

    def process_csv(
        self,
        file_object,
        delimiter=',',
        required_cols=None,
        excluded_cols=None,
        required_rows=None,
    ):
        """Helper function to process and validate a downloaded csv file."""
        # Check that the correct object type has been passed
        self.assertIsInstance(file_object, io.StringIO)

        file_object.seek(0)

        reader = csv.reader(file_object, delimiter=delimiter)

        headers = []
        rows = []

        for idx, row in enumerate(reader):
            if idx == 0:
                headers = row
            else:
                rows.append(row)

        if required_cols is not None:
            for col in required_cols:
                self.assertIn(col, headers)

        if excluded_cols is not None:
            for col in excluded_cols:
                self.assertNotIn(col, headers)

        if required_rows is not None:
            self.assertEqual(len(rows), required_rows)

        # Return the file data as a list of dict items, based on the headers
        data = []

        for row in rows:
            entry = {}

            for idx, col in enumerate(headers):
                entry[col] = row[idx]

            data.append(entry)

        return data

    def assertDictContainsSubset(self, a, b):
        """Assert that dictionary 'a' is a subset of dictionary 'b'."""
        self.assertEqual(b, b | a)


class AdminTestCase(InvenTreeAPITestCase):
    """Tests for the admin interface integration."""

    superuser = True

    def helper(self, model: type[models.Model], model_kwargs=None):
        """Test the admin URL."""
        if model_kwargs is None:
            model_kwargs = {}

        # Add object
        obj = model.objects.create(**model_kwargs)
        app_app, app_mdl = model._meta.app_label, model._meta.model_name

        # 'Test listing
        response = self.get(reverse(f'admin:{app_app}_{app_mdl}_changelist'))
        self.assertEqual(response.status_code, 200)

        # Test change view
        response = self.get(
            reverse(f'admin:{app_app}_{app_mdl}_change', kwargs={'object_id': obj.pk})
        )
        self.assertEqual(response.status_code, 200)

        return obj
