"""API unit tests for the 'pricing' app."""

from decimal import Decimal

from django.urls import reverse

from rest_framework.test import APIClient

from common.models import InvenTreeSetting
from InvenTree.unit_test import InvenTreeAPITestCase
from part.models import Part
from pricing.api import StockItemCostEntryList, StockItemCostList
from pricing.models import (
    CostSource,
    PartInternalPriceBreak,
    PartSellPriceBreak,
    StockItemCost,
    StockItemCostEntry,
)
from pricing.status_codes import CostType
from stock.models import StockItem


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


class StockItemCostApiTestBase(InvenTreeAPITestCase):
    """Base class for the stock item cost API tests."""

    fixtures = ['category', 'part', 'location', 'stock']

    ALL_PERMISSIONS = ['view', 'add', 'change', 'delete']

    roles = [
        *[f'pricing.{perm}' for perm in ALL_PERMISSIONS],
        *[f'stock.{perm}' for perm in ALL_PERMISSIONS],
    ]

    @classmethod
    def setUpTestData(cls):
        """Create some cost data to work with."""
        super().setUpTestData()

        InvenTreeSetting.set_setting('INVENTREE_DEFAULT_CURRENCY', 'USD', None)

        items = StockItem.objects.all().order_by('pk')
        cls.item = items[0]
        cls.other_item = items[1]

        cls.entry = StockItemCostEntry.objects.create_cost(
            cls.item, CostType.PURCHASE, 'plugin:test', min_cost=10, max_cost=12
        )

        StockItemCostEntry.objects.create_cost(
            cls.item, CostType.LANDED, CostSource.MANUAL, min_cost=1, estimated=True
        )

        StockItemCostEntry.objects.create_cost(
            cls.other_item, CostType.PURCHASE, CostSource.MANUAL, min_cost=5
        )

    def set_roles(self, *roles):
        """Replace the user's roles with the provided roles."""
        self.clearRoles()

        for role in roles:
            self.assignRole(role)


