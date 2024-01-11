"""Unit testing for the company app API functions"""

from django.urls import reverse

from rest_framework import status

from InvenTree.unit_test import InvenTreeAPITestCase

from .models import Address, Company, Contact, ManufacturerPart, SupplierPart


class CompanyTest(InvenTreeAPITestCase):
    """Series of tests for the Company DRF API."""

    roles = ['purchase_order.add', 'purchase_order.change']

    @classmethod
    def setUpTestData(cls):
        """Perform initialization for the unit test class"""
        super().setUpTestData()

        # Create some company objects to work with
        cls.acme = Company.objects.create(
            name='ACME', description='Supplier', is_customer=False, is_supplier=True
        )
        Company.objects.create(
            name='Drippy Cup Co.',
            description='Customer',
            is_customer=True,
            is_supplier=False,
        )
        Company.objects.create(
            name='Sippy Cup Emporium', description='Another supplier'
        )

    def test_company_list(self):
        """Test the list API endpoint for the Company model"""
        url = reverse('api-company-list')

        # There should be three companies
        response = self.get(url)
        self.assertEqual(len(response.data), 3)

        data = {'is_customer': True}

        # There should only be one customer
        response = self.get(url, data)
        self.assertEqual(len(response.data), 1)

        data = {'is_supplier': True}

        # There should be two suppliers
        response = self.get(url, data)
        self.assertEqual(len(response.data), 2)

    def test_company_detail(self):
        """Tests for the Company detail endpoint."""
        url = reverse('api-company-detail', kwargs={'pk': self.acme.pk})
        response = self.get(url)

        self.assertEqual(response.data['name'], 'ACME')

        # Change the name of the company
        # Note we should not have the correct permissions (yet)
        data = response.data
        response = self.client.patch(url, data, format='json', expected_code=400)

        self.assignRole('company.change')

        # Update the name and set the currency to a valid value
        data['name'] = 'ACMOO'
        data['currency'] = 'NZD'

        response = self.client.patch(url, data, format='json', expected_code=200)

        self.assertEqual(response.data['name'], 'ACMOO')
        self.assertEqual(response.data['currency'], 'NZD')

    def test_company_search(self):
        """Test search functionality in company list."""
        url = reverse('api-company-list')
        data = {'search': 'cup'}
        response = self.get(url, data)
        self.assertEqual(len(response.data), 2)

    def test_company_create(self):
        """Test that we can create a company via the API!"""
        url = reverse('api-company-list')

        # Name is required
        response = self.post(url, {'description': 'A description!'}, expected_code=400)

        # Minimal example, checking default values
        response = self.post(
            url,
            {'name': 'My API Company', 'description': 'A company created via the API'},
            expected_code=201,
        )

        self.assertTrue(response.data['is_supplier'])
        self.assertFalse(response.data['is_customer'])
        self.assertFalse(response.data['is_manufacturer'])

        self.assertEqual(response.data['currency'], 'USD')

        # Maximal example, specify values
        response = self.post(
            url,
            {
                'name': 'Another Company',
                'description': 'Also created via the API!',
                'currency': 'AUD',
                'is_supplier': False,
                'is_manufacturer': True,
                'is_customer': True,
            },
            expected_code=201,
        )

        self.assertEqual(response.data['currency'], 'AUD')
        self.assertFalse(response.data['is_supplier'])
        self.assertTrue(response.data['is_customer'])
        self.assertTrue(response.data['is_manufacturer'])

        # Attempt to create with invalid currency
        response = self.post(
            url,
            {'name': 'A name', 'description': 'A description', 'currency': 'POQD'},
            expected_code=400,
        )

        self.assertTrue('currency' in response.data)


