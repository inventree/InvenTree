"""Unit tests for action caller sample."""

from django.test import TestCase

import requests_mock

from plugin import registry


class SampleApiCallerPluginTests(TestCase):
    """Tests for SampleApiCallerPluginTests."""

    @requests_mock.Mocker()
    def test_return(self, m):
        """Check if the external api call works."""
        # Set up mock responses
        m.get('https://api.example.com/api/users/2', json={'data': 'sample'})

        # The plugin should be defined
        self.assertIn('sample-api-caller', registry.plugins)
        plg = registry.plugins['sample-api-caller']
        self.assertTrue(plg)

        # do an api call
        result = plg.get_external_url()

        self.assertTrue(result)
        self.assertIn('data', result)