class StockItemCostEntryApiTests(StockItemCostApiTestBase):
    """Tests for the StockItemCostEntry API endpoints."""

    LIST_URL = reverse('api-stock-cost-entry-list')

    def detail_url(self, pk):
        """Return the detail URL for a cost entry."""
        return reverse('api-stock-cost-entry-detail', kwargs={'pk': pk})

    def test_list(self):
        """Test listing and filtering cost entries."""
        response = self.get(self.LIST_URL)
        self.assertEqual(len(response.data), 3)

        for field in [
            'pk',
            'stock_item',
            'cost_type',
            'cost_type_text',
            'source',
            'estimated',
            'currency',
            'min_cost',
            'max_cost',
            'converted_currency',
            'converted_min_cost',
            'converted_max_cost',
            'date',
            'user',
            'source_data',
            'notes',
        ]:
            self.assertIn(field, response.data[0])

        response = self.get(self.LIST_URL, {'stock_item': self.item.pk})
        self.assertEqual(len(response.data), 2)

        response = self.get(self.LIST_URL, {'cost_type': CostType.LANDED.value})
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['cost_type_text'], 'Landed')

        response = self.get(self.LIST_URL, {'source': 'plugin:test'})
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['pk'], self.entry.pk)

        response = self.get(self.LIST_URL, {'estimated': True})
        self.assertEqual(len(response.data), 1)

        response = self.get(self.LIST_URL, {'user_detail': True})
        self.assertIn('user_detail', response.data[0])

    def test_create(self):
        """Test creating a cost entry via the API."""
        response = self.post(
            self.LIST_URL,
            {
                'stock_item': self.other_item.pk,
                'cost_type': CostType.FEES.value,
                'min_cost': '1.25',
                'currency': 'USD',
                'notes': 'Bank fee',
            },
        )

        data = response.data

        # Source defaults to 'manual', and the user is recorded
        self.assertEqual(data['source'], 'manual')
        self.assertEqual(data['user'], self.user.pk)

        # Missing bound is filled in, and converted values are calculated
        self.assertEqual(data['min_cost'], 1.25)
        self.assertEqual(data['max_cost'], 1.25)
        self.assertEqual(data['converted_currency'], 'USD')
        self.assertEqual(data['converted_min_cost'], 1.25)
        self.assertFalse(data['estimated'])

        summary = StockItemCost.objects.get(stock_item=self.other_item)
        self.assertEqual(summary.min_cost, Decimal('6.25'))

        # An explicit source is retained, and converted values cannot be set
        response = self.post(
            self.LIST_URL,
            {
                'stock_item': self.other_item.pk,
                'cost_type': CostType.ADJUSTMENT.value,
                'min_cost': -2,
                'max_cost': -1,
                'source': 'plugin:my-plugin',
                'estimated': True,
                'converted_min_cost': 999,
            },
        )

        self.assertEqual(response.data['source'], 'plugin:my-plugin')
        self.assertEqual(response.data['converted_min_cost'], -2)

        summary.refresh_from_db()
        self.assertEqual(summary.min_cost, Decimal('4.25'))
        self.assertEqual(summary.max_cost, Decimal('5.25'))
        self.assertTrue(summary.estimated)

    def test_user_detail_queries(self):
        """The 'user_detail' field is prefetched (no additional queries per row)."""
        from django.contrib.auth.models import User
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        def count_queries(limit):
            with CaptureQueriesContext(connection) as ctx:
                response = self.get(
                    self.LIST_URL, {'user_detail': True, 'limit': limit}
                )

            results = response.data['results']
            self.assertEqual(len(results), limit)

            for row in results:
                self.assertEqual(row['user_detail']['pk'], row['user'])

            return len(ctx.captured_queries)

        # Create entries against a number of different users
        for idx in range(8):
            StockItemCostEntry.objects.create_cost(
                self.other_item,
                CostType.FEES,
                CostSource.MANUAL,
                min_cost=idx,
                user=User.objects.create(username=f'cost-user-{idx}'),
            )

        # Warm up (first request performs one-off session / settings queries)
        count_queries(1)

        self.assertEqual(count_queries(2), count_queries(8))

    def test_invalid_source(self):
        """The source must follow the naming convention."""
        for source in ['my-plugin', 'plugin:', 'plugin:Bad Slug']:
            response = self.post(
                self.LIST_URL,
                {'stock_item': self.item.pk, 'min_cost': 1, 'source': source},
                expected_code=400,
            )
            self.assertIn('source', response.data)

        response = self.patch(
            self.detail_url(self.entry.pk), {'source': 'nope'}, expected_code=400
        )
        self.assertIn('source', response.data)

    def test_create_invalid(self):
        """Test that invalid cost entries are rejected."""
        n = StockItemCostEntry.objects.count()

        response = self.post(
            self.LIST_URL,
            {'stock_item': self.item.pk, 'cost_type': CostType.PURCHASE.value},
            expected_code=400,
        )
        self.assertIn('min_cost', response.data)

        response = self.post(
            self.LIST_URL,
            {'stock_item': self.item.pk, 'min_cost': 5, 'max_cost': 4},
            expected_code=400,
        )
        self.assertIn('max_cost', response.data)

        response = self.post(
            self.LIST_URL,
            {'stock_item': self.item.pk, 'min_cost': 5, 'cost_type': 999},
            expected_code=400,
        )
        self.assertIn('cost_type', response.data)

        response = self.post(
            self.LIST_URL,
            {'stock_item': self.item.pk, 'min_cost': 5, 'currency': 'XYZ'},
            expected_code=400,
        )
        self.assertIn('currency', response.data)

        self.assertEqual(StockItemCostEntry.objects.count(), n)

    def test_update(self):
        """Test editing a cost entry via the API."""
        url = self.detail_url(self.entry.pk)

        response = self.patch(url, {'max_cost': 15, 'notes': 'Updated'})

        self.assertEqual(response.data['min_cost'], 10)
        self.assertEqual(response.data['max_cost'], 15)
        self.assertEqual(response.data['converted_max_cost'], 15)

        summary = StockItemCost.objects.get(stock_item=self.item)
        self.assertEqual(summary.min_cost, Decimal('11'))
        self.assertEqual(summary.max_cost, Decimal('16'))

        # Invalid range is rejected
        self.patch(url, {'min_cost': 20}, expected_code=400)

        # The stock item cannot be changed
        response = self.patch(url, {'stock_item': self.other_item.pk})
        self.assertEqual(response.data['stock_item'], self.item.pk)

        self.entry.refresh_from_db()
        self.assertEqual(self.entry.stock_item, self.item)
        self.assertEqual(self.entry.max_cost, Decimal('15'))

    def test_delete(self):
        """Test deleting a cost entry via the API."""
        self.delete(self.detail_url(self.entry.pk))

        self.assertFalse(StockItemCostEntry.objects.filter(pk=self.entry.pk).exists())

        summary = StockItemCost.objects.get(stock_item=self.item)
        self.assertEqual(summary.min_cost, Decimal('1'))
        self.assertEqual(summary.max_cost, Decimal('1'))

    def test_status_codes(self):
        """Test the cost type status code endpoint."""
        response = self.get(reverse('api-stock-cost-entry-status-codes'))

        self.assertEqual(response.data['status_class'], 'CostType')
        self.assertIn('PURCHASE', response.data['values'])

    def test_permissions(self):
        """Both the 'pricing' and 'stock' roles are required."""
        url = self.detail_url(self.entry.pk)

        data = {'stock_item': self.item.pk, 'min_cost': 1}

        def check(expected_codes):
            """Check the response code for each request type."""
            self.get(self.LIST_URL, expected_code=expected_codes['view'])
            self.get(url, expected_code=expected_codes['view'])
            self.post(self.LIST_URL, data, expected_code=expected_codes['add'])
            self.patch(url, {'notes': 'x'}, expected_code=expected_codes['change'])

            # Run delete last, as it may remove the entry
            self.delete(url, expected_code=expected_codes['delete'])

        denied = dict.fromkeys(self.ALL_PERMISSIONS, 403)

        # No roles
        self.set_roles()
        check(denied)

        # Only the 'pricing' role
        self.set_roles(*[f'pricing.{perm}' for perm in self.ALL_PERMISSIONS])
        check(denied)

        # Only the 'stock' role
        self.set_roles(*[f'stock.{perm}' for perm in self.ALL_PERMISSIONS])
        check(denied)

        # View permission for both roles - read only
        self.set_roles('pricing.view', 'stock.view')
        check({'view': 200, 'add': 403, 'change': 403, 'delete': 403})

        # Write permission for 'pricing', but only view for 'stock'
        self.set_roles(
            *[f'pricing.{perm}' for perm in self.ALL_PERMISSIONS], 'stock.view'
        )
        check({'view': 200, 'add': 403, 'change': 403, 'delete': 403})

        # Note: a RuleSet with 'add' or 'delete' permission always has 'change' permission
        # (see RuleSet.save), so 'stock.change' is the effective requirement for any write

        # Only 'stock.change' is required (in addition to 'stock.view') for any write operation
        self.set_roles(
            *[f'pricing.{perm}' for perm in self.ALL_PERMISSIONS],
            'stock.view',
            'stock.change',
        )
        check({'view': 200, 'add': 201, 'change': 200, 'delete': 204})

        # The 'pricing' permission must still match the request type
        self.entry = StockItemCostEntry.objects.create_cost(
            self.item, CostType.PURCHASE, CostSource.MANUAL, min_cost=1
        )
        url = self.detail_url(self.entry.pk)
        self.set_roles('pricing.view', 'pricing.change', 'stock.view', 'stock.change')
        check({'view': 200, 'add': 403, 'change': 200, 'delete': 403})

    def test_oauth2_scopes(self):
        """OAuth2 tokens require the matching 'pricing' scope, plus 'stock' view (read) or change (write)."""
        scopes = StockItemCostEntryList.required_alternate_scopes

        self.assertEqual(scopes['GET'], [['r:view:pricing', 'r:view:stock']])
        self.assertEqual(scopes['POST'], [['r:add:pricing', 'r:change:stock']])
        self.assertEqual(scopes['PUT'], [['r:change:pricing', 'r:change:stock']])
        self.assertEqual(scopes['PATCH'], [['r:change:pricing', 'r:change:stock']])
        self.assertEqual(scopes['DELETE'], [['r:delete:pricing', 'r:change:stock']])
        self.assertEqual(scopes['OPTIONS'], [['g:read']])


