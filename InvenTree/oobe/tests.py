"""Tests for setups"""

from django.urls import reverse

from InvenTree.api_tester import InvenTreeAPITestCase


class OOBEApiTest(InvenTreeAPITestCase):
    """Tests for the setups listing API"""

    def test_api_list(self):
        """Test list URL"""
        url = reverse('api-setup-list')
        self.get(url, expected_code=200)
