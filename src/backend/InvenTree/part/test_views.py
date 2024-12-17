"""Unit tests for Part Views (see views.py)."""

from django.urls import reverse

from InvenTree.unit_test import InvenTreeTestCase


class PartViewTestCase(InvenTreeTestCase):
    """Base class for unit testing the various Part views."""

    fixtures = ['category', 'part', 'bom', 'location', 'company', 'supplier_part']

    roles = 'all'
    superuser = True


class PartDetailTest(PartViewTestCase):
    """Unit tests for the PartDetail view."""

    def test_bom_download(self):
        """Test downloading a BOM for a valid part."""
        response = self.client.get(
            reverse('api-bom-download', args=(1,)),
            headers={'x-requested-with': 'XMLHttpRequest'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('streaming_content', dir(response))
