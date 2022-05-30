"""Unit tests for Part Views (see views.py)"""

from django.urls import reverse

from InvenTree.helpers import InvenTreeTestCase

from .models import Part


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


class PartListTest(PartViewTestCase):
    """Unit tests for the PartList view"""

    def test_part_index(self):
        """Test that the PartIndex page returns successfully"""
        response = self.client.get(reverse('part-index'))
        self.assertEqual(response.status_code, 200)

        keys = response.context.keys()
        self.assertIn('csrf_token', keys)
        self.assertIn('parts', keys)
        self.assertIn('user', keys)


class PartDetailTest(PartViewTestCase):
    """Unit tests for the PartDetail view"""

    def test_part_detail(self):
        """Test that we can retrieve a part detail page."""
        pk = 1

        response = self.client.get(reverse('part-detail', args=(pk,)))
        self.assertEqual(response.status_code, 200)

        part = Part.objects.get(pk=pk)

        keys = response.context.keys()

        self.assertIn('part', keys)
        self.assertIn('category', keys)

        self.assertEqual(response.context['part'].pk, pk)
        self.assertEqual(response.context['category'], part.category)

    def test_part_detail_from_ipn(self):
        """Test that we can retrieve a part detail page from part IPN:

        - if no part with matching IPN -> return part index
        - if unique IPN match -> return part detail page
        - if multiple IPN matches -> return part index
        """
        ipn_test = 'PART-000000-AA'
        pk = 1

        def test_ipn_match(index_result=False, detail_result=False):
            """Helper function for matching IPN detail view"""
            index_redirect = False
            detail_redirect = False

            response = self.client.get(reverse('part-detail-from-ipn', args=(ipn_test,)))

            # Check for PartIndex redirect
            try:
                if response.url == '/part/':
                    index_redirect = True
            except AttributeError:
                pass

            # Check for PartDetail redirect
            try:
                if response.context['part'].pk == pk:
                    detail_redirect = True
            except TypeError:
                pass

            self.assertEqual(index_result, index_redirect)
            self.assertEqual(detail_result, detail_redirect)

        # Test no match
        test_ipn_match(index_result=True, detail_result=False)

        # Test unique match
        part = Part.objects.get(pk=pk)
        part.IPN = ipn_test
        part.save()

        test_ipn_match(index_result=False, detail_result=True)

        # Test multiple matches
        part = Part.objects.get(pk=pk + 1)
        part.IPN = ipn_test
        part.save()

        test_ipn_match(index_result=True, detail_result=False)

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


class CategoryTest(PartViewTestCase):
    """Tests for PartCategory related views."""

    def test_set_category(self):
        """Test that the "SetCategory" view works."""
        url = reverse('part-set-category')

        response = self.client.get(url, {'parts[]': 1}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

        data = {
            'part_id_10': True,
            'part_id_1': True,
            'part_category': 5
        }

        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
