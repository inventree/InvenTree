"""API unit tests for the 'pricing' app."""

from decimal import Decimal

from django.urls import reverse

from rest_framework.test import APIClient

from common.models import InvenTreeSetting
from InvenTree.unit_test import InvenTreeAPITestCase
from part.models import Part
from pricing.models import PartInternalPriceBreak, PartSellPriceBreak


class PartPricingDetailTests(InvenTreeAPITestCase):
    """Tests for the part pricing API endpoint."""

    fixtures = ['category', 'part', 'location']

    roles = ['pricing.change']

    def url(self, pk):
        """Construct a pricing URL."""
        return reverse('api-part-pricing', kwargs={'pk': pk})

    def test_pricing_detail(self):
        """Test an empty pricing detail."""
        response = self.get(self.url(1), expected_code=200)

        # Check for expected fields
        expected_fields = [
            'currency',
            'updated',
            'bom_cost_min',
            'bom_cost_max',
            'purchase_cost_min',
            'purchase_cost_max',
            'internal_cost_min',
            'internal_cost_max',
            'supplier_price_min',
            'supplier_price_max',
            'overall_min',
            'overall_max',
        ]

        for field in expected_fields:
            self.assertIn(field, response.data)

        # Empty fields (no pricing by default)
        for field in expected_fields[2:]:
            self.assertIsNone(response.data[field])

    def test_pricing_permissions(self):
        """Test that the 'pricing' role (not the 'part' role) controls access."""
        url = self.url(1)

        self.clearRoles()
        self.assignRole('part.change')

        self.get(url, expected_code=403)
        self.patch(url, {'update': True}, expected_code=403)

        # The 'part' role is not required to view or edit pricing data
        self.clearRoles()
        self.assignRole('pricing.view')
        self.get(url, expected_code=200)
        self.patch(url, {'update': True}, expected_code=403)

        self.assignRole('pricing.change')
        self.patch(url, {'update': True}, expected_code=200)

    def test_override_validation(self):
        """Override minimum price must not exceed override maximum price."""
        url = self.url(1)

        # Both values provided together
        self.patch(
            url,
            {
                'override_min': 100,
                'override_min_currency': 'USD',
                'override_max': 10,
                'override_max_currency': 'USD',
            },
            expected_code=400,
        )

        self.patch(
            url, {'override_max': 10, 'override_max_currency': 'USD'}, expected_code=200
        )

        # Partial update - compared against the existing override_max value
        response = self.patch(
            url,
            {'override_min': 100, 'override_min_currency': 'USD'},
            expected_code=400,
        )
        self.assertIn('override_min', response.data)

        self.patch(
            url, {'override_min': 5, 'override_min_currency': 'USD'}, expected_code=200
        )

        # Partial update of the maximum - compared against the existing override_min value
        self.patch(
            url, {'override_max': 1, 'override_max_currency': 'USD'}, expected_code=400
        )

        # Clearing a value removes the constraint
        self.patch(url, {'override_max': None}, expected_code=200)
        self.patch(
            url,
            {'override_min': 1000, 'override_min_currency': 'USD'},
            expected_code=200,
        )


class PartInternalPriceBreakTest(InvenTreeAPITestCase):
    """Unit tests for the PartInternalPrice API endpoints."""

    fixtures = [
        'category',
        'part',
        'params',
        'location',
        'bom',
        'company',
        'test_templates',
        'manufacturer_part',
        'supplier_part',
        'order',
        'stock',
    ]

    roles = [
        'part.change',
        'part.add',
        'part.delete',
        'part_category.change',
        'part_category.add',
        'part_category.delete',
        'pricing.add',
        'pricing.delete',
    ]

    def test_price_break_permissions(self):
        """Test that price breaks require the 'pricing' role."""
        # Sale price breaks can only be created for salable parts
        Part.objects.filter(pk=1).update(salable=True)

        for url in [
            reverse('api-part-internal-price-list'),
            reverse('api-part-sale-price-list'),
        ]:
            self.clearRoles()
            self.assignRole('part.change')
            self.get(url, expected_code=403)
            self.post(url, {'part': 1, 'quantity': 1, 'price': 1}, expected_code=403)

            self.assignRole('pricing.view')
            self.get(url, expected_code=200)
            self.post(url, {'part': 1, 'quantity': 1, 'price': 1}, expected_code=403)

            self.assignRole('pricing.add')
            self.post(url, {'part': 1, 'quantity': 1, 'price': 1}, expected_code=201)

    def test_create_price_breaks(self):
        """Test we can create price breaks at various quantities."""
        url = reverse('api-part-internal-price-list')

        breaks = [
            (1.0, 101),
            (1.1, 92.555555555),
            (1.5, 90.999999999),
            (1.756, 89),
            (2, 86),
            (25, 80),
        ]

        for q, p in breaks:
            data = self.post(
                url, {'part': 1, 'quantity': q, 'price': p}, expected_code=201
            ).data

            self.assertEqual(data['part'], 1)
            self.assertEqual(round(Decimal(data['quantity']), 4), round(Decimal(q), 4))
            self.assertEqual(round(Decimal(data['price']), 4), round(Decimal(p), 4))

        # Now, ensure that we can delete the Part via the API
        # In particular this test checks that there are no circular post_delete relationships
        # Ref: https://github.com/inventree/InvenTree/pull/3986

        # First, ensure the part instance can be deleted
        p = Part.objects.get(pk=1)
        p.active = False
        p.save()

        InvenTreeSetting.set_setting('PART_ALLOW_DELETE_FROM_ASSEMBLY', True)

        self.delete(reverse('api-part-detail', kwargs={'pk': 1}))

        with self.assertRaises(Part.DoesNotExist):
            p.refresh_from_db()


