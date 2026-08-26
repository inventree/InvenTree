"""Tests for the 'scim' app."""

import json

from django.contrib.auth.models import Group, User
from django.test import override_settings
from django.urls import reverse

from rest_framework.test import APIClient
from scim2_client.engines.httpx import SyncSCIMClient
from scim2_tester import check_server

from InvenTree.unit_test import InvenTreeAPITestCase
from scim.models import ScimConfiguration


class ScimConfigurationModelTests(InvenTreeAPITestCase):
    """Tests for the ScimConfiguration model."""

    def test_singleton(self):
        """Only a single configuration object can ever exist."""
        a = ScimConfiguration.load()
        b = ScimConfiguration.load()
        self.assertEqual(a.pk, b.pk)
        self.assertEqual(ScimConfiguration.objects.count(), 1)

    def test_generate_and_verify_secret(self):
        """A generated secret can be verified, but only while enabled."""
        config = ScimConfiguration.load()
        self.assertFalse(config.has_secret)

        secret = config.generate_secret()
        config.enabled = True
        config.save()

        self.assertTrue(config.has_secret)
        self.assertTrue(config.verify_secret(secret))
        self.assertFalse(config.verify_secret('not-the-secret'))
        self.assertFalse(config.verify_secret(''))

        # Disabling the endpoint rejects the (still valid) secret
        config.enabled = False
        config.save()
        self.assertFalse(config.verify_secret(secret))

    def test_rotate_invalidates_previous_secret(self):
        """Generating a new secret invalidates the previous one."""
        config = ScimConfiguration.load()
        first = config.generate_secret()
        config.enabled = True
        config.save()

        second = config.generate_secret()

        self.assertFalse(config.verify_secret(first))
        self.assertTrue(config.verify_secret(second))

    def test_revoke(self):
        """Revoking clears the secret and disables the endpoint."""
        config = ScimConfiguration.load()
        secret = config.generate_secret()
        config.enabled = True
        config.save()

        config.revoke()

        self.assertFalse(config.enabled)
        self.assertFalse(config.has_secret)
        self.assertFalse(config.verify_secret(secret))


class ScimAdminAPITests(InvenTreeAPITestCase):
    """Tests for the Admin Center facing SCIM configuration API."""

    def test_non_superuser_denied(self):
        """A non-superuser cannot view or manage the SCIM configuration."""
        self.get(reverse('api-scim-list'), expected_code=403)
        self.post(reverse('api-scim-generate'), expected_code=403)
        self.post(reverse('api-scim-disable'), expected_code=403)

    def test_generate_rotate_disable(self):
        """A superuser can generate, rotate and disable the SCIM secret."""
        self.user.is_superuser = True
        self.user.save()

        response = self.get(reverse('api-scim-list'), expected_code=200)
        self.assertFalse(response.data['enabled'])
        self.assertFalse(response.data['has_secret'])

        response = self.post(reverse('api-scim-generate'), expected_code=200)
        secret = response.data['secret']
        self.assertTrue(secret)

        config = ScimConfiguration.load()
        self.assertTrue(config.enabled)
        self.assertTrue(config.verify_secret(secret))

        response = self.post(reverse('api-scim-generate'), expected_code=200)
        new_secret = response.data['secret']
        self.assertNotEqual(secret, new_secret)

        self.post(reverse('api-scim-disable'), expected_code=200)
        config.refresh_from_db()
        self.assertFalse(config.enabled)
        self.assertFalse(config.has_secret)


