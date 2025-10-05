"""Unit tests for the tenant app."""

from django.contrib.auth import get_user_model
from django.urls import reverse

from InvenTree.unit_test import InvenTreeAPITestCase

from .models import Tenant

User = get_user_model()


class TenantTest(InvenTreeAPITestCase):
    """Test cases for the Tenant model and API."""

    def setUp(self):
        """Set up test data."""
        super().setUp()

        # Create test tenants
        self.tenant1 = Tenant.objects.create(
            name='Tenant 1', description='First test tenant', code='T1', is_active=True
        )

        self.tenant2 = Tenant.objects.create(
            name='Tenant 2', description='Second test tenant', code='T2', is_active=True
        )

        self.tenant3 = Tenant.objects.create(
            name='Inactive Tenant',
            description='Inactive test tenant',
            code='T3',
            is_active=False,
        )

    def test_tenant_creation(self):
        """Test tenant model creation."""
        self.assertEqual(Tenant.objects.count(), 3)
        self.assertEqual(str(self.tenant1), 'Tenant 1')
        self.assertTrue(self.tenant1.is_active)
        self.assertFalse(self.tenant3.is_active)

    def test_tenant_api_list(self):
        """Test tenant API list endpoint."""
        url = reverse('api-tenant-list')
        response = self.get(url, expected_code=200)

        self.assertEqual(len(response.data), 3)

    def test_tenant_api_filter_active(self):
        """Test filtering tenants by active status."""
        url = reverse('api-tenant-list')
        response = self.get(url, data={'is_active': True}, expected_code=200)

        self.assertEqual(len(response.data), 2)

    def test_tenant_api_detail(self):
        """Test tenant API detail endpoint."""
        url = reverse('api-tenant-detail', kwargs={'pk': self.tenant1.pk})
        response = self.get(url, expected_code=200)

        self.assertEqual(response.data['name'], 'Tenant 1')
        self.assertEqual(response.data['code'], 'T1')

    def test_tenant_api_create(self):
        """Test creating a tenant via API."""
        url = reverse('api-tenant-list')
        data = {
            'name': 'New Tenant',
            'description': 'A new tenant',
            'code': 'NT',
            'is_active': True,
        }
        response = self.post(url, data, expected_code=201)

        self.assertEqual(response.data['name'], 'New Tenant')
        self.assertEqual(Tenant.objects.count(), 4)

    def test_tenant_api_update(self):
        """Test updating a tenant via API."""
        url = reverse('api-tenant-detail', kwargs={'pk': self.tenant1.pk})
        data = {'description': 'Updated description'}
        response = self.patch(url, data, expected_code=200)

        self.assertEqual(response.data['description'], 'Updated description')

    def test_tenant_api_delete(self):
        """Test deleting a tenant via API."""
        url = reverse('api-tenant-detail', kwargs={'pk': self.tenant3.pk})
        self.delete(url, expected_code=204)

        self.assertEqual(Tenant.objects.count(), 2)

    def test_tenant_list_permissions(self):
        """Test that the user permissions are correctly applied.

        - For all /api/tenant/ endpoints, any authenticated user should have full read access
        - Write access is limited to staff users
        - Non authenticated users should have no access at all
        """
        url = reverse('api-tenant-list')

        # Non-authenticated user should have no access
        self.logout()
        self.get(url, expected_code=401)

        # Authenticated non-staff user should have read access only
        self.user.is_staff = False
        self.user.save()
        self.login()

        # Check read access to tenant list URL
        response = self.get(url, expected_code=200)
        self.assertEqual(len(response.data), 3)

        # Attempt to create a new tenant (should fail for non-staff)
        new_tenant_data = {
            'name': 'New Tenant',
            'description': 'A new tenant for testing',
            'code': 'NT',
            'is_active': True,
        }

        self.post(url, data=new_tenant_data, expected_code=403)

        # Verify the tenant was not created
        self.assertEqual(Tenant.objects.count(), 3)

        # Now, test with a staff user
        self.logout()
        self.user.is_staff = True
        self.user.save()
        self.login()

        # Staff user should be able to create a new tenant
        response = self.post(url, data=new_tenant_data, expected_code=201)
        self.assertEqual(response.data['name'], 'New Tenant')
        self.assertEqual(response.data['code'], 'NT')

        # Verify the tenant was created
        self.assertEqual(Tenant.objects.count(), 4)

    def test_tenant_detail_permissions(self):
        """Test that the user permissions are correctly applied to detail endpoints."""
        detail_url = reverse('api-tenant-detail', kwargs={'pk': self.tenant1.pk})

        # Non-authenticated user should have no access
        self.logout()
        self.get(detail_url, expected_code=401)

        # Authenticated non-staff user should have read access only
        self.user.is_staff = False
        self.user.save()
        self.login()

        # Check read access to tenant detail URL
        response = self.get(detail_url, expected_code=200)
        self.assertEqual(response.data['name'], self.tenant1.name)
        self.assertEqual(response.data['code'], self.tenant1.code)

        # Attempt to update the tenant (should fail for non-staff)
        self.patch(
            detail_url, data={'description': 'Updated description'}, expected_code=403
        )

        # Verify the tenant was not updated
        self.tenant1.refresh_from_db()
        self.assertNotEqual(self.tenant1.description, 'Updated description')

        # Attempt to delete the tenant (should fail for non-staff)
        self.delete(detail_url, expected_code=403)

        # Verify the tenant still exists
        self.assertTrue(Tenant.objects.filter(pk=self.tenant1.pk).exists())

        # Now, test with a staff user
        self.logout()
        self.user.is_staff = True
        self.user.save()
        self.login()

        # Staff user should be able to update the tenant
        response = self.patch(
            detail_url,
            data={'description': 'Staff updated description'},
            expected_code=200,
        )
        self.assertEqual(response.data['description'], 'Staff updated description')

        # Verify the tenant was updated
        self.tenant1.refresh_from_db()
        self.assertEqual(self.tenant1.description, 'Staff updated description')

        # Staff user should be able to delete the tenant
        self.delete(detail_url, expected_code=204)

        # Verify the tenant was deleted
        self.assertFalse(Tenant.objects.filter(pk=self.tenant1.pk).exists())

    def test_non_staff_read_access(self):
        """Test that non-staff users can read tenants."""
        url = reverse('api-tenant-list')

        # Authenticated non-staff user should have read access
        self.user.is_staff = False
        self.user.save()
        self.login()

        response = self.get(url, expected_code=200)
        self.assertEqual(len(response.data), 3)

        # Verify the data is correct
        names = [item['name'] for item in response.data]
        self.assertIn('Tenant 1', names)
        self.assertIn('Tenant 2', names)
        self.assertIn('Inactive Tenant', names)

    def test_non_staff_cannot_create(self):
        """Test that non-staff users cannot create tenants."""
        url = reverse('api-tenant-list')

        self.user.is_staff = False
        self.user.save()
        self.login()

        new_tenant_data = {
            'name': 'Unauthorized Tenant',
            'code': 'UT',
            'is_active': True,
        }

        self.post(url, data=new_tenant_data, expected_code=403)
        self.assertEqual(Tenant.objects.count(), 3)

    def test_non_staff_cannot_update(self):
        """Test that non-staff users cannot update tenants."""
        detail_url = reverse('api-tenant-detail', kwargs={'pk': self.tenant1.pk})
        original_name = self.tenant1.name

        self.user.is_staff = False
        self.user.save()
        self.login()

        self.patch(detail_url, data={'name': 'Hacked Name'}, expected_code=403)

        self.tenant1.refresh_from_db()
        self.assertEqual(self.tenant1.name, original_name)

    def test_non_staff_cannot_delete(self):
        """Test that non-staff users cannot delete tenants."""
        detail_url = reverse('api-tenant-detail', kwargs={'pk': self.tenant2.pk})

        self.user.is_staff = False
        self.user.save()
        self.login()

        self.delete(detail_url, expected_code=403)
        self.assertTrue(Tenant.objects.filter(pk=self.tenant2.pk).exists())

    def test_staff_full_access(self):
        """Test that staff users have full access to tenant operations."""
        url = reverse('api-tenant-list')

        self.user.is_staff = True
        self.user.save()
        self.login()

        # Staff can create
        new_tenant_data = {
            'name': 'Staff Created Tenant',
            'description': 'Created by staff',
            'code': 'SCT',
            'is_active': True,
        }

        response = self.post(url, data=new_tenant_data, expected_code=201)
        self.assertEqual(response.data['name'], 'Staff Created Tenant')
        tenant_id = response.data['pk']

        # Staff can update
        detail_url = reverse('api-tenant-detail', kwargs={'pk': tenant_id})
        response = self.patch(
            detail_url, data={'description': 'Updated by staff'}, expected_code=200
        )
        self.assertEqual(response.data['description'], 'Updated by staff')

        # Staff can delete
        self.delete(detail_url, expected_code=204)
        self.assertFalse(Tenant.objects.filter(pk=tenant_id).exists())
