""" Unit tests for Company views (see views.py) """

from django.urls import reverse

from InvenTree.InvenTree.helpers import InvenTreeTestCase


class CompanyViewTestBase(InvenTreeTestCase):

    fixtures = [
        'category',
        'part',
        'location',
        'company',
        'manufacturer_part',
        'supplier_part',
    ]

    roles = [
        'all',
    ]


class CompanyViewTest(CompanyViewTestBase):
    """
    Tests for various 'Company' views
    """

    def test_company_index(self):
        """ Test the company index """

        response = self.client.get(reverse('company-index'))
        self.assertEqual(response.status_code, 200)

    def test_manufacturer_index(self):
        """ Test the manufacturer index """

        response = self.client.get(reverse('manufacturer-index'))
        self.assertEqual(response.status_code, 200)

    def test_customer_index(self):
        """ Test the customer index """

        response = self.client.get(reverse('customer-index'))
        self.assertEqual(response.status_code, 200)

    def test_manufacturer_part_detail_view(self):
        """ Test the manufacturer part detail view """

        response = self.client.get(reverse('manufacturer-part-detail', kwargs={'pk': 1}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'MPN123')

    def test_supplier_part_detail_view(self):
        """ Test the supplier part detail view """

        response = self.client.get(reverse('supplier-part-detail', kwargs={'pk': 10}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'MPN456-APPEL')
