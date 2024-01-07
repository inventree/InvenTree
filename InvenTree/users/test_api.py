"""API tests for various user / auth API endpoints"""

import datetime

from django.contrib.auth.models import Group, User
from django.urls import reverse

from InvenTree.unit_test import InvenTreeAPITestCase
from users.models import ApiToken


class UserAPITests(InvenTreeAPITestCase):
    """Tests for user API endpoints"""

    def test_user_api(self):
        """Tests for User API endpoints"""
        response = self.get(reverse('api-user-list'), expected_code=200)

        # Check the correct number of results was returned
        self.assertEqual(len(response.data), User.objects.count())

        for key in ['username', 'pk', 'email']:
            self.assertIn(key, response.data[0])

        # Check detail URL
        pk = response.data[0]['pk']

        response = self.get(
            reverse('api-user-detail', kwargs={'pk': pk}), expected_code=200
        )

        self.assertIn('pk', response.data)
        self.assertIn('username', response.data)

    def test_group_api(self):
        """Tests for the Group API endpoints"""
        response = self.get(reverse('api-group-list'), expected_code=200)

        self.assertIn('name', response.data[0])

        self.assertEqual(len(response.data), Group.objects.count())

        # Check detail URL
        response = self.get(
            reverse('api-group-detail', kwargs={'pk': response.data[0]['pk']}),
            expected_code=200,
        )

        self.assertIn('name', response.data)


class UserTokenTests(InvenTreeAPITestCase):
    """Tests for user token functionality"""

    def test_token_generation(self):
        """Test user token generation"""

        url = reverse('api-token')

        self.assertEqual(ApiToken.objects.count(), 0)

        # Generate multiple tokens with different names
        for name in ['cat', 'dog', 'biscuit']:
            data = self.get(url, data={'name': name}, expected_code=200).data

            self.assertTrue(data['token'].startswith('inv-'))
            self.assertEqual(data['name'], name)

        # Check that the tokens were created
        self.assertEqual(ApiToken.objects.count(), 3)

        # If we re-generate a token, the value changes
        token = ApiToken.objects.filter(name='cat').first()

        # Request the token with the same name
        data = self.get(url, data={'name': 'cat'}, expected_code=200).data

        self.assertEqual(data['token'], token.key)

        self.assertEqual(ApiToken.objects.count(), 3)

        # Revoke the token, and then request again
        token.revoked = True
        token.save()

        data = self.get(url, data={'name': 'cat'}, expected_code=200).data

        self.assertNotEqual(data['token'], token.key)

        # A new token has been generated
        self.assertEqual(ApiToken.objects.count(), 4)

        # Test with a really long name
        data = self.get(url, data={'name': 'cat' * 100}, expected_code=200).data

        # Name should be truncated
        self.assertEqual(len(data['name']), 100)

        token.refresh_from_db()

        # Check that the metadata has been updated
        keys = [
            'user_agent',
            'remote_addr',
            'remote_host',
            'remote_user',
            'server_name',
            'server_port',
        ]

        for k in keys:
            self.assertIn(k, token.metadata)

    def test_token_auth(self):
        """Test user token authentication"""

        # Create a new token
        token_key = self.get(
            url=reverse('api-token'), data={'name': 'test'}, expected_code=200
        ).data['token']

        # Check that we can use the token to authenticate
        self.client.logout()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token_key)

        me = reverse('api-user-me')

        response = self.client.get(me, expected_code=200)

        # Grab the token, and update
        token = ApiToken.objects.first()
        self.assertEqual(token.key, token_key)
        self.assertIsNotNone(token.last_seen)

        # Revoke the token
        token.revoked = True
        token.save()

        self.assertFalse(token.active)

        response = self.client.get(me, expected_code=401)
        self.assertIn('Token has been revoked', str(response.data))

        # Expire the token
        token.revoked = False
        token.expiry = datetime.datetime.now().date() - datetime.timedelta(days=10)
        token.save()

        self.assertTrue(token.expired)
        self.assertFalse(token.active)

        response = self.client.get(me, expected_code=401)
        self.assertIn('Token has expired', str(response.data))

        # Re-enable the token
        token.revoked = False
        token.expiry = datetime.datetime.now().date() + datetime.timedelta(days=10)
        token.save()

        self.client.get(me, expected_code=200)
