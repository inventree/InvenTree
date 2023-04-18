"""Helper functions for performing API unit tests."""

import csv
import io
import re

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.http.response import StreamingHttpResponse

from djmoney.contrib.exchange.models import ExchangeBackend, Rate
from rest_framework.test import APITestCase

from plugin import registry
from plugin.models import PluginConfig


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
        """Run setup for all tests in a given class"""
        super().setUpTestData()

        # Create a user to log in with
        cls.user = get_user_model().objects.create_user(
            username=cls.username,
            password=cls.password,
            email=cls.email
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
        """Run setup for individual test methods"""

        if self.auto_login:
            self.client.login(username=self.username, password=self.password)

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
            raise TypeError('assignRole: assign_all must be a boolean value')

        if not role and not assign_all:
            raise ValueError('assignRole: either role must be provided, or assign_all must be set')

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
    """Mixin class for generating exchange rate data"""

    def generate_exchange_rates(self):
        """Helper function which generates some exchange rates to work with"""

        rates = {
            'AUD': 1.5,
            'CAD': 1.7,
            'GBP': 0.9,
            'USD': 1.0,
        }

        # Create a dummy backend
        ExchangeBackend.objects.create(
            name='InvenTreeExchange',
            base_currency='USD',
        )

        backend = ExchangeBackend.objects.get(name='InvenTreeExchange')

        items = []

        for currency, rate in rates.items():
            items.append(
                Rate(
                    currency=currency,
                    value=rate,
                    backend=backend,
                )
            )

        Rate.objects.bulk_create(items)


class InvenTreeAPITestCase(ExchangeRateMixin, UserMixin, APITestCase):
    """Base class for running InvenTree API tests."""

    def checkResponse(self, url, method, expected_code, response):
        """Debug output for an unexpected response"""

        # No expected code, return
        if expected_code is None:
            return

        if expected_code != response.status_code:

            print(f"Unexpected {method} response at '{url}': status_code = {response.status_code}")

            if hasattr(response, 'data'):
                print('data:', response.data)
            if hasattr(response, 'body'):
                print('body:', response.body)
            if hasattr(response, 'content'):
                print('content:', response.content)

        self.assertEqual(expected_code, response.status_code)

    def getActions(self, url):
        """Return a dict of the 'actions' available at a given endpoint.

        Makes use of the HTTP 'OPTIONS' method to request this.
        """
        response = self.client.options(url)
        self.assertEqual(response.status_code, 200)

        actions = response.data.get('actions', None)

        if not actions:
            actions = {}

        return actions

    def get(self, url, data=None, expected_code=200, format='json'):
        """Issue a GET request."""
        # Set default - see B006
        if data is None:
            data = {}

        response = self.client.get(url, data, format=format)

        self.checkResponse(url, 'GET', expected_code, response)

        return response

    def post(self, url, data=None, expected_code=None, format='json'):
        """Issue a POST request."""

        # Set default value - see B006
        if data is None:
            data = {}

        response = self.client.post(url, data=data, format=format)

        self.checkResponse(url, 'POST', expected_code, response)

        return response

    def delete(self, url, data=None, expected_code=None, format='json'):
        """Issue a DELETE request."""

        if data is None:
            data = {}

        response = self.client.delete(url, data=data, format=format)

        self.checkResponse(url, 'DELETE', expected_code, response)

        return response

    def patch(self, url, data, expected_code=None, format='json'):
        """Issue a PATCH request."""
        response = self.client.patch(url, data=data, format=format)

        self.checkResponse(url, 'PATCH', expected_code, response)

        return response

    def put(self, url, data, expected_code=None, format='json'):
        """Issue a PUT request."""
        response = self.client.put(url, data=data, format=format)

        self.checkResponse(url, 'PUT', expected_code, response)

        return response

    def options(self, url, expected_code=None):
        """Issue an OPTIONS request."""
        response = self.client.options(url, format='json')

        self.checkResponse(url, 'OPTIONS', expected_code, response)

        return response

    def download_file(self, url, data, expected_code=None, expected_fn=None, decode=True):
        """Download a file from the server, and return an in-memory file."""
        response = self.client.get(url, data=data, format='json')

        if expected_code is not None:
            self.assertEqual(response.status_code, expected_code)

        # Check that the response is of the correct type
        if not isinstance(response, StreamingHttpResponse):
            raise ValueError("Response is not a StreamingHttpResponse object as expected")

        # Extract filename
        disposition = response.headers['Content-Disposition']

        result = re.search(r'attachment; filename="([\w.]+)"', disposition)

        fn = result.groups()[0]

        if expected_fn is not None:
            self.assertEqual(expected_fn, fn)

        if decode:
            # Decode data and return as StringIO file object
            fo = io.StringIO()
            fo.name = fo
            fo.write(response.getvalue().decode('UTF-8'))
        else:
            # Return a a BytesIO file object
            fo = io.BytesIO()
            fo.name = fn
            fo.write(response.getvalue())

        fo.seek(0)

        return fo

    def process_csv(self, fo, delimiter=',', required_cols=None, excluded_cols=None, required_rows=None):
        """Helper function to process and validate a downloaded csv file."""
        # Check that the correct object type has been passed
        self.assertTrue(isinstance(fo, io.StringIO))

        fo.seek(0)

        reader = csv.reader(fo, delimiter=delimiter)

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
