"""API tests for tax models."""

from django.urls import reverse

from InvenTree.unit_test import InvenTreeAPITestCase

from .models import TaxConfiguration


class TaxAPITest(InvenTreeAPITestCase):
    """Unit tests for TaxConfiguration API endpoints."""

    @classmethod
    def setUpTestData(cls):
        """Set up test data for all tests."""
        super().setUpTestData()

        # Create some test tax configurations
        TaxConfiguration.objects.create(
            year=2024,
            name='VAT 2024',
            description='Value Added Tax for 2024',
            rate=20.0,
            currency='USD',
            is_active=True,
            is_inclusive=False,
            applies_to_sales=True,
            applies_to_purchases=True,
        )

        TaxConfiguration.objects.create(
            year=2023,
            name='VAT 2023',
            description='Value Added Tax for 2023',
            rate=19.0,
            currency='USD',
            is_active=True,
            is_inclusive=False,
            applies_to_sales=True,
            applies_to_purchases=True,
        )

    def test_tax_list_url(self):
        """Test that the tax configuration list URL is correct."""
        url = reverse('api-tax-configuration-list')
        self.assertEqual(url, '/api/tax/configuration/')

    def test_tax_detail_url(self):
        """Test that the tax configuration detail URL is correct."""
        tax = TaxConfiguration.objects.first()
        url = reverse('api-tax-configuration-detail', kwargs={'pk': tax.pk})
        self.assertEqual(url, f'/api/tax/configuration/{tax.pk}/')

    def test_tax_list_permissions(self):
        """Test that the user permissions are correctly applied.

        - For all /api/tax/ endpoints, any authenticated user should have full read access
        - Write access is limited to staff users
        - Non authenticated users should have no access at all
        """
        url = reverse('api-tax-configuration-list')

        # Non-authenticated user should have no access
        self.logout()
        self.get(url, expected_code=401)

        # Authenticated non-staff user should have read access only
        self.user.is_staff = False
        self.user.save()
        self.login()

        # Check read access to tax list URL
        response = self.get(url, expected_code=200)
        self.assertEqual(len(response.data), 2)

        # Attempt to create a new tax configuration (should fail for non-staff)
        new_tax_data = {
            'year': 2025,
            'name': 'VAT 2025',
            'description': 'Value Added Tax for 2025',
            'rate': 21.0,
            'currency': 'USD',
            'is_active': True,
            'is_inclusive': False,
            'applies_to_sales': True,
            'applies_to_purchases': True,
        }

        self.post(url, data=new_tax_data, expected_code=403)

        # Verify the tax configuration was not created
        self.assertEqual(TaxConfiguration.objects.count(), 2)

        # Now, test with a staff user
        self.logout()
        self.user.is_staff = True
        self.user.save()
        self.login()

        # Staff user should be able to create a new tax configuration
        response = self.post(url, data=new_tax_data, expected_code=201)
        self.assertEqual(response.data['name'], 'VAT 2025')
        self.assertEqual(response.data['year'], 2025)
        self.assertEqual(float(response.data['rate']), 21.0)

        # Verify the tax configuration was created
        self.assertEqual(TaxConfiguration.objects.count(), 3)

    def test_tax_detail_permissions(self):
        """Test that the user permissions are correctly applied to detail endpoints."""
        tax = TaxConfiguration.objects.first()
        detail_url = reverse('api-tax-configuration-detail', kwargs={'pk': tax.pk})

        # Non-authenticated user should have no access
        self.logout()
        self.get(detail_url, expected_code=401)

        # Authenticated non-staff user should have read access only
        self.user.is_staff = False
        self.user.save()
        self.login()

        # Check read access to tax detail URL
        response = self.get(detail_url, expected_code=200)
        self.assertEqual(response.data['name'], tax.name)
        self.assertEqual(response.data['year'], tax.year)

        # Attempt to update the tax configuration (should fail for non-staff)
        self.patch(
            detail_url, data={'description': 'Updated description'}, expected_code=403
        )

        # Verify the tax configuration was not updated
        tax.refresh_from_db()
        self.assertNotEqual(tax.description, 'Updated description')

        # Attempt to delete the tax configuration (should fail for non-staff)
        self.delete(detail_url, expected_code=403)

        # Verify the tax configuration still exists
        self.assertTrue(TaxConfiguration.objects.filter(pk=tax.pk).exists())

        # Now, test with a staff user
        self.logout()
        self.user.is_staff = True
        self.user.save()
        self.login()

        # Staff user should be able to update the tax configuration
        response = self.patch(
            detail_url,
            data={'description': 'Staff updated description'},
            expected_code=200,
        )
        self.assertEqual(response.data['description'], 'Staff updated description')

        # Verify the tax configuration was updated
        tax.refresh_from_db()
        self.assertEqual(tax.description, 'Staff updated description')

        # Staff user should be able to delete the tax configuration
        self.delete(detail_url, expected_code=204)

        # Verify the tax configuration was deleted
        self.assertFalse(TaxConfiguration.objects.filter(pk=tax.pk).exists())

    def test_tax_list_read_operations(self):
        """Test that all authenticated users can read tax configurations."""
        url = reverse('api-tax-configuration-list')

        # Authenticated non-staff user should have read access
        self.user.is_staff = False
        self.user.save()
        self.login()

        response = self.get(url, expected_code=200)
        self.assertEqual(len(response.data), 2)

        # Verify the data is correct
        names = [item['name'] for item in response.data]
        self.assertIn('VAT 2024', names)
        self.assertIn('VAT 2023', names)

    def test_tax_detail_read_operations(self):
        """Test that all authenticated users can read individual tax configurations."""
        tax = TaxConfiguration.objects.first()
        detail_url = reverse('api-tax-configuration-detail', kwargs={'pk': tax.pk})

        # Authenticated non-staff user should have read access
        self.user.is_staff = False
        self.user.save()
        self.login()

        response = self.get(detail_url, expected_code=200)
        self.assertEqual(response.data['name'], tax.name)
        self.assertEqual(response.data['year'], tax.year)
        self.assertEqual(float(response.data['rate']), float(tax.rate))

    def test_tax_filtering(self):
        """Test that tax configurations can be filtered correctly."""
        url = reverse('api-tax-configuration-list')

        self.user.is_staff = False
        self.user.save()
        self.login()

        # Filter by year
        response = self.get(url, data={'year': 2024}, expected_code=200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['year'], 2024)

        # Filter by is_active
        response = self.get(url, data={'is_active': True}, expected_code=200)
        self.assertEqual(len(response.data), 2)

        # Search by name
        response = self.get(url, data={'search': '2024'}, expected_code=200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['year'], 2024)

    def test_staff_create_operations(self):
        """Test that staff users can create tax configurations."""
        url = reverse('api-tax-configuration-list')

        self.user.is_staff = True
        self.user.save()
        self.login()

        new_tax_data = {
            'year': 2026,
            'name': 'Sales Tax 2026',
            'description': 'Sales tax for 2026',
            'rate': 8.5,
            'currency': 'USD',
            'is_active': True,
            'is_inclusive': True,
            'applies_to_sales': True,
            'applies_to_purchases': False,
        }

        response = self.post(url, data=new_tax_data, expected_code=201)
        self.assertEqual(response.data['name'], 'Sales Tax 2026')
        self.assertEqual(response.data['year'], 2026)
        self.assertEqual(float(response.data['rate']), 8.5)
        self.assertTrue(response.data['is_inclusive'])
        self.assertTrue(response.data['applies_to_sales'])
        self.assertFalse(response.data['applies_to_purchases'])

    def test_staff_update_operations(self):
        """Test that staff users can update tax configurations."""
        tax = TaxConfiguration.objects.first()
        detail_url = reverse('api-tax-configuration-detail', kwargs={'pk': tax.pk})

        self.user.is_staff = True
        self.user.save()
        self.login()

        update_data = {'rate': 22.5, 'description': 'Updated tax rate'}

        response = self.patch(detail_url, data=update_data, expected_code=200)
        self.assertEqual(float(response.data['rate']), 22.5)
        self.assertEqual(response.data['description'], 'Updated tax rate')

        tax.refresh_from_db()
        self.assertEqual(float(tax.rate), 22.5)
        self.assertEqual(tax.description, 'Updated tax rate')

    def test_staff_delete_operations(self):
        """Test that staff users can delete tax configurations."""
        tax = TaxConfiguration.objects.first()
        detail_url = reverse('api-tax-configuration-detail', kwargs={'pk': tax.pk})
        tax_id = tax.pk

        self.user.is_staff = True
        self.user.save()
        self.login()

        self.delete(detail_url, expected_code=204)
        self.assertFalse(TaxConfiguration.objects.filter(pk=tax_id).exists())

    def test_non_staff_cannot_create(self):
        """Test that non-staff users cannot create tax configurations."""
        url = reverse('api-tax-configuration-list')

        self.user.is_staff = False
        self.user.save()
        self.login()

        new_tax_data = {
            'year': 2027,
            'name': 'Test Tax',
            'rate': 10.0,
            'currency': 'USD',
            'is_active': True,
            'applies_to_sales': True,
            'applies_to_purchases': True,
        }

        self.post(url, data=new_tax_data, expected_code=403)
        self.assertEqual(TaxConfiguration.objects.count(), 2)

    def test_non_staff_cannot_update(self):
        """Test that non-staff users cannot update tax configurations."""
        tax = TaxConfiguration.objects.first()
        detail_url = reverse('api-tax-configuration-detail', kwargs={'pk': tax.pk})
        original_rate = tax.rate

        self.user.is_staff = False
        self.user.save()
        self.login()

        self.patch(detail_url, data={'rate': 99.9}, expected_code=403)

        tax.refresh_from_db()
        self.assertEqual(tax.rate, original_rate)

    def test_non_staff_cannot_delete(self):
        """Test that non-staff users cannot delete tax configurations."""
        tax = TaxConfiguration.objects.first()
        detail_url = reverse('api-tax-configuration-detail', kwargs={'pk': tax.pk})

        self.user.is_staff = False
        self.user.save()
        self.login()

        self.delete(detail_url, expected_code=403)
        self.assertTrue(TaxConfiguration.objects.filter(pk=tax.pk).exists())
