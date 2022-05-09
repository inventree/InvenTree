"""Tests for setups"""

from django.urls import reverse

from InvenTree.api_tester import InvenTreeAPITestCase


class OOBEApiTest(InvenTreeAPITestCase):
    """Tests for the setups listing API"""

    def test_api_list(self):
        """Test list URL"""
        url = reverse('api-setup-list')
        self.get(url, expected_code=200)

    def test_view(self):
        """Test initial setup view"""
        url = reverse('dynamic_setup', kwargs={'setup': 'initial'})

        # Check that the setup redirects to the first setup page
        response = self.get(url, expected_code=302)
        self.assertTrue('welcome' in response.url)
        url = response.url

        # check the first page loads without errors
        self.get(url, expected_code=200)