class ContactTest(InvenTreeAPITestCase):
    """Tests for the Contact models"""

    roles = []

    @classmethod
    def setUpTestData(cls):
        """Perform init for this test class"""
        super().setUpTestData()

        # Create some companies
        companies = [
            Company(name=f'Company {idx}', description='Some company')
            for idx in range(3)
        ]

        Company.objects.bulk_create(companies)

        contacts = []

        # Create some contacts
        for cmp in Company.objects.all():
            contacts += [
                Contact(company=cmp, name=f'My name {idx}') for idx in range(3)
            ]

        Contact.objects.bulk_create(contacts)

        cls.url = reverse('api-contact-list')

    def test_list(self):
        """Test company list API endpoint"""
        # List all results
        response = self.get(self.url, {}, expected_code=200)

        self.assertEqual(len(response.data), 9)

        for result in response.data:
            for key in ['name', 'email', 'pk', 'company']:
                self.assertIn(key, result)

        # Filter by particular company
        for cmp in Company.objects.all():
            response = self.get(self.url, {'company': cmp.pk}, expected_code=200)

            self.assertEqual(len(response.data), 3)

    def test_create(self):
        """Test that we can create a new Contact object via the API"""
        n = Contact.objects.count()

        company = Company.objects.first()

        # Without required permissions, creation should fail
        self.post(
            self.url, {'company': company.pk, 'name': 'Joe Bloggs'}, expected_code=403
        )

        self.assignRole('return_order.add')

        self.post(
            self.url, {'company': company.pk, 'name': 'Joe Bloggs'}, expected_code=201
        )

        self.assertEqual(Contact.objects.count(), n + 1)

    def test_edit(self):
        """Test that we can edit a Contact via the API"""
        # Get the first contact
        contact = Contact.objects.first()
        # Use this contact in the tests
        url = reverse('api-contact-detail', kwargs={'pk': contact.pk})

        # Retrieve detail view
        data = self.get(url, expected_code=200).data

        for key in ['pk', 'name', 'role']:
            self.assertIn(key, data)

        self.patch(url, {'role': 'model'}, expected_code=403)

        self.assignRole('purchase_order.change')

        self.patch(url, {'role': 'x'}, expected_code=200)

        # Get the contact again
        contact = Contact.objects.first()
        self.assertEqual(contact.role, 'x')

    def test_delete(self):
        """Tests that we can delete a Contact via the API"""
        # Get the last contact
        contact = Contact.objects.first()
        url = reverse('api-contact-detail', kwargs={'pk': contact.pk})

        # Delete (without required permissions)
        self.delete(url, expected_code=403)

        self.assignRole('sales_order.delete')

        self.delete(url, expected_code=204)

        # Try to access again (gone!)
        self.get(url, expected_code=404)


class AddressTest(InvenTreeAPITestCase):
    """Test cases for Address API endpoints"""

    roles = []

    @classmethod
    def setUpTestData(cls):
        """Perform initialization for this test class"""
        super().setUpTestData()
        cls.num_companies = 3
        cls.num_addr = 3
        # Create some companies
        companies = [
            Company(name=f'Company {idx}', description='Some company')
            for idx in range(cls.num_companies)
        ]

        Company.objects.bulk_create(companies)

        addresses = []

        # Create some contacts
        for cmp in Company.objects.all():
            addresses += [
                Address(company=cmp, title=f'Address no. {idx}')
                for idx in range(cls.num_addr)
            ]

        cls.url = reverse('api-address-list')

        Address.objects.bulk_create(addresses)

    def test_list(self):
        """Test listing all addresses without filtering"""
        response = self.get(self.url, expected_code=200)

        self.assertEqual(len(response.data), self.num_companies * self.num_addr)

    def test_filter_list(self):
        """Test listing addresses filtered on company"""
        company = Company.objects.first()

        response = self.get(self.url, {'company': company.pk}, expected_code=200)

        self.assertEqual(len(response.data), self.num_addr)

    def test_create(self):
        """Test creating a new address"""
        company = Company.objects.first()

        self.post(self.url, {'company': company.pk, 'title': 'HQ'}, expected_code=403)

        self.assignRole('purchase_order.add')

        self.post(self.url, {'company': company.pk, 'title': 'HQ'}, expected_code=201)

    def test_get(self):
        """Test that objects are properly returned from a get"""
        addr = Address.objects.first()

        url = reverse('api-address-detail', kwargs={'pk': addr.pk})
        response = self.get(url, expected_code=200)

        self.assertEqual(response.data['pk'], addr.pk)

        for key in [
            'title',
            'line1',
            'line2',
            'postal_code',
            'postal_city',
            'province',
            'country',
        ]:
            self.assertIn(key, response.data)

    def test_edit(self):
        """Test editing an object"""
        addr = Address.objects.first()

        url = reverse('api-address-detail', kwargs={'pk': addr.pk})

        self.patch(url, {'title': 'Hello'}, expected_code=403)

        self.assignRole('purchase_order.change')

        self.patch(url, {'title': 'World'}, expected_code=200)

        data = self.get(url, expected_code=200).data

        self.assertEqual(data['title'], 'World')

    def test_delete(self):
        """Test deleting an object"""
        addr = Address.objects.first()

        url = reverse('api-address-detail', kwargs={'pk': addr.pk})

        self.delete(url, expected_code=403)

        self.assignRole('purchase_order.delete')

        self.delete(url, expected_code=204)

        self.get(url, expected_code=404)


