"""API tests for various user / auth API endpoints."""

import datetime
import time
from unittest import mock

from django.contrib.auth.models import Group, User
from django.urls import reverse

from allauth.account.internal.flows.login import (
    _AUTHENTICATION_METHODS_USER_SESSION_KEY,
    AUTHENTICATION_METHODS_SESSION_KEY,
)
from allauth.account.internal.userkit import user_id_to_str
from allauth.account.models import EmailAddress
from allauth.mfa.models import Authenticator

import InvenTree.helpers
from common.models import NotificationMessage
from InvenTree.unit_test import InvenTreeAPITestCase
from users.models import ApiToken, default_token
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

        self.assertEqual(fields['is_staff']['label'], 'Administrator')
        self.assertEqual(
            fields['is_staff']['help_text'],
            'Does this user have administrative permissions',
        )

    def test_api_url(self):
        """Test the 'api_url' attribute in related API endpoints.

        Ref: https://github.com/inventree/InvenTree/pull/10182
        """
        self.user.is_superuser = True
        self.user.save()

        url = reverse('api-build-list')
        response = self.options(url)
        actions = response.data['actions']['POST']

        issued_by = actions['issued_by']
        self.assertTrue(issued_by['read_only'])

        project_code = actions['project_code']
        self.assertFalse(project_code['read_only'])
        self.assertEqual(project_code['type'], 'related field')
        self.assertEqual(project_code['model'], 'projectcode')
        self.assertEqual(project_code['api_url'], reverse('api-project-code-list'))
        self.assertEqual(project_code['pk_field'], 'pk')

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
        self.assertTrue(
            EmailAddress.objects.filter(
                user__username=data['username'], email=data['email'], primary=True
            ).exists()
        )

        # A second user with the same email address (any case) is rejected
        response = self.post(
            url,
            data={**data, 'username': 'test2', 'email': 'AA@example.org'},
            expected_code=400,
        )
        self.assertIn('email', response.data)

        # Try to adjust the 'is_superuser' field
        # Only a "superuser" can set this field
        response = self.post(
            url,
            data={
                **data,
                'username': 'Superuser',
                'email': 'su@example.org',
                'is_superuser': True,
            },
            expected_code=403,
        )

        self.assertIn('Only a superuser can adjust this field', str(response.data))

        # Try again, but with superuser access
        self.user.is_superuser = True
        self.user.save()

        response = self.post(
            url,
            data={
                **data,
                'username': 'Superuser',
                'email': 'su@example.org',
                'is_superuser': True,
            },
            expected_code=201,
        )

        self.assertEqual(response.data['username'], 'Superuser')
        self.assertEqual(response.data['is_superuser'], True)

    def test_user_create_with_groups(self):
        """Test that groups can be assigned when creating a new user via the API."""
        url = reverse('api-user-list')

        group_a = Group.objects.create(name='Group A')
        group_b = Group.objects.create(name='Group B')

        self.user.is_staff = True
        self.user.save()
        self.assignRole('admin.add')

        data = {
            'username': 'grouped',
            'first_name': 'Grouped',
            'last_name': 'User',
            'email': 'grouped@example.org',
            'group_ids': [group_a.pk, group_b.pk],
        }

        response = self.post(url, data=data, expected_code=201)

        self.assertEqual(response.data['username'], 'grouped')

        group_names = {g['name'] for g in response.data['groups']}
        self.assertEqual(group_names, {'Group A', 'Group B'})

        user = User.objects.get(username='grouped')
        self.assertEqual(set(user.groups.all()), {group_a, group_b})

        # Creating a user without specifying groups must still work
        response = self.post(
            url,
            data={
                **data,
                'username': 'ungrouped',
                'email': 'ungrouped@example.org',
                'group_ids': [],
            },
            expected_code=201,
        )
        self.assertEqual(response.data['groups'], [])

    def test_user_detail(self):
        """Test the UserDetail API endpoint."""
        user = User.objects.first()
        assert user

        url = reverse('api-user-detail', kwargs={'pk': user.pk})

        user.is_staff = False
        user.save()

        # Any authenticated user can access the user detail endpoint
        self.get(url, expected_code=200)

        # Let's try to update the user
        data = {'is_active': True, 'is_staff': False}

        self.patch(url, data=data, expected_code=403)

        # But, what if we have the "admin" role?
        self.assignRole('admin.change')

        # Still cannot - we are not staff
        self.patch(url, data=data, expected_code=403)

        self.user.is_staff = True
        self.user.save()

        self.patch(url, data=data, expected_code=200)

        # Try to change the "is_superuser" field - only a superuser can do this
        data['is_superuser'] = True
        response = self.patch(url, data=data, expected_code=403)

        self.assertIn(
            'You do not have permission to perform this action', str(response.data)
        )

        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save()

        for val in [True, False]:
            data['is_staff'] = True
            data['is_superuser'] = val

            response = self.patch(url, data=data, expected_code=200)
            self.assertEqual(response.data['is_superuser'], val)
            self.assertEqual(response.data['is_staff'], True)

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
        self.assertIn('roles', response.data)
        self.assertIn('permissions', response.data)

        self.assertGreater(len(response.data['roles']), 0)

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

    def test_me_endpoint(self):
        """Test against the users /me/ endpoint."""
        url = reverse('api-user-me')

        # Test endpoint options
        response = self.options(url, expected_code=200)

        # Check that particular fields are present, and have the correct attributes
        fields = response.data['actions']['PUT']

        for name in [
            'pk',
            'username',
            'email',
            'groups',
            'is_active',
            'is_staff',
            'is_superuser',
        ]:
            self.assertIn(name, fields)

        for name in ['is_active', 'is_staff', 'is_superuser']:
            self.assertTrue(fields[name]['read_only'])

        # Perform a GET request against the endpoint
        response = self.get(url, expected_code=200)

        for field in [
            'pk',
            'username',
            'email',
            'is_active',
            'is_staff',
            'is_superuser',
        ]:
            self.assertIn(field, response.data)

        # Username and email are read-only
        for name in ['username', 'email']:
            self.assertTrue(fields[name]['read_only'])

        # Users can change their own name
        response = self.patch(
            url, data={'first_name': 'Henry', 'last_name': 'Sally'}, expected_code=200
        )
        self.assertEqual(response.data['first_name'], 'Henry')
        self.assertEqual(response.data['last_name'], 'Sally')

        # Defined starting point for the user
        for v in [True, False]:
            self.user.is_staff = v
            self.user.is_superuser = v
            self.user.save()

            for key in ['is_staff', 'is_superuser']:
                for val in [True, False]:
                    response = self.patch(url, data={key: val}, expected_code=200)

                    # Check that the field was *NOT CHANGED*
                    self.assertEqual(response.data[key], v)

        # Ensure we cannot change the "is_active" field either
        response = self.patch(url, data={'is_active': False}, expected_code=200)
        self.assertEqual(response.data['is_active'], True)

        self.user.is_active = False
        self.user.save()

        # User cannot fetch their own details if they are not active
        response = self.get(url, expected_code=401)

    def test_me_endpoint_identity_fields_read_only(self):
        """A user must not be able to change their own username or email via '/api/user/me/'.

        - Setting another user's email breaks email-based flows (login link) for that user
        - Changing email bypasses allauth email verification
        - Claiming an unused username hijacks a future LDAP / remote-user login
        """
        url = reverse('api-user-me')

        victim = User.objects.create_user(
            username='victim', email='victim@example.com', password='password'
        )

        original_username = self.user.username
        original_email = self.user.email

        for data in [
            {'email': victim.email},
            {'email': 'unverified@example.com'},
            {'username': 'not_yet_logged_in'},
            {'username': 'not_yet_logged_in', 'email': 'other@example.com'},
        ]:
            # Read-only fields are silently ignored
            response = self.patch(url, data=data, expected_code=200)
            self.assertEqual(response.data['username'], original_username)
            self.assertEqual(response.data['email'], original_email)

            self.user.refresh_from_db()
            self.assertEqual(self.user.username, original_username)
            self.assertEqual(self.user.email, original_email)

        # The victim's email must still be unique
        self.assertEqual(User.objects.filter(email__iexact=victim.email).count(), 1)
        self.assertFalse(User.objects.filter(username='not_yet_logged_in').exists())

        # Full update (PUT) must not change the fields either
        response = self.put(
            url,
            data={
                'username': 'not_yet_logged_in',
                'email': victim.email,
                'first_name': 'A',
                'last_name': 'B',
            },
            expected_code=200,
        )
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, original_username)
        self.assertEqual(self.user.email, original_email)
        self.assertEqual(self.user.first_name, 'A')

    def test_admin_can_edit_user_identity(self):
        """A staff user with the 'admin' role can still change another user's username and email."""
        other = User.objects.create_user(
            username='other', email='other@example.com', password='password'
        )
        url = reverse('api-user-detail', kwargs={'pk': other.pk})

        # Without staff + admin role, no write access
        self.patch(url, data={'username': 'renamed'}, expected_code=403)

        self.assignRole('admin.change')
        self.user.is_staff = True
        self.user.save()

        response = self.patch(
            url,
            data={'username': 'renamed', 'email': 'renamed@example.com'},
            expected_code=200,
        )
        self.assertEqual(response.data['username'], 'renamed')
        self.assertEqual(response.data['email'], 'renamed@example.com')

        other.refresh_from_db()
        self.assertEqual(other.username, 'renamed')
        self.assertEqual(other.email, 'renamed@example.com')

    def test_admin_cannot_set_duplicate_email(self):
        """An admin cannot assign an email address which is already in use by another user.

        Email-based flows (password reset, login link) fail silently for
        a user whose email address is shared with another account.
        """
        self.assignRole('admin.change')
        self.assignRole('admin.add')
        self.user.is_staff = True
        self.user.save()

        first = User.objects.create_user(
            username='first', email='first@example.com', password='password'
        )
        second = User.objects.create_user(
            username='second', email='second@example.com', password='password'
        )

        # An address known only to allauth (e.g. a secondary address) is also taken
        EmailAddress.objects.create(
            user=first, email='first.alt@example.com', verified=True
        )

        url = reverse('api-user-detail', kwargs={'pk': second.pk})

        for email in [
            'first@example.com',
            'FIRST@Example.com',  # Case-insensitive match
            'first.alt@example.com',
        ]:
            response = self.patch(url, data={'email': email}, expected_code=400)
            self.assertIn(
                'A user with this email address already exists',
                str(response.data['email']),
            )

        second.refresh_from_db()
        self.assertEqual(second.email, 'second@example.com')

        # Re-submitting the user's own address (e.g. a full PUT from the edit form) is fine
        response = self.patch(
            url,
            data={'email': 'SECOND@example.com', 'first_name': 'Sec'},
            expected_code=200,
        )
        self.assertEqual(response.data['first_name'], 'Sec')

        # As is a new, unused address, or a blank one
        for email in ['new@example.com', '']:
            response = self.patch(url, data={'email': email}, expected_code=200)
            self.assertEqual(response.data['email'], email)

        # User creation also rejects duplicates
        response = self.post(
            reverse('api-user-list'),
            data={'username': 'third', 'email': 'First@example.com'},
            expected_code=400,
        )
        self.assertIn('email', response.data)
        self.assertFalse(User.objects.filter(username='third').exists())

    def test_me_endpoint_delete_is_blocked(self):
        """A user must not be able to delete their own account via '/api/user/me/'."""
        url = reverse('api-user-me')
        pk = self.user.pk

        self.delete(url, expected_code=405)

        self.assertTrue(User.objects.filter(pk=pk).exists())


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

        # now with overwrite
        resp = self.put(
            url, {'password': 1, 'override_warning': True}, expected_code=200
        )
        self.assertEqual(resp.data, {})

        # complex enough pwd
        resp = self.put(url, {'password': 'inventree'}, expected_code=200)
        self.assertEqual(resp.data, {})


