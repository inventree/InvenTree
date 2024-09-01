"""API tests for various user / auth API endpoints."""

import datetime

from django.contrib.auth.models import Group, User
from django.urls import reverse

from InvenTree.unit_test import InvenTreeAPITestCase
from users.models import ApiToken


class UserAPITests(InvenTreeAPITestCase):
    """Tests for user API endpoints."""

    def test_user_options(self):
        """Tests for the User OPTIONS request."""
        self.assignRole('admin.add')
        response = self.options(reverse('api-user-list'), expected_code=200)

        fields = response.data['actions']['POST']

        # Check some of the field values
        self.assertEqual(fields['username']['label'], 'Username')

        self.assertEqual(fields['email']['label'], 'Email')
        self.assertEqual(fields['email']['help_text'], 'Email address of the user')

        self.assertEqual(fields['is_active']['label'], 'Active')
        self.assertEqual(
            fields['is_active']['help_text'], 'Is this user account active'
        )

        self.assertEqual(fields['is_staff']['label'], 'Staff')
        self.assertEqual(
            fields['is_staff']['help_text'], 'Does this user have staff permissions'
        )

    def test_user_api(self):
        """Tests for User API endpoints."""
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
        """Tests for the Group API endpoints."""
        response = self.get(reverse('api-group-list'), expected_code=200)

        self.assertIn('name', response.data[0])

        self.assertEqual(len(response.data), Group.objects.count())

        # Check detail URL
        pk = response.data[0]['pk']
        response = self.get(
            reverse('api-group-detail', kwargs={'pk': pk}), expected_code=200
        )
        self.assertIn('name', response.data)
        self.assertNotIn('permissions', response.data)

        # Check more detailed URL
        response = self.get(
            reverse('api-group-detail', kwargs={'pk': pk}),
            data={'permission_detail': True},
            expected_code=200,
        )
        self.assertIn('name', response.data)
        self.assertIn('permissions', response.data)

    def test_logout(self):
        """Test api logout endpoint."""
        token_key = self.get(url=reverse('api-token')).data['token']
        self.client.logout()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token_key)

        self.post(reverse('api-logout'), expected_code=200)
        self.get(reverse('api-token'), expected_code=401)

    def test_login_redirect(self):
        """Test login redirect endpoint."""
        response = self.get(reverse('api-login-redirect'), expected_code=302)
        self.assertEqual(response.url, '/index/')

        # PUI
        self.put(reverse('api-ui-preference'), {'preferred_method': 'pui'})
        response = self.get(reverse('api-login-redirect'), expected_code=302)
        self.assertEqual(response.url, '/platform/logged-in/')


class UserTokenTests(InvenTreeAPITestCase):
    """Tests for user token functionality."""

    def test_token_generation(self):
        """Test user token generation."""
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
        """Test user token authentication."""
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

    def test_buildin_token(self):
        """Test the built-in token authentication."""
        response = self.post(
            reverse('rest_login'),
            {'username': self.username, 'password': self.password},
            expected_code=200,
        )
        self.assertIn('key', response.data)
        self.assertTrue(response.data['key'].startswith('inv-'))

    def test_token_api(self):
        """Test the token API."""
        url = reverse('api-token-list')
        response = self.get(url, expected_code=200)
        self.assertEqual(response.data, [])

        # Get token
        response = self.get(reverse('api-token'), expected_code=200)
        self.assertIn('token', response.data)

        # Now there should be one token
        response = self.get(url, expected_code=200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['active'], True)
        self.assertEqual(response.data[0]['revoked'], False)
        self.assertEqual(response.data[0]['in_use'], False)
        expected_day = str(
            datetime.datetime.now().date() + datetime.timedelta(days=365)
        )
        self.assertEqual(response.data[0]['expiry'], expected_day)

        # Destroy token
        self.delete(
            reverse('api-token-detail', kwargs={'pk': response.data[0]['id']}),
            expected_code=204,
        )

        # Get token without auth (should fail)
        self.client.logout()
        self.get(reverse('api-token'), expected_code=401)
