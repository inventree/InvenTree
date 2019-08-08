""" Unit tests for Part Views (see views.py) """

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from .models import Part

class PartViewTestCase(TestCase):
    
    fixtures = [
        'category',
        'part',
        'location',
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
        self.assertIn('<img src=', data)

    def test_invalid_part(self):
        response = self.client.get(reverse('part-qr', args=(9999,)), HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        data = str(response.content)
        
        self.assertIn('Error:', data)