class UserTokenTests(InvenTreeAPITestCase):
    """Tests for user token functionality."""

    fixtures = ['users']

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
        assert token

        # Request the token with the same name
        data = self.get(url, data={'name': 'cat'}, expected_code=200).data

        token.refresh_from_db()
        self.assertNotEqual(data['token'], token.key)
        self.assertTrue(data['token'].startswith('inv-2-'))
        self.assertTrue(token.revoked)

        self.assertEqual(ApiToken.objects.count(), 4)

        # Request again, which issues another replacement token
        data = self.get(url, data={'name': 'cat'}, expected_code=200).data

        self.assertNotEqual(data['token'], token.key)

        # A new token has been generated
        self.assertEqual(ApiToken.objects.count(), 5)

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

    def test_token_issued_notification(self):
        """A notification is sent whenever a token is issued, with a warning if email is unavailable."""
        self.ensurePluginsLoaded()

        url = reverse('api-token')
        category = 'users.api_token_issued'

        self.assertEqual(
            NotificationMessage.objects.filter(category=category).count(), 0
        )

        # No email configured -> warning is returned, UI notification is still created
        with self.assertLogs('inventree', level='WARNING') as logs:
            data = self.get(url, data={'name': 'notify'}, expected_code=200).data

        self.assertIn('warning', data)
        self.assertIn('Email is not configured', data['warning'])
        self.assertTrue(any('INVE-W7' in msg for msg in logs.output))

        msgs = NotificationMessage.objects.filter(category=category, user=self.user)
        self.assertEqual(msgs.count(), 1)
        self.assertIn("'notify'", msgs.first().message)

        # Re-issuing a token with the same name sends another notification
        self.get(url, data={'name': 'notify'}, expected_code=200)
        self.assertEqual(msgs.count(), 2)

        # Email configured -> no warning
        with self.settings(EMAIL_HOST='localhost', TESTING_BYPASS_MAILCHECK=True):
            data = self.get(url, data={'name': 'mailed'}, expected_code=200).data
        self.assertNotIn('warning', data)

        # Superuser issuing a token for another user notifies that user
        self.user.is_superuser = True
        self.user.save()
        other = User.objects.exclude(pk=self.user.pk).first()

        data = self.post(
            reverse('api-token-list'),
            data={'name': 'for-other', 'user': other.pk},
            expected_code=201,
        ).data
        self.assertIn('warning', data)

        msg = NotificationMessage.objects.get(category=category, user=other)
        self.assertIn(self.user.username, msg.message)

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
        assert token
        self.assertEqual(token.key, ApiToken.split_token(token_key)[0])
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

    def test_token_last_seen_no_clobber(self):
        """Regression test: updating token.last_seen must overwrite other fields.

        Simulates a revoke landing in the window between this request's token
        lookup and its last_seen save, by revoking the token (directly against
        the database) from inside a patched ApiToken.save().
        """
        token_key = self.get(
            url=reverse('api-token'), data={'name': 'race'}, expected_code=200
        ).data['token']

        token = ApiToken.objects.get(key=ApiToken.split_token(token_key)[0])

        # Force last_seen to be 'stale' so the auth backend attempts to update it
        ApiToken.objects.filter(pk=token.pk).update(
            last_seen=datetime.date.today() - datetime.timedelta(days=1)
        )

        original_save = ApiToken.save

        def revoke_then_save(self, *args, **kwargs):
            # Simulate a concurrent request revoking this token, via a direct
            # DB write, right before this request's last_seen save lands
            ApiToken.objects.filter(pk=self.pk).update(revoked=True)
            return original_save(self, *args, **kwargs)

        self.client.logout()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token_key)

        with mock.patch.object(ApiToken, 'save', revoke_then_save):
            self.client.get(reverse('api-user-me'), expected_code=200)

        token.refresh_from_db()
        self.assertTrue(
            token.revoked,
            'Concurrent revoke must not be clobbered by the last_seen update',
        )

    def test_token_api(self):
        """Test the token API."""
        url = reverse('api-token-list')
        response = self.get(url, expected_code=200)
        self.assertEqual(response.data, [])

        # Get token
        response = self.get(reverse('api-token'), expected_code=200)
        self.assertIn('token', response.data)
        raw_token = response.data['token']

        self.client.logout()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {raw_token}')

        # Now there should be one token
        response = self.get(url, expected_code=200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['active'], True)
        self.assertEqual(response.data[0]['revoked'], False)
        self.assertEqual(response.data[0]['in_use'], True)
        self.assertEqual(response.data[0]['issued_by'], self.user.pk)
        self.assertIsNone(response.data[0]['revoked_by'])
        self.assertIsNone(response.data[0]['revocation_reason'])
        expected_day = str(
            datetime.datetime.now().date() + datetime.timedelta(days=365)
        )
        self.assertEqual(response.data[0]['expiry'], expected_day)

        # Destroy token
        token_id = response.data[0]['id']
        self.delete(
            reverse('api-token-detail', kwargs={'pk': token_id}),
            data={'revocation_reason': 'No longer needed'},
            expected_code=204,
        )

        token = ApiToken.objects.get(pk=token_id)
        self.assertTrue(token.revoked)
        self.assertEqual(token.revoked_by, self.user)
        self.assertEqual(token.revocation_reason, 'No longer needed')

        # Revoking again must not overwrite the original revocation record
        other_user = User.objects.create_user(username='other-revoker', password='x')
        other_user.is_superuser = True
        other_user.save()
        self.client.force_authenticate(user=other_user)
        self.delete(
            reverse('api-token-detail', kwargs={'pk': token_id}) + '?all_users=true',
            data={'revocation_reason': 'Overwritten reason'},
            expected_code=204,
        )
        self.client.force_authenticate(user=None)

        token.refresh_from_db()
        self.assertTrue(token.revoked)
        self.assertEqual(token.revoked_by, self.user)
        self.assertEqual(token.revocation_reason, 'No longer needed')

        # Get token without auth (should fail)
        self.client.logout()
        self.get(reverse('api-token'), expected_code=401)

    def test_token_security(self):
        """Test that token generation is only available to users with the correct permissions."""
        url = reverse('api-token-list')

        # Try to generate a token for a different user (should fail)
        response = self.post(url, data={'name': 'test', 'user': 1}, expected_code=400)
        self.assertIn(
            'Only a superuser can create a token for another user', str(response.data)
        )

        # there should be no tokens created
        self.assertEqual(ApiToken.objects.count(), 0)

        # now with superuser permissions
        self.user.is_superuser = True
        self.user.save()

        response = self.post(url, data={'name': 'test', 'user': 1}, expected_code=201)
        self.assertIn('token', response.data)

        self.assertEqual(ApiToken.objects.count(), 1)

    def test_token_create_fields(self):
        """Test that protected token fields cannot be set when creating a token."""
        url = reverse('api-token-list')
        today = InvenTree.helpers.current_date()
        other = User.objects.create_user(username='other', password='password')

        # Expiry date must be within the allowed token lifetime
        for expiry in [today - datetime.timedelta(days=1), datetime.date(9999, 12, 31)]:
            response = self.post(
                url, data={'name': 'test', 'expiry': str(expiry)}, expected_code=400
            )
            self.assertIn('expiry', response.data)

        for expiry in [today, today + datetime.timedelta(days=365)]:
            response = self.post(
                url,
                data={'name': f'test-{expiry}', 'expiry': str(expiry)},
                expected_code=201,
            )
            self.assertEqual(response.data['expiry'], str(expiry))

        # Read-only fields are ignored
        response = self.post(
            url,
            data={
                'name': 'protected',
                'revoked': True,
                'revoked_by': other.pk,
                'issued_by': other.pk,
                'revocation_reason': 'forged',
                'token_version': 1,
                'last_seen': str(today),
            },
            expected_code=201,
        )

        token = ApiToken.objects.get(pk=response.data['id'])
        self.assertFalse(token.revoked)
        self.assertIsNone(token.revoked_by)
        self.assertEqual(token.issued_by, self.user)
        self.assertIsNone(token.revocation_reason)
        self.assertEqual(token.token_version, 2)
        self.assertIsNone(token.last_seen)

    def set_auth_time(self, age: float):
        """Record an allauth authentication event in the test client session.

        Arguments:
            age: How many seconds ago the authentication occurred
        """
        session = self.client.session
        session[AUTHENTICATION_METHODS_SESSION_KEY] = [
            {
                'method': 'mfa',
                'type': 'totp',
                'reauthenticated': True,
                'at': time.time() - age,
            }
        ]
        session[_AUTHENTICATION_METHODS_USER_SESSION_KEY] = user_id_to_str(self.user)
        session.save()

    def test_token_mfa_reauthentication(self):
        """Test that MFA users must have recently authenticated to mint a token.

        Every endpoint which issues a new API token must enforce this check.
        Otherwise an aged (or stolen) session could be converted into a
        long-lived API token without the second factor.
        """
        Authenticator.objects.create(
            user=self.user, type=Authenticator.Type.TOTP, data={'secret': 'abc'}
        )

        n_tokens = ApiToken.objects.filter(user=self.user).count()

        endpoints = [
            lambda name: self.get(
                reverse('api-token'), data={'name': name}, expected_code=None
            ),
            lambda name: self.get(
                reverse('api-token_legacy'), data={'name': name}, expected_code=None
            ),
            lambda name: self.post(
                reverse('api-token-list'), data={'name': name}, expected_code=None
            ),
        ]

        # No authentication record, or an aged one: reauthentication is required
        for age in [None, 600]:
            if age is not None:
                self.set_auth_time(age)

            for idx, mint in enumerate(endpoints):
                response = mint(f'mfa-{age}-{idx}')
                self.assertEqual(response.status_code, 401, response.data)
                self.assertEqual(response.data['id'], 'reauthentication_required')

                flows = [flow['id'] for flow in response.data['data']['flows']]
                self.assertIn('mfa_reauthenticate', flows)

        # No tokens were issued
        self.assertEqual(ApiToken.objects.filter(user=self.user).count(), n_tokens)

        # After recent (re)authentication, tokens can be issued
        self.set_auth_time(10)

        self.get(reverse('api-token'), data={'name': 'mfa-ok-0'}, expected_code=200)
        response = self.post(
            reverse('api-token-list'), data={'name': 'mfa-ok-1'}, expected_code=201
        )
        self.assertIn('token', response.data)

        self.assertEqual(ApiToken.objects.filter(user=self.user).count(), n_tokens + 2)

    def test_token_v1(self):
        """Test that v1 API tokens still work."""
        # Create a v1 token via model - this is NOT recommended; use v2 tokens
        token = ApiToken.objects.create(
            user=self.user,
            key=default_token(),
            token_version=1,
            expiry=datetime.datetime.now() + datetime.timedelta(days=365),
        )
        token_key = token.key
        self.assertTrue(token_key.startswith('inv-'))

        # Check match and validate functions
        self.assertTrue(token.match(token_key))
        self.assertTrue(token.validate(token_key))

        # test api access with token
        self.logout()
        # false test - ensure that without the token, access is denied
        self.get(reverse('api-user-me'), expected_code=401)

        # valid test
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token_key}')
        response = self.get(reverse('api-user-me'), expected_code=200)
        self.assertEqual(response.data['username'], self.user.username)

        # check if info view also works
        response_data = self.get(
            reverse('api-inventree-info'), expected_code=200
        ).json()
        # staff users are allowed to see the database field
        self.assertIn('database', response_data)
        self.assertIsNotNone(response_data.get('database'))