class StockItemPricingDetailTests(StockItemCostApiTestBase):
    """Tests for the optional 'pricing_detail' field on the StockItem API."""

    def test_pricing_detail(self):
        """The cost summary is only included on request, for users with the 'pricing' view role."""
        url = reverse('api-stock-detail', kwargs={'pk': self.item.pk})

        # Not included by default
        self.assertNotIn('pricing_detail', self.get(url).data)

        data = self.get(url, {'pricing_detail': True}).data['pricing_detail']

        self.assertEqual(data['currency'], 'USD')
        self.assertEqual(data['min_cost'], 11)
        self.assertEqual(data['max_cost'], 13)
        self.assertTrue(data['estimated'])
        self.assertFalse(data['incomplete'])
        self.assertNotIn('stock_item', data)

        # No cost data for this stock item
        no_cost = StockItem.objects.exclude(
            pk__in=[self.item.pk, self.other_item.pk]
        ).first()

        response = self.get(
            reverse('api-stock-detail', kwargs={'pk': no_cost.pk}),
            {'pricing_detail': True},
        )
        self.assertIsNone(response.data['pricing_detail'])

        # Users without the 'pricing' view role never see the field (and get no error)
        self.set_roles(*[f'stock.{perm}' for perm in self.ALL_PERMISSIONS])

        response = self.get(url, {'pricing_detail': True})
        self.assertNotIn('pricing_detail', response.data)

        response = self.get(reverse('api-stock-list'), {'pricing_detail': True})

        for row in response.data:
            self.assertNotIn('pricing_detail', row)

    def test_unit_cost_filter_ordering(self):
        """Stock items can be filtered and ordered by unit cost (with the 'pricing' view role)."""
        url = reverse('api-stock-list')

        costed = [self.other_item.pk, self.item.pk]  # 5 USD, 11 - 13 USD
        total = StockItem.objects.count()

        def pks(**params):
            return [row['pk'] for row in self.get(url, params).data]

        self.assertEqual(sorted(pks(has_unit_cost=True)), sorted(costed))

        uncosted = pks(has_unit_cost=False)
        self.assertEqual(len(uncosted), total - 2)
        self.assertFalse(set(uncosted) & set(costed))

        self.assertEqual(pks(has_unit_cost=True, ordering='unit_cost'), costed)
        self.assertEqual(pks(has_unit_cost=True, ordering='-unit_cost'), costed[::-1])

        # Without the 'pricing' view role, the filter and ordering are ignored
        self.set_roles(*[f'stock.{perm}' for perm in self.ALL_PERMISSIONS])

        self.assertEqual(len(pks(has_unit_cost=True)), total)
        self.assertEqual(len(pks(has_unit_cost=False)), total)

        self.assertEqual(pks(ordering='-unit_cost'), pks())

    def test_pricing_detail_queries(self):
        """The cost summary is prefetched (a single additional query, regardless of the number of rows)."""
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        url = reverse('api-stock-list')

        # Give every stock item a cost summary
        StockItemCostEntry.objects.bulk_create_costs([
            {'stock_item': item, 'min_cost': 1, 'source': CostSource.MANUAL}
            for item in StockItem.objects.all()
        ])

        def count_queries(limit, pricing_detail):
            with CaptureQueriesContext(connection) as ctx:
                response = self.get(
                    url, {'pricing_detail': pricing_detail, 'limit': limit}
                )

            results = response.data['results']
            self.assertEqual(len(results), limit)

            for row in results:
                self.assertEqual('pricing_detail' in row, pricing_detail)

            return len(ctx.captured_queries)

        # Warm up (first request performs one-off session / settings queries)
        count_queries(1, True)

        # The overhead (prefetch + 'pricing' role check) does not depend on the number of rows
        overhead = [
            count_queries(limit, True) - count_queries(limit, False) for limit in [2, 8]
        ]

        self.assertEqual(overhead[0], overhead[1])
        self.assertLessEqual(overhead[0], 3)


