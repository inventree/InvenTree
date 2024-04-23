"""Tests for api_version."""

from django.urls import reverse

from InvenTree.api_version import INVENTREE_API_VERSION
from InvenTree.unit_test import InvenTreeAPITestCase
from InvenTree.version import inventreeApiText, parse_version_text


class ApiVersionTests(InvenTreeAPITestCase):
    """Tests for api_version functions and APIs."""

    def test_api(self):
        """Test that the API text is correct."""
        url = reverse('api-version-text')
        response = self.client.get(url, format='json')
        data = response.json()

        self.assertEqual(len(data), 10)

        response = self.client.get(reverse('api-version'), format='json').json()
        self.assertIn('version', response)
        self.assertIn('dev', response)
        self.assertIn('up_to_date', response)

    def test_inventree_api_text(self):
        """Test that the inventreeApiText function works expected."""
        # Normal run
        resp = inventreeApiText()
        self.assertEqual(len(resp), 10)

        # More responses
        resp = inventreeApiText(20)
        self.assertEqual(len(resp), 20)

        # Specific version
        resp = inventreeApiText(start_version=5)
        self.assertEqual(list(resp)[0], 'v5')

    def test_parse_version_text(self):
        """Test that api version text is correctly parsed."""
        resp = parse_version_text()

        # Check that all texts are parsed
        self.assertEqual(len(resp), INVENTREE_API_VERSION - 1)