class ScimProtocolTests(InvenTreeAPITestCase):
    """Tests for the SCIM 2.0 protocol endpoint."""

    def setUp(self):
        """Enable SCIM and generate a bearer secret for use in tests."""
        super().setUp()
        self.config = ScimConfiguration.load()
        self.secret = self.config.generate_secret()
        self.config.enabled = True
        self.config.save()

    def auth_header(self, secret=None):
        """Return the kwargs required to attach a SCIM bearer token to a request."""
        return {'HTTP_AUTHORIZATION': f'Bearer {secret or self.secret}'}

    def test_service_provider_config_is_public(self):
        """The discovery endpoints do not require authentication."""
        self.get(reverse('scim-service-provider-config'), expected_code=200)
        self.get(reverse('scim-resource-types'), expected_code=200)
        self.get(reverse('scim-schemas'), expected_code=200)

    def test_users_endpoint_requires_bearer_token(self):
        """The Users endpoint rejects requests without a valid bearer token."""
        self.get(reverse('scim-users'), expected_code=401)
        self.get(reverse('scim-users'), expected_code=401, **self.auth_header('wrong'))

    def test_filter_users_by_username(self):
        """Users can be filtered by an exact userName match."""
        response = self.get(
            reverse('scim-users'),
            data={'filter': f'userName eq "{self.user.username}"'},
            expected_code=200,
            **self.auth_header(),
        )
        self.assertEqual(response.data['totalResults'], 1)
        self.assertEqual(response.data['Resources'][0]['userName'], self.user.username)

        # wrong field name
        self.get(
            reverse('scim-users'),
            data={'filter': f'qbc eq "{self.user.username}"'},
            expected_code=400,
            **self.auth_header(),
        )

    def test_create_group_with_members(self):
        """A group can be provisioned with initial membership via SCIM."""
        payload = {
            'schemas': ['urn:ietf:params:scim:schemas:core:2.0:Group'],
            'displayName': 'scim-engineering',
            'members': [{'value': str(self.user.pk), 'type': 'User'}],
        }
        response = self.post(
            reverse('scim-groups'),
            data=payload,
            expected_code=201,
            **self.auth_header(),
        )
        group = Group.objects.get(pk=response.data['id'])
        self.assertEqual(group.name, 'scim-engineering')
        self.assertIn(self.user, group.user_set.all())

        # assign a user
        new_user = User.objects.create_user(username='scim-user', password='test')
        new_user.groups.add(group)
        self.assertIn(new_user, group.user_set.all())

        # remove membership via update
        payload['members'] = [{'value': str(self.user.pk), 'type': 'User'}]
        self.put(
            reverse('scim-group-detail', kwargs={'pk': group.pk}),
            data=payload,
            expected_code=200,
            **self.auth_header(),
        )
        group.refresh_from_db()
        self.assertNotIn(new_user, group.user_set.all())

        # and remove group via delete
        self.delete(
            reverse('scim-group-detail', kwargs={'pk': group.pk}),
            expected_code=204,
            **self.auth_header(),
        )
        self.assertFalse(Group.objects.filter(pk=group.pk).exists())

    @override_settings(
        SITE_URL='http://testserver', CSRF_TRUSTED_ORIGINS=['http://testserver']
    )
    def test_suite(self):
        """Run the SCIM 2.0 conformance test suite against the endpoint."""
        cls = PatchedApiClient(base_url='http://testserver/scim/v2')
        cls.logout()
        cls.credentials(HTTP_AUTHORIZATION=f'Bearer {self.secret}')

        scim_client = SyncSCIMClient(cls)
        ignore_tags = {
            'crud:read:attributes',  # 1: we do not have this attribute
            'patch:add',  # 2: we do not map these attributes to the User model right now
            'patch:remove',  # 2:see above
            'patch:replace',  # 2: see above
            'check_replace',  # BD
            'crud:delete',  # 3: there is no deleting users right now
            'misc',
        }
        results = check_server(scim_client)
        failures = [result for result in results if result.status.value not in (1, 7)]

        if failures:
            details = '\n'.join(
                f'{result.status.name}: {result.title} - {result.reason}'
                for result in failures
                if not ignore_tags.intersection(result.tags)
            )
            if details:
                self.fail(
                    f'SCIM conformance suite reported failures:\n{details}'
                )  # pragma: no cover


class PatchedApiClient(APIClient):
    """A DRF APIClient subclass that supports the SCIM media type."""

    def __init__(self, base_url: str, *args, **kwargs):
        """Initialize the client."""
        self.base_url = base_url
        super().__init__(*args, **kwargs)

    def generic(self, method, path, data=None, format=None, content_type=None, **extra):
        """Override the generic method to set the SCIM media type."""
        if content_type is None:
            content_type = 'application/scim+json'
        path = self.base_url + path if not '/scim/v2/' in path else path

        if json_data := extra.pop('json', None):
            data = json.dumps(json_data)
            format = 'json'  # noqa: A001
        return super().generic(
            method, path, data=data, format=format, content_type=content_type, **extra
        )
