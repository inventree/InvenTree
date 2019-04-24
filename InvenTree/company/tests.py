from django.test import TestCase

from .models import Company


class CompanySimpleTest(TestCase):

    def setUp(self):
        Company.objects.create(name='ABC Co.',
                               description='Seller of ABC products',
                               website='www.abc-sales.com',
                               address='123 Sales St.',
                               is_customer=False,
                               is_supplier=True)

    def test_company_model(self):
        c = Company.objects.get(pk=1)
        self.assertEqual(c.name, 'ABC Co.')
        self.assertEqual(c.get_absolute_url(), '/company/1/')