""" Unit tests for Part Views (see views.py) """

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from .models import Part


class PartViewTestCase(TestCase):
    
    fixtures = [
        'category',
        'part',
        'bom',
        'location',
        'company',
        'supplier_part',
    ]

    def setUp(self):
        super().setUp()

        # Create a user
        User = get_user_model()
        User.objects.create_user('username', 'user@email.com', 'password')

        self.client.login(username='username', password='password')


class PartListTest(PartViewTestCase):

    def test_part_index(self):
        response = self.client.get(reverse('part-index'))
        self.assertEqual(response.status_code, 200)
        
        keys = response.context.keys()
        self.assertIn('csrf_token', keys)
        self.assertIn('parts', keys)
        self.assertIn('user', keys)
    
    def test_export(self):
        """ Export part data to CSV """

        response = self.client.get(reverse('part-export'), {'parts': '1,2,3,4,5,6,7,8,9,10'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(response.status_code, 200)
        self.assertIn('streaming_content', dir(response))


class PartDetailTest(PartViewTestCase):

    def test_part_detail(self):
        """ Test that we can retrieve a part detail page """

        pk = 1

        response = self.client.get(reverse('part-detail', args=(pk,)))
        self.assertEqual(response.status_code, 200)

        part = Part.objects.get(pk=pk)

        keys = response.context.keys()

        self.assertIn('part', keys)
        self.assertIn('category', keys)

        self.assertEqual(response.context['part'].pk, pk)
        self.assertEqual(response.context['category'], part.category)

        self.assertFalse(response.context['editing_enabled'])

    def test_editable(self):

        pk = 1
        response = self.client.get(reverse('part-detail', args=(pk,)), {'edit': True})

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['editing_enabled'])

    def test_part_detail_from_ipn(self):
        """
        Test that we can retrieve a part detail page from part IPN:
        - if no part with matching IPN -> return part index
        - if unique IPN match -> return part detail page
        - if multiple IPN matches -> return part index
        """
        ipn_test = 'PART-000000-AA'
        pk = 1

        def test_ipn_match(index_result=False, detail_result=False):
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
        """ Test downloading a BOM for a valid part """

        response = self.client.get(reverse('bom-download', args=(1,)), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertIn('streaming_content', dir(response))
    

class PartTests(PartViewTestCase):
    """ Tests for Part forms """

    def test_part_edit(self):
        response = self.client.get(reverse('part-edit', args=(1,)), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

        keys = response.context.keys()
        data = str(response.content)

        self.assertIn('part', keys)
        self.assertIn('csrf_token', keys)

        self.assertIn('html_form', data)
        self.assertIn('"title":', data)

    def test_part_create(self):
        """ Launch form to create a new part """
        response = self.client.get(reverse('part-create'), {'category': 1}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

        # And again, with an invalid category
        response = self.client.get(reverse('part-create'), {'category': 9999}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

        # And again, with no category
        response = self.client.get(reverse('part-create'), {'name': 'Test part'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

    def test_part_duplicate(self):
        """ Launch form to duplicate part """

        # First try with an invalid part
        response = self.client.get(reverse('part-duplicate', args=(9999,)), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('part-duplicate', args=(1,)), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

    def test_make_variant(self):

        response = self.client.get(reverse('make-part-variant', args=(1,)), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)


class PartAttachmentTests(PartViewTestCase):

    def test_valid_create(self):
        """ test creation of an attachment for a valid part """

        response = self.client.get(reverse('part-attachment-create'), {'part': 1}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

    def test_invalid_create(self):
        """ test creation of an attachment for an invalid part """

        # TODO
        pass

    def test_edit(self):
        """ test editing an attachment """

        # TODO
        pass


class PartQRTest(PartViewTestCase):
    """ Tests for the Part QR Code AJAX view """

    def test_html_redirect(self):
        # A HTML request for a QR code should be redirected (use an AJAX request instead)
        response = self.client.get(reverse('part-qr', args=(1,)))
        self.assertEqual(response.status_code, 302)

    def test_valid_part(self):
        response = self.client.get(reverse('part-qr', args=(1,)), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        
        data = str(response.content)

        self.assertIn('Part QR Code', data)
        self.assertIn('<img class=', data)

    def test_invalid_part(self):
        response = self.client.get(reverse('part-qr', args=(9999,)), HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        data = str(response.content)
        
        self.assertIn('Error:', data)


class CategoryTest(PartViewTestCase):
    """ Tests for PartCategory related views """

    def test_create(self):
        """ Test view for creating a new category """
        response = self.client.get(reverse('category-create'), {'category': 1}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(response.status_code, 200)

    def test_create_invalid_parent(self):
        """ test creation of a new category with an invalid parent """
        response = self.client.get(reverse('category-create'), {'category': 9999}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        # Form should still return OK
        self.assertEqual(response.status_code, 200)

    def test_edit(self):
        """ Retrieve the part category editing form """
        response = self.client.get(reverse('category-edit', args=(1,)), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

    def test_set_category(self):
        """ Test that the "SetCategory" view works """

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


class BomItemTests(PartViewTestCase):
    """ Tests for BomItem related views """

    def test_create_valid_parent(self):
        """ Create a BomItem for a valid part """
        response = self.client.get(reverse('bom-item-create'), {'parent': 1}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

    def test_create_no_parent(self):
        """ Create a BomItem without a parent """
        response = self.client.get(reverse('bom-item-create'), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

    def test_create_invalid_parent(self):
        """ Create a BomItem with an invalid parent """
        response = self.client.get(reverse('bom-item-create'), {'parent': 99999}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