class GroupDetailTests(InvenTreeAPITestCase):
    """Tests for the GroupDetail API endpoint."""

    fixtures = ['users']

    def test_group_list(self):
        """Test the GroupDetail API endpoint."""
        url = reverse('api-group-detail', kwargs={'pk': 1})

        response = self.get(url, {'user_detail': 'true'}, expected_code=200)
        self.assertIn('users', response.data)

        response = self.get(url, {'role_detail': 'true'}, expected_code=200)
        self.assertIn('roles', response.data)

        response = self.get(url, {'permission_detail': 'true'}, expected_code=200)
        self.assertIn('permissions', response.data)

        response = self.get(url, {'permission_detail': 'false'}, expected_code=200)
        self.assertNotIn('permissions', response.data)


class RuleSetPermissionTests(InvenTreeAPITestCase):
    """Tests for permission enforcement on the Group / RuleSet API endpoints.

    Regression tests for a privilege-escalation bug where a *staff* user
    (without the 'admin' role) was able to write to these endpoints - in
    particular, granting themselves 'admin' RuleSet permissions via the
    RuleSet API, despite not holding the 'admin' role themselves.
    """

    def test_group_write_requires_admin_role(self):
        """A staff-only user (without the 'admin' role) cannot write to the Group API."""
        url = reverse('api-group-detail', kwargs={'pk': self.group.pk})

        # Sanity check - the default test user is staff, but has no assigned roles
        self.assertTrue(self.user.is_staff)

        # Read access is still permitted
        self.get(url, expected_code=200)

        # Write access is rejected, as the user does not have the 'admin' role
        self.patch(url, {'name': 'renamed-group'}, expected_code=403)

        self.group.refresh_from_db()
        self.assertNotEqual(self.group.name, 'renamed-group')

        # Once the 'admin' role is granted, the write succeeds
        self.assignRole('admin.change')
        self.patch(url, {'name': 'renamed-group'}, expected_code=200)

        self.group.refresh_from_db()
        self.assertEqual(self.group.name, 'renamed-group')

    def test_ruleset_write_requires_admin_role(self):
        """A staff-only user cannot self-escalate permissions via the RuleSet API."""
        admin_ruleset = self.group.rule_sets.get(name='admin')
        url = reverse('api-ruleset-detail', kwargs={'pk': admin_ruleset.pk})

        # Sanity check - the default test user is staff, but has no assigned roles
        self.assertTrue(self.user.is_staff)
        self.assertFalse(admin_ruleset.can_change)

        # Read access is still permitted
        self.get(url, expected_code=200)

        # Attempt to self-escalate to full 'admin' ruleset permissions
        self.patch(
            url,
            {'can_view': True, 'can_add': True, 'can_change': True, 'can_delete': True},
            expected_code=403,
        )

        admin_ruleset.refresh_from_db()
        self.assertFalse(admin_ruleset.can_change)

        # Granting the 'admin' role directly (not via the API) allows the write
        self.assignRole('admin.change')
        self.patch(url, {'can_delete': True}, expected_code=200)

        admin_ruleset.refresh_from_db()
        self.assertTrue(admin_ruleset.can_delete)

    def test_non_staff_user_read_only(self):
        """A non-staff, non-admin authenticated user retains read-only access."""
        self.user.is_staff = False
        self.user.save()

        group_url = reverse('api-group-detail', kwargs={'pk': self.group.pk})
        ruleset_url = reverse(
            'api-ruleset-detail',
            kwargs={'pk': self.group.rule_sets.get(name='admin').pk},
        )

        self.get(group_url, expected_code=200)
        self.get(ruleset_url, expected_code=200)

        self.patch(group_url, {'name': 'renamed-group'}, expected_code=403)
        self.patch(ruleset_url, {'can_change': True}, expected_code=403)


