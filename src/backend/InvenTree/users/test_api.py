"""API tests for various user / auth API endpoints"""

from django.contrib.auth.models import Group, User
from django.urls import reverse

from InvenTree.unit_test import InvenTreeAPITestCase


class UserAPITests(InvenTreeAPITestCase):
    """Tests for user API endpoints"""

    def test_user_api(self):
        """Tests for User API endpoints"""

        response = self.get(
            reverse('api-user-list'),
            expected_code=200
        )

        # Check the correct number of results was returned
        self.assertEqual(len(response.data), User.objects.count())

        for key in ['username', 'pk', 'email']:
            self.assertIn(key, response.data[0])

        # Check detail URL
        pk = response.data[0]['pk']

        response = self.get(
            reverse('api-user-detail', kwargs={'pk': pk}),
            expected_code=200
        )

        self.assertIn('pk', response.data)
        self.assertIn('username', response.data)

    def test_group_api(self):
        """Tests for the Group API endpoints"""

        response = self.get(
            reverse('api-group-list'),
            expected_code=200,
        )

        self.assertIn('name', response.data[0])

        self.assertEqual(len(response.data), Group.objects.count())

        # Check detail URL
        response = self.get(
            reverse('api-group-detail', kwargs={'pk': response.data[0]['pk']}),
            expected_code=200,
        )

        self.assertIn('name', response.data)
