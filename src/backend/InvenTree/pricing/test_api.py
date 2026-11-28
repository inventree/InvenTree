"""API unit tests for the 'pricing' app."""

import json
from decimal import Decimal

from django.core.files.base import ContentFile
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
            cls.item, CostType.LANDED, CostSource.MANUAL, min_cost=1
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
            'source_text',
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

        # Human readable source labels
        # Note: No plugin with the 'test' slug is installed - the slug is displayed
        self.assertEqual(response.data[0]['source_text'], 'Plugin: test')

        response = self.get(self.LIST_URL, {'source': CostSource.MANUAL})
        self.assertEqual(len(response.data), 2)

        for entry in response.data:
            self.assertEqual(entry['source_text'], 'Manual')

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
        self.assertNotIn('estimated', data)

        summary = StockItemCost.objects.get(stock_item=self.other_item)
        self.assertEqual(summary.min_cost, Decimal('6.25'))

        # The source, source data and converted values cannot be set via the API
        response = self.post(
            self.LIST_URL,
            {
                'stock_item': self.other_item.pk,
                'cost_type': CostType.ADJUSTMENT.value,
                'min_cost': -2,
                'max_cost': -1,
                'source': CostSource.PURCHASE_ORDER,
                'source_data': {'purchase_order': 99},
                'converted_min_cost': 999,
            },
        )

        self.assertEqual(response.data['source'], 'manual')
        self.assertIsNone(response.data['source_data'])
        self.assertEqual(response.data['converted_min_cost'], -2)

        summary.refresh_from_db()
        self.assertEqual(summary.min_cost, Decimal('4.25'))
        self.assertEqual(summary.max_cost, Decimal('5.25'))

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

    def test_source_read_only(self):
        """The source of an entry cannot be set (or changed) via the API."""
        for source in [CostSource.LEGACY, 'plugin:my-plugin', 'not-a-source']:
            response = self.post(
                self.LIST_URL,
                {'stock_item': self.item.pk, 'min_cost': 1, 'source': source},
                expected_code=201,
            )
            self.assertEqual(response.data['source'], CostSource.MANUAL)

        # An entry recorded automatically keeps its source (and source data) on update
        entry = StockItemCostEntry.objects.create_cost(
            self.item,
            CostType.PURCHASE,
            CostSource.PURCHASE_ORDER,
            min_cost=1,
            source_data={'purchase_order': 1},
        )

        response = self.patch(
            self.detail_url(entry.pk),
            {
                'source': CostSource.MANUAL,
                'source_data': {'purchase_order': 99},
                'min_cost': 2,
                'max_cost': 2,
            },
        )

        self.assertEqual(response.data['source'], CostSource.PURCHASE_ORDER)
        self.assertEqual(response.data['source_data'], {'purchase_order': 1})
        self.assertEqual(response.data['min_cost'], 2)

        entry.refresh_from_db()
        self.assertEqual(entry.source, CostSource.PURCHASE_ORDER)
        self.assertEqual(entry.source_data, {'purchase_order': 1})

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

    def test_export(self):
        """Cost entries can be exported (with the same filtering as the list endpoint)."""
        with self.export_data(
            self.LIST_URL, params={'stock_item': self.item.pk}
        ) as data_file:
            data = self.process_csv(
                data_file,
                required_cols=[
                    'Stock Item',
                    'Cost Type',
                    'Source',
                    'Minimum Cost',
                    'Maximum Cost',
                    'Currency',
                ],
                required_rows=self.item.cost_entries.count(),
            )

        self.assertEqual(
            sorted(Decimal(row['Minimum Cost']) for row in data),
            [Decimal(1), Decimal(10)],
        )

        for row in data:
            self.assertEqual(int(row['Stock Item']), self.item.pk)

    def test_export_permissions(self):
        """Exporting cost entries requires the same roles as viewing them."""
        for roles in [[], ['stock.view'], ['pricing.view']]:
            with self.subTest(roles=roles):
                self.set_roles(*roles)
                self.export_data(self.LIST_URL, expected_code=403)

        self.set_roles('pricing.view', 'stock.view')

        with self.export_data(self.LIST_URL) as data_file:
            self.process_csv(
                data_file, required_rows=StockItemCostEntry.objects.count()
            )

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