class StockItemCostApiTests(StockItemCostApiTestBase):
    """Tests for the (read-only) StockItemCost summary API endpoints."""

    LIST_URL = reverse('api-stock-cost-list')

    def test_list(self):
        """Test listing and filtering cost summaries."""
        response = self.get(self.LIST_URL)
        self.assertEqual(len(response.data), 2)

        response = self.get(self.LIST_URL, {'stock_item': self.item.pk})
        self.assertEqual(len(response.data), 1)

        data = response.data[0]
        self.assertEqual(data['currency'], 'USD')
        self.assertEqual(data['min_cost'], 11)
        self.assertEqual(data['max_cost'], 13)
        self.assertTrue(data['estimated'])
        self.assertFalse(data['incomplete'])

        response = self.get(self.LIST_URL, {'estimated': False})
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['stock_item'], self.other_item.pk)

    def test_read_only(self):
        """Cost summaries cannot be created or edited via the API."""
        summary = StockItemCost.objects.get(stock_item=self.item)
        url = reverse('api-stock-cost-detail', kwargs={'pk': summary.pk})

        self.get(url)

        self.post(self.LIST_URL, {'stock_item': self.item.pk}, expected_code=405)
        self.patch(url, {'min_cost': 1}, expected_code=405)
        self.delete(url, expected_code=405)

        summary.refresh_from_db()
        self.assertEqual(summary.min_cost, Decimal('11'))

    def test_permissions(self):
        """Both the 'pricing' and 'stock' roles are required."""
        summary = StockItemCost.objects.get(stock_item=self.item)
        url = reverse('api-stock-cost-detail', kwargs={'pk': summary.pk})

        for roles in [[], ['pricing.view'], ['stock.view']]:
            self.set_roles(*roles)
            self.get(self.LIST_URL, expected_code=403)
            self.get(url, expected_code=403)

        self.set_roles('pricing.view', 'stock.view')
        self.get(self.LIST_URL, expected_code=200)
        self.get(url, expected_code=200)

        self.assertEqual(
            StockItemCostList.required_alternate_scopes['GET'],
            [['r:view:pricing', 'r:view:stock']],
        )
