"""Unit tests for Part Views (see views.py)"""

from django.urls import reverse

from InvenTree.helpers import InvenTreeTestCase


class PartViewTestCase(InvenTreeTestCase):
    """Base class for unit testing the various Part views"""

    fixtures = [
        'category',
        'part',
        'bom',
        'location',
        'company',
        'supplier_part',
    ]

    roles = 'all'
    superuser = True


class PartDetailTest(PartViewTestCase):
    """Unit tests for the PartDetail view"""

    def test_bom_download(self):
        """Test downloading a BOM for a valid part."""
        response = self.client.get(reverse('bom-download', args=(1,)), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertIn('streaming_content', dir(response))


class PartQRTest(PartViewTestCase):
    """Tests for the Part QR Code AJAX view."""

    def test_html_redirect(self):
        """A HTML request for a QR code should be redirected (use an AJAX request instead)"""
        response = self.client.get(reverse('part-qr', args=(1,)))
        self.assertEqual(response.status_code, 302)

    def test_valid_part(self):
        """Test QR code response for a Part"""
        response = self.client.get(reverse('part-qr', args=(1,)), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

        data = str(response.content)

        self.assertIn('Part QR Code', data)
        self.assertIn('<img src=', data)

    def test_invalid_part(self):
        """Test response for an invalid Part ID value"""
        response = self.client.get(reverse('part-qr', args=(9999,)), HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(response.status_code, 200)