class StockItemCostImportTests(StockItemCostApiTestBase):
    """Importing stock item cost entries from a file, via the data importer API."""

    SESSION_URL = reverse('api-importer-session-list')

    def create_session(self, csv: str, expected_code=201, **kwargs):
        """Create an import session for cost entries, from the provided CSV data."""
        data = {
            'model_type': 'stockitemcostentry',
            'data_file': ContentFile(csv.encode(), 'costs.csv'),
        }

        for key, value in kwargs.items():
            data[key] = json.dumps(value) if isinstance(value, dict) else value

        return self.post(
            self.SESSION_URL, data, format='multipart', expected_code=expected_code
        ).data

    def lookup_by_id(self, session):
        """Match the 'Stock Item' column of a session against stock item IDs only.

        By default, values are also matched against stock item serial numbers
        (StockItem.IMPORT_ID_FIELDS) - so a value which is both a valid ID and a
        serial number is ambiguous, and the row is rejected.
        """
        for mapping in session['column_mappings']:
            if mapping['field'] == 'stock_item':
                response = self.patch(
                    reverse(
                        'api-importer-mapping-detail', kwargs={'pk': mapping['pk']}
                    ),
                    {'lookup_field': 'pk'},
                    expected_code=None,
                )
                self.assertEqual(response.status_code, 200, response.data)

    def accept_fields(self, session, expected_code=200):
        """Accept the (automatic) column mapping of a session."""
        return self.post(
            reverse('api-import-session-accept-fields', kwargs={'pk': session['pk']}),
            expected_code=expected_code,
        )

    def rows(self, session) -> list:
        """Return the rows of an import session."""
        return self.get(
            reverse('api-importer-row-list'), {'session': session['pk']}
        ).data

    def accept_rows(self, session, rows, expected_code=201):
        """Import the provided rows of a session."""
        return self.post(
            reverse('api-import-session-accept-rows', kwargs={'pk': session['pk']}),
            {'rows': [row['pk'] for row in rows]},
            expected_code=expected_code,
        )

    def import_all(self, csv: str, **kwargs) -> list:
        """Run an import from start to finish, and return the rows."""
        session = self.create_session(csv, **kwargs)
        self.lookup_by_id(session)
        self.accept_fields(session)

        rows = self.rows(session)

        for row in rows:
            self.assertTrue(row['valid'], row['errors'])

        self.accept_rows(session, rows)

        return rows

    def test_importable_fields(self):
        """Only the user-editable fields of a cost entry can be imported."""
        session = self.create_session('Notes\nx\n')

        fields = set(session['available_fields'].keys())

        for field in ['stock_item', 'cost_type', 'currency', 'min_cost', 'max_cost']:
            self.assertIn(field, fields)

        # Recorded automatically - cannot be imported
        for field in [
            'source',
            'source_data',
            'user',
            'date',
            'converted_currency',
            'converted_min_cost',
            'converted_max_cost',
            'cost_type_text',
            'source_text',
        ]:
            self.assertNotIn(field, fields)

    def test_import_for_stock_item(self):
        """Import costs against a single stock item (as from the stock item costs table)."""
        item = self.other_item
        existing = set(item.cost_entries.values_list('pk', flat=True))

        csv = (
            'Cost Type,Minimum Cost,Maximum Cost,Currency,Notes\n'
            'Landed,2.5,,USD,Freight\n'
            'Purchase,10,12,USD,Supplier estimate\n'
            '60,-1,,USD,Rebate\n'
        )

        # The stock item is provided as an override (not in the file)
        self.import_all(csv, field_overrides={'stock_item': item.pk})

        entries = item.cost_entries.exclude(pk__in=existing).order_by('pk')
        self.assertEqual(entries.count(), 3)

        landed, purchase, rebate = entries

        self.assertEqual(landed.cost_type, CostType.LANDED)
        self.assertEqual(landed.min_cost, Decimal('2.5'))
        self.assertEqual(landed.max_cost, Decimal('2.5'))
        self.assertEqual(landed.notes, 'Freight')

        self.assertEqual(purchase.cost_type, CostType.PURCHASE)
        self.assertEqual(purchase.min_cost, Decimal(10))
        self.assertEqual(purchase.max_cost, Decimal(12))

        self.assertEqual(rebate.cost_type, CostType.ADJUSTMENT)
        self.assertEqual(rebate.min_cost, Decimal(-1))

        for entry in entries:
            # Imported entries are manual entries, attributed to the importing user
            self.assertEqual(entry.source, CostSource.MANUAL)
            self.assertIsNone(entry.source_data)
            self.assertEqual(entry.user, self.user)
            self.assertEqual(entry.currency, 'USD')
            self.assertEqual(entry.converted_currency, 'USD')

        # The cost summary includes the imported entries (existing entry = 5 USD)
        summary = StockItemCost.objects.get(stock_item=item)
        self.assertEqual(summary.min_cost, Decimal('16.5'))
        self.assertEqual(summary.max_cost, Decimal('18.5'))
        self.assertFalse(summary.incomplete)

        # Other stock items are unaffected
        self.assertEqual(self.item.cost_entries.count(), 2)

    def test_import_override_ignores_file_column(self):
        """A stock item override takes precedence over a 'Stock Item' column in the file."""
        csv = f'Stock Item,Cost Type,Minimum Cost,Currency\n{self.item.pk},Fees,3,USD\n'

        self.import_all(csv, field_overrides={'stock_item': self.other_item.pk})

        self.assertTrue(
            self.other_item.cost_entries.filter(cost_type=CostType.FEES).exists()
        )
        self.assertFalse(
            self.item.cost_entries.filter(cost_type=CostType.FEES).exists()
        )

    def test_import_multiple_stock_items(self):
        """Import costs for multiple stock items (as from the admin center)."""
        csv = (
            'Stock Item,Cost Type,Minimum Cost,Maximum Cost,Currency\n'
            f'{self.item.pk},Landed,1,2,USD\n'
            f'{self.other_item.pk},Landed,3,,USD\n'
        )

        self.import_all(csv)

        self.assertEqual(
            self.item.cost_entries.filter(cost_type=CostType.LANDED).count(), 2
        )
        self.assertEqual(
            self.other_item.cost_entries.filter(cost_type=CostType.LANDED).count(), 1
        )

        # 10-12 (purchase) + 1 (existing landed) + 1-2 (imported)
        summary = StockItemCost.objects.get(stock_item=self.item)
        self.assertEqual(summary.min_cost, Decimal(12))
        self.assertEqual(summary.max_cost, Decimal(15))

        summary = StockItemCost.objects.get(stock_item=self.other_item)
        self.assertEqual(summary.min_cost, Decimal(8))
        self.assertEqual(summary.max_cost, Decimal(8))

    def test_ambiguous_stock_item(self):
        """A stock item value which matches both an ID and a serial number is rejected."""
        serial = StockItem.objects.exclude(serial=None).exclude(serial='').first()
        self.assertIsNotNone(serial)

        # An ID which is also another item's serial number
        item = StockItem.objects.filter(pk=int(serial.serial)).first()
        self.assertIsNotNone(item)
        self.assertNotEqual(item.pk, serial.pk)

        csv = f'Stock Item,Cost Type,Minimum Cost,Currency\n{item.pk},Landed,1,USD\n'

        session = self.create_session(csv)
        self.accept_fields(session)

        row = self.rows(session)[0]
        self.assertFalse(row['valid'])
        self.assertIn('Multiple matches', str(row['errors']['stock_item']))

        # Selecting the 'ID' lookup field resolves the ambiguity
        self.import_all(csv)
        self.assertTrue(item.cost_entries.filter(cost_type=CostType.LANDED).exists())

    def test_import_unconverted(self):
        """An imported cost without an exchange rate is stored, and the summary is incomplete."""
        from django.core.cache import cache

        from djmoney.contrib.exchange.models import Rate

        # Ensure that no exchange rates are available
        Rate.objects.all().delete()
        cache.clear()

        csv = 'Cost Type,Minimum Cost,Currency\nLanded,4,NZD\n'

        self.import_all(csv, field_overrides={'stock_item': self.other_item.pk})

        entry = self.other_item.cost_entries.get(currency='NZD')
        self.assertEqual(entry.min_cost, Decimal(4))
        self.assertIsNone(entry.converted_min_cost)

        summary = StockItemCost.objects.get(stock_item=self.other_item)
        self.assertTrue(summary.incomplete)
        self.assertEqual(summary.min_cost, Decimal(5))

    def test_import_source_column_ignored(self):
        """Source columns in the file cannot be mapped - imported entries are always manual."""
        csv = (
            'Cost Type,Minimum Cost,Currency,Source,User\n'
            f'Purchase,1,USD,purchase_order,{self.user.pk}\n'
        )

        session = self.create_session(
            csv, field_overrides={'stock_item': self.other_item.pk}
        )

        mapped = {
            mapping['field']
            for mapping in session['column_mappings']
            if mapping['column']
        }
        self.assertNotIn('source', mapped)
        self.assertNotIn('user', mapped)

        self.accept_fields(session)
        self.accept_rows(session, self.rows(session))

        entry = self.other_item.cost_entries.order_by('-pk').first()
        self.assertEqual(entry.source, CostSource.MANUAL)

    def test_import_invalid_rows(self):
        """Invalid rows are reported, and cannot be imported."""
        csv = (
            'Stock Item,Cost Type,Minimum Cost,Maximum Cost,Currency\n'
            f'{self.item.pk},Landed,5,2,USD\n'
            f'{self.item.pk},Not a cost type,1,,USD\n'
            ',Landed,1,,USD\n'
            '999999,Landed,1,,USD\n'
            f'{self.item.pk},Landed,,,USD\n'
            f'{self.item.pk},Landed,1,,USD\n'
        )

        session = self.create_session(csv)
        self.lookup_by_id(session)
        self.accept_fields(session)

        rows = self.rows(session)
        self.assertEqual(len(rows), 6)

        # Only the last row is valid
        self.assertEqual([row['valid'] for row in rows], [False] * 5 + [True])

        self.assertIn('max_cost', rows[0]['errors'])
        self.assertIn('cost_type', rows[1]['errors'])
        self.assertIn('stock_item', rows[2]['errors'])
        self.assertIn('stock_item', rows[3]['errors'])
        self.assertIn('min_cost', rows[4]['errors'])

        N = StockItemCostEntry.objects.count()

        # Invalid rows are not imported
        self.accept_rows(session, rows[:1], expected_code=400)
        self.assertEqual(StockItemCostEntry.objects.count(), N)

        self.accept_rows(session, rows[5:])
        self.assertEqual(StockItemCostEntry.objects.count(), N + 1)

    def test_update_existing(self):
        """Existing entries can be updated by ID - the source is retained, and the item cannot change."""
        entry = StockItemCostEntry.objects.create_cost(
            self.item,
            CostType.PURCHASE,
            CostSource.PURCHASE_ORDER,
            min_cost=4,
            currency='USD',
            source_data={'purchase_order': 1},
        )

        # Note: Both bounds are provided (a minimum above the existing maximum is invalid)
        csv = (
            'ID,Stock Item,Minimum Cost,Maximum Cost,Notes\n'
            f'{entry.pk},{self.other_item.pk},6,7,Corrected\n'
        )

        self.import_all(csv, update_records=True)

        entry.refresh_from_db()

        self.assertEqual(entry.min_cost, Decimal(6))
        self.assertEqual(entry.max_cost, Decimal(7))
        self.assertEqual(entry.notes, 'Corrected')
        self.assertEqual(entry.stock_item, self.item)
        self.assertEqual(entry.source, CostSource.PURCHASE_ORDER)
        self.assertEqual(entry.source_data, {'purchase_order': 1})
        self.assertEqual(entry.user, self.user)

    def test_permissions(self):
        """Importing requires the 'pricing' change and 'stock' change permissions."""
        csv = 'Cost Type,Minimum Cost,Currency\nLanded,1,USD\n'
        overrides = {'stock_item': self.other_item.pk}

        cases = [
            ([], 403),
            # The 'pricing' role alone is not sufficient
            ([f'pricing.{perm}' for perm in self.ALL_PERMISSIONS], 403),
            (['pricing.change', 'pricing.add', 'stock.view'], 403),
            # The 'stock' role alone is not sufficient
            ([f'stock.{perm}' for perm in self.ALL_PERMISSIONS], 403),
            (['pricing.view', 'stock.change'], 403),
            # Both are required
            (['pricing.change', 'stock.change'], 200),
        ]

        for roles, expected_code in cases:
            with self.subTest(roles=roles):
                self.set_roles(*roles)
                session = self.create_session(csv, field_overrides=overrides)
                self.accept_fields(session, expected_code=expected_code)

        # Losing the 'stock' role before the rows are imported also prevents the import
        rows = self.rows(session)
        self.set_roles('pricing.change')
        self.accept_rows(session, rows, expected_code=403)

        N = StockItemCostEntry.objects.count()

        self.set_roles('pricing.change', 'stock.change')
        self.accept_rows(session, rows)

        self.assertEqual(StockItemCostEntry.objects.count(), N + 1)


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
        self.assertFalse(data['incomplete'])

        # An estimate is recorded as a cost range - there is no separate 'estimated' field
        self.assertNotIn('estimated', data)

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