class ManufacturerTest(InvenTreeAPITestCase):
    """Series of tests for the Manufacturer DRF API."""

    fixtures = [
        'category',
        'part',
        'location',
        'company',
        'manufacturer_part',
        'supplier_part',
    ]

    roles = ['part.add', 'part.change']

    def test_manufacturer_part_list(self):
        """Test the ManufacturerPart API list functionality"""
        url = reverse('api-manufacturer-part-list')

        # There should be three manufacturer parts
        response = self.get(url)
        self.assertEqual(len(response.data), 3)

        # Create manufacturer part
        data = {'part': 1, 'manufacturer': 7, 'MPN': 'MPN_TEST'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['MPN'], 'MPN_TEST')

        # Filter by manufacturer
        data = {'manufacturer': 7}
        response = self.get(url, data)
        self.assertEqual(len(response.data), 3)

        # Filter by part
        data = {'part': 5}
        response = self.get(url, data)
        self.assertEqual(len(response.data), 2)

    def test_manufacturer_part_detail(self):
        """Tests for the ManufacturerPart detail endpoint."""
        url = reverse('api-manufacturer-part-detail', kwargs={'pk': 1})

        response = self.get(url)
        self.assertEqual(response.data['MPN'], 'MPN123')

        # Change the MPN
        data = {'MPN': 'MPN-TEST-123'}

        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['MPN'], 'MPN-TEST-123')

    def test_manufacturer_part_search(self):
        """Test search functionality in manufacturer list"""
        url = reverse('api-manufacturer-part-list')
        data = {'search': 'MPN'}
        response = self.get(url, data)
        self.assertEqual(len(response.data), 3)

    def test_supplier_part_create(self):
        """Test a SupplierPart can be created via the API"""
        url = reverse('api-supplier-part-list')

        # Create a manufacturer part
        response = self.post(
            reverse('api-manufacturer-part-list'),
            {
                'part': 1,
                'manufacturer': 7,
                'MPN': 'PART_NUMBER',
                'link': 'https://www.axel-larsson.se/Exego.aspx?p_id=341&ArtNr=0804020E',
            },
            expected_code=201,
        )

        pk = response.data['pk']

        # Create a supplier part (associated with the new manufacturer part)
        data = {
            'part': 1,
            'supplier': 1,
            'SKU': 'SKU_TEST',
            'manufacturer_part': pk,
            'link': 'https://www.axel-larsson.se/Exego.aspx?p_id=341&ArtNr=0804020E',
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check link is not modified
        self.assertEqual(
            response.data['link'],
            'https://www.axel-larsson.se/Exego.aspx?p_id=341&ArtNr=0804020E',
        )

        # Check link is not modified
        self.assertEqual(
            response.data['link'],
            'https://www.axel-larsson.se/Exego.aspx?p_id=341&ArtNr=0804020E',
        )


class SupplierPartTest(InvenTreeAPITestCase):
    """Unit tests for the SupplierPart API endpoints"""

    fixtures = [
        'category',
        'part',
        'location',
        'company',
        'manufacturer_part',
        'supplier_part',
    ]

    roles = ['part.add', 'part.change', 'part.add', 'purchase_order.change']

    def test_supplier_part_list(self):
        """Test the SupplierPart API list functionality"""
        url = reverse('api-supplier-part-list')

        # Return *all* SupplierParts
        response = self.get(url, {}, expected_code=200)

        self.assertEqual(len(response.data), SupplierPart.objects.count())

        # Filter by Supplier reference
        for supplier in Company.objects.filter(is_supplier=True):
            response = self.get(url, {'supplier': supplier.pk}, expected_code=200)
            self.assertEqual(len(response.data), supplier.supplied_parts.count())

        # Filter by Part reference
        expected = {1: 4, 25: 2}

        for pk, n in expected.items():
            response = self.get(url, {'part': pk}, expected_code=200)
            self.assertEqual(len(response.data), n)

    def test_available(self):
        """Tests for updating the 'available' field"""
        url = reverse('api-supplier-part-list')

        # Should fail when sending an invalid 'available' field
        response = self.post(
            url,
            {'part': 1, 'supplier': 2, 'SKU': 'QQ', 'available': 'not a number'},
            expected_code=400,
        )

        self.assertIn('A valid number is required', str(response.data))

        # Create a SupplierPart without specifying available quantity
        response = self.post(
            url, {'part': 1, 'supplier': 2, 'SKU': 'QQ'}, expected_code=201
        )

        sp = SupplierPart.objects.get(pk=response.data['pk'])

        self.assertIsNone(sp.availability_updated)
        self.assertEqual(sp.available, 0)

        # Now, *update* the available quantity via the API
        self.patch(
            reverse('api-supplier-part-detail', kwargs={'pk': sp.pk}),
            {'available': 1234},
            expected_code=200,
        )

        sp.refresh_from_db()
        self.assertIsNotNone(sp.availability_updated)
        self.assertEqual(sp.available, 1234)

        # We should also be able to create a SupplierPart with initial 'available' quantity
        response = self.post(
            url,
            {'part': 1, 'supplier': 2, 'SKU': 'QQQ', 'available': 999},
            expected_code=201,
        )

        sp = SupplierPart.objects.get(pk=response.data['pk'])
        self.assertEqual(sp.available, 999)
        self.assertIsNotNone(sp.availability_updated)


class CompanyMetadataAPITest(InvenTreeAPITestCase):
    """Unit tests for the various metadata endpoints of API."""

    fixtures = [
        'category',
        'part',
        'location',
        'company',
        'contact',
        'manufacturer_part',
        'supplier_part',
    ]

    roles = ['company.change', 'purchase_order.change', 'part.change']

    def metatester(self, apikey, model):
        """Generic tester"""
        modeldata = model.objects.first()

        # Useless test unless a model object is found
        self.assertIsNotNone(modeldata)

        url = reverse(apikey, kwargs={'pk': modeldata.pk})

        # Metadata is initially null
        self.assertIsNone(modeldata.metadata)

        numstr = f'12{len(apikey)}'

        self.patch(
            url,
            {'metadata': {f'abc-{numstr}': f'xyz-{apikey}-{numstr}'}},
            expected_code=200,
        )

        # Refresh
        modeldata.refresh_from_db()
        self.assertEqual(
            modeldata.get_metadata(f'abc-{numstr}'), f'xyz-{apikey}-{numstr}'
        )

    def test_metadata(self):
        """Test all endpoints"""
        for apikey, model in {
            'api-manufacturer-part-metadata': ManufacturerPart,
            'api-supplier-part-metadata': SupplierPart,
            'api-company-metadata': Company,
            'api-contact-metadata': Contact,
        }.items():
            self.metatester(apikey, model)