class NewUserMfaOnboardingTests(InvenTreeAPITestCase):
    """Regression tests for onboarding admin-created users while MFA is enforced.

    Ref: https://github.com/inventree/InvenTree/issues/13238
    """

    NEW_PASSWORD = 'Corr3ct-Horse-Battery-Staple!'

    def setUp(self):
        """Allow the test user to create other users."""
        super().setUp()
        self.user.is_staff = True
        self.user.save()
        self.assignRole('admin.add')

    def create_user(self, username='newbie', email='newbie@example.org'):
        """Create a new user via the API, as an administrator would."""
        self.post(
            reverse('api-user-list'),
            data={
                'username': username,
                'first_name': 'New',
                'last_name': 'User',
                'email': email,
            },
            expected_code=201,
        )
        return User.objects.get(username=username)

    def reset_password(self, user):
        """Complete the headless password reset flow using a valid reset key."""
        from allauth.account.forms import default_token_generator
        from allauth.account.utils import user_pk_to_url_str

        key = f'{user_pk_to_url_str(user)}-{default_token_generator.make_token(user)}'

        response = self.client.post(
            reverse('browser:account:reset_password'),
            {'key': key, 'password': self.NEW_PASSWORD},
            content_type='application/json',
        )
        # Password reset does not log the user in -> 401 'unauthenticated' response
        self.assertIn(response.status_code, [200, 401], response.content)

    def get_totp(self):
        """Request a TOTP secret (first step of MFA registration)."""
        return self.client.get(reverse('browser:mfa:manage_totp'))

    def test_new_user_can_register_mfa(self):
        """A new user must be able to register MFA after resetting their password."""
        new_user = self.create_user()

        email = EmailAddress.objects.get(user=new_user)
        self.assertFalse(email.verified)
        self.assertFalse(new_user.has_usable_password())

        self.client.logout()

        with mock.patch.dict('os.environ', {'INVENTREE_LOGIN_ENFORCE_MFA': 'True'}):
            self.reset_password(new_user)

            # Completing the reset proves ownership of the mailbox
            email.refresh_from_db()
            self.assertTrue(email.verified)

            # The new user can now log in with their new password...
            response = self.client.post(
                reverse('browser:account:login'),
                {'username': 'newbie', 'password': self.NEW_PASSWORD},
                content_type='application/json',
            )
            self.assertEqual(response.status_code, 200, response.content)

            # ...is still blocked from the API until MFA is set up...
            response = self.client.get(reverse('api-part-list'))
            self.assertEqual(response.status_code, 401)
            self.assertEqual(response.json()['id'], 'mfa_register')

            # ...but can obtain a TOTP secret to register MFA
            response = self.get_totp()
            self.assertEqual(response.status_code, 404, response.content)
            self.assertIn('secret', response.json()['meta'])

    def test_unverified_email_blocks_mfa_registration(self):
        """Without a verified email, MFA registration is refused (the original bug)."""
        new_user = self.create_user()
        new_user.set_password(self.NEW_PASSWORD)
        new_user.save()

        self.client.logout()
        self.client.login(username='newbie', password=self.NEW_PASSWORD)

        response = self.get_totp()
        self.assertEqual(response.status_code, 409, response.content)
        self.assertEqual(response.json()['errors'][0]['code'], 'unverified_email')

    def test_reset_with_multiple_addresses(self):
        """Do not verify any address if the user has more than one."""
        new_user = self.create_user()
        EmailAddress.objects.create(
            user=new_user, email='other@example.org', primary=False, verified=False
        )

        self.client.logout()
        self.reset_password(new_user)

        self.assertFalse(
            EmailAddress.objects.filter(user=new_user, verified=True).exists()
        )

    def test_reset_with_mismatched_address(self):
        """Do not verify an address which does not match the account email."""
        new_user = self.create_user()
        EmailAddress.objects.filter(user=new_user).update(email='stale@example.org')

        self.client.logout()
        self.reset_password(new_user)

        self.assertFalse(
            EmailAddress.objects.filter(user=new_user, verified=True).exists()
        )
