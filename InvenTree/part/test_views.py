""" Unit tests for Part Views (see views.py) """

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

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

    def test_part_index(self):
        response = self.client.get(reverse('part-index'))
        self.assertEqual(response.status_code, 200)
        
        keys = response.context.keys()
        self.assertIn('csrf_token', keys)
        self.assertIn('parts', keys)
        self.assertIn('user', keys)
    
