"""API tests for various user / auth API endpoints."""

import datetime

from django.contrib.auth.models import Group, User
from django.urls import reverse

from InvenTree.unit_test import InvenTreeAPITestCase
from users.models import ApiToken
from users.ruleset import RULESET_NAMES, get_ruleset_models


class UserAPITests(InvenTreeAPITestCase):
    """Tests for user API endpoints."""

    def test_user_options(self):
        """Tests for the User OPTIONS request."""
        self.assignRole('admin.add')
        response = self.options(reverse('api-user-list'), expected_code=200)

        self.user.is_staff = True
        self.user.save()

        # User is a *staff* user with *admin* role, so can POST against this endpoint
        self.assertIn('POST', response.data['actions'])

        fields = response.data['actions']['GET']

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
        url = reverse('api-user-list')
        response = self.get(url, expected_code=200)

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

        data = {
            'username': 'test',
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'aa@example.org',
        }

        # Test create user - requires staff access with 'admin' role
        response = self.post(url, data=data, expected_code=403)
        self.assertIn(
            'You do not have permission to perform this action.', str(response.data)
        )

        # Try again with "staff" access
        self.user.is_staff = True
        self.user.save()

        # Try again - should fail still, as user does not have "admin" role
        response = self.post(url, data=data, expected_code=403)

        # Assign the "admin" role to the user
        self.assignRole('admin.view')

        # Fail again - user does not have "add" permission against the "admin" role
        response = self.post(url, data=data, expected_code=403)

        self.assignRole('admin.add')

        response = self.post(url, data=data, expected_code=201)

        self.assertEqual(response.data['username'], 'test')
        self.assertEqual(response.data['first_name'], 'Test')
        self.assertEqual(response.data['last_name'], 'User')
        self.assertEqual(response.data['is_staff'], False)
        self.assertEqual(response.data['is_superuser'], False)
        self.assertEqual(response.data['is_active'], True)

        # Try to adjust the 'is_superuser' field
        # Only a "superuser" can set this field
        response = self.post(
            url,
            data={**data, 'username': 'Superuser', 'is_superuser': True},
            expected_code=403,
        )

        self.assertIn('Only a superuser can adjust this field', str(response.data))

    def test_user_detail(self):
        """Test the UserDetail API endpoint."""
        user = User.objects.first()
        url = reverse('api-user-detail', kwargs={'pk': user.pk})

        user.is_staff = False
        user.save()

        # Any authenticated user can access the user detail endpoint
        self.get(url, expected_code=200)

        # Let's try to update the user
        data = {'is_active': False, 'is_staff': False}

        self.patch(url, data=data, expected_code=403)

        # But, what if we have the "admin" role?
        self.assignRole('admin.change')

        # Still cannot - we are not staff
        self.patch(url, data=data, expected_code=403)

        self.user.is_staff = True
        self.user.save()

        self.patch(url, data=data, expected_code=200)

        # Try again, but logged out - expect no access to the endpoint
        self.logout()
        self.get(url, expected_code=401)

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

    def test_login_redirect(self):
        """Test login redirect endpoint."""
        response = self.get(reverse('api-login-redirect'), expected_code=302)
        self.assertEqual(response.url, '/web/logged-in/')

    def test_user_roles(self):
        """Test the user 'roles' API endpoint."""
        url = reverse('api-user-roles')

        response = self.get(url, expected_code=200)
        data = response.data

        # User has no 'permissions' yet
        self.assertEqual(len(data['permissions']), 0)
        self.assertEqual(len(data['roles']), len(RULESET_NAMES))

        # assign the 'purchase_order.add' role to the test group
        self.assignRole('purchase_order.add')

        response = self.get(url, expected_code=200)
        data = response.data

        # Expected number of permissions
        perms = get_ruleset_models()['purchase_order']
        self.assertEqual(len(data['permissions']), len(perms))

        for P in data['permissions'].values():
            self.assertIn('add', P)
            self.assertIn('change', P)
            self.assertIn('view', P)

            self.assertNotIn('delete', P)

        # assign a different role - check stacking
        self.assignRole('build.view')

        response = self.get(url, expected_code=200)
        data = response.data
        build_perms = get_ruleset_models()['build']

        self.assertEqual(len(data['permissions']), len(perms) + len(build_perms))


class SuperuserAPITests(InvenTreeAPITestCase):
    """Tests for user API endpoints that require superuser rights."""

    fixtures = ['users']
    superuser = True

    def test_user_password_set(self):
        """Test the set-password/ endpoint."""
        user = User.objects.get(pk=2)
        url = reverse('api-user-set-password', kwargs={'pk': user.pk})

        # to simple password
        resp = self.put(url, {'password': 1}, expected_code=400)
        self.assertContains(resp, 'This password is too short', status_code=400)

        # now with overwerite
        resp = self.put(
            url, {'password': 1, 'override_warning': True}, expected_code=200
        )
        self.assertEqual(resp.data, {})

        # complex enough pwd
        resp = self.put(url, {'password': 'inventree'}, expected_code=200)
        self.assertEqual(resp.data, {})


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