class PricingLegacyRedirectTests(InvenTreeAPITestCase):
    """Tests for redirects from the legacy pricing endpoints (previously under /api/part/)."""

    fixtures = ['category', 'part', 'location']

    roles = ['part.view', 'pricing.add', 'pricing.change', 'pricing.delete']

    @classmethod
    def setUpTestData(cls):
        """Sale price breaks can only be created for salable parts."""
        super().setUpTestData()
        Part.objects.filter(pk=1).update(salable=True)

    def test_redirect_urls(self):
        """Legacy URLs redirect (HTTP 308) to the new endpoints."""
        pb = PartInternalPriceBreak.objects.create(part_id=1, quantity=1, price=10)
        sb = PartSellPriceBreak.objects.create(part_id=1, quantity=1, price=10)

        redirects = {
            '/api/part/sale-price/': reverse('api-part-sale-price-list'),
            f'/api/part/sale-price/{sb.pk}/': reverse(
                'api-part-sale-price-detail', kwargs={'pk': sb.pk}
            ),
            '/api/part/internal-price/': reverse('api-part-internal-price-list'),
            f'/api/part/internal-price/{pb.pk}/': reverse(
                'api-part-internal-price-detail', kwargs={'pk': pb.pk}
            ),
            '/api/part/1/pricing/': reverse('api-part-pricing', kwargs={'pk': 1}),
        }

        for old_url, new_url in redirects.items():
            self.assertTrue(new_url.startswith('/api/pricing/'))

            response = self.client.get(old_url)
            self.assertEqual(response.status_code, 308, old_url)
            self.assertEqual(response['Location'], new_url)

            # Query parameters are passed through
            response = self.client.get(old_url, {'part': 1, 'ordering': '-quantity'})
            self.assertEqual(response.status_code, 308, old_url)
            self.assertEqual(
                response['Location'], f'{new_url}?part=1&ordering=-quantity'
            )

    def test_redirect_methods(self):
        """The request method (and data) is preserved when following a redirect."""
        old_url = '/api/part/sale-price/'

        # GET
        response = self.get(old_url, {'part': 1}, follow=True)
        self.assertEqual(len(response.data), 0)

        # POST
        response = self.post(
            old_url,
            {'part': 1, 'quantity': 5, 'price': 12.5},
            follow=True,
            expected_code=201,
        )
        pk = response.data['pk']
        self.assertEqual(PartSellPriceBreak.objects.get(pk=pk).quantity, 5)

        # PATCH
        self.patch(
            f'/api/part/sale-price/{pk}/',
            {'quantity': 7},
            follow=True,
            expected_code=200,
        )
        self.assertEqual(PartSellPriceBreak.objects.get(pk=pk).quantity, 7)

        # DELETE
        self.delete(f'/api/part/sale-price/{pk}/', follow=True, expected_code=204)
        self.assertFalse(PartSellPriceBreak.objects.filter(pk=pk).exists())

        # Part pricing detail
        response = self.patch(
            '/api/part/1/pricing/',
            {'override_min': 1, 'override_min_currency': 'USD'},
            follow=True,
            expected_code=200,
        )
        self.assertEqual(float(response.data['override_min']), 1)

    def test_redirect_permissions(self):
        """Redirects do not bypass the permission checks of the new endpoints."""
        self.clearRoles()
        self.assignRole('part.view')

        response = self.client.get('/api/part/sale-price/')
        self.assertEqual(response.status_code, 308)

        self.get('/api/part/sale-price/', follow=True, expected_code=403)
        self.post(
            '/api/part/sale-price/',
            {'part': 1, 'quantity': 5, 'price': 12.5},
            follow=True,
            expected_code=403,
        )

    def test_redirect_csrf(self):
        """The redirect itself is not subject to CSRF checks, but the new endpoint is."""
        client = APIClient(enforce_csrf_checks=True)
        client.force_login(self.user)

        data = {'part': 1, 'quantity': 5, 'price': 12.5}

        response = client.post('/api/part/sale-price/', data, format='json')
        self.assertEqual(response.status_code, 308)

        # Following the redirect, the new endpoint enforces CSRF for session authentication
        response = client.post(
            '/api/part/sale-price/', data, format='json', follow=True
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(PartSellPriceBreak.objects.filter(quantity=5).exists())


class NestedPricingPermissionTests(InvenTreeAPITestCase):
    """Pricing data must not be exposed via nested (embedded) part data.

    Regression test: nested serializers were constructed without the requesting user,
    so permission checks for their optional fields were skipped entirely.
    """

    fixtures = ['category', 'part', 'location', 'bom', 'stock']

    roles = ['part.view', 'bom.view', 'stock.view']

    PRICING_FIELDS = ['pricing_min', 'pricing_max']

    def nested_part_data(self) -> list[dict]:
        """Return nested part data from a selection of API endpoints."""
        bom_item = self.get(
            reverse('api-bom-item-detail', kwargs={'pk': 3}),
            {'sub_part_detail': True, 'pricing': True},
        ).data

        stock_item = self.get(
            reverse('api-stock-list'), {'part_detail': True, 'limit': 1}
        ).data['results'][0]

        return [bom_item['sub_part_detail'], stock_item['part_detail']]

    def test_nested_pricing(self):
        """Nested pricing fields depend on the 'pricing' role of the requesting user."""
        for data in self.nested_part_data():
            self.assertIn('name', data)

            for field in self.PRICING_FIELDS:
                self.assertNotIn(field, data)

        self.assignRole('pricing.view')

        for data in self.nested_part_data():
            for field in self.PRICING_FIELDS:
                self.assertIn(field, data)
