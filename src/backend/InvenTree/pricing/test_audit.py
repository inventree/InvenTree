"""Audit log tests for the pricing models."""

from django.contrib.contenttypes.models import ContentType
from django.urls import reverse

from audit.models import AuditLogEntry
from InvenTree.unit_test import InvenTreeAPITestCase
from part.models import Part
from pricing.models import (
    CostSource,
    PartInternalPriceBreak,
    PartPricing,
    PartSellPriceBreak,
    StockItemCostEntry,
)
from pricing.status_codes import CostType
from stock.models import StockItem

ACTION = AuditLogEntry.Action


class PricingAuditTest(InvenTreeAPITestCase):
    """Audit tests for PartPricing and the part price break models."""

    roles = [
        'part.view',
        'pricing.view',
        'pricing.add',
        'pricing.change',
        'pricing.delete',
    ]

    @classmethod
    def setUpTestData(cls):
        """Create test data."""
        super().setUpTestData()

        cls.part = Part.objects.create(
            name='Widget', description='A widget', salable=True
        )

    def entries(self, model, pk=None, **filters):
        """Return audit entries for a given model (and object)."""
        queryset = AuditLogEntry.objects.filter(
            content_type=ContentType.objects.get_for_model(model), **filters
        )

        if pk is not None:
            queryset = queryset.filter(object_pk=str(pk))

        return queryset

    def part_history(self):
        """Return the audit history for the part (including pricing entries)."""
        return self.get(
            reverse('api-audit-log-list'),
            {'model_type': 'part.part', 'model_id': self.part.pk},
        ).data

    def check_price_breaks(self, model, list_url, detail_url):
        """Create / update / delete a price break via the API, and check the audit trail."""
        pk = self.post(
            reverse(list_url),
            {
                'part': self.part.pk,
                'quantity': 10,
                'price': '1.50',
                'price_currency': 'USD',
            },
        ).data['pk']

        url = reverse(detail_url, kwargs={'pk': pk})
        self.patch(url, {'price': '1.25'})

        self.assertEqual(
            model.objects.get(pk=pk).__str__(), f'{self.part} - $1.25 @ 10'
        )

        self.delete(url)

        entries = self.entries(model, pk)

        self.assertEqual(
            sorted(entries.values_list('action', flat=True)),
            [ACTION.CREATE, ACTION.UPDATE, ACTION.DELETE],
        )

        for entry in entries:
            self.assertEqual(entry.actor, self.user)
            self.assertEqual(entry.parent_object_pk, str(self.part.pk))
            self.assertNotIn(' object (', entry.object_repr)

        update = entries.get(action=ACTION.UPDATE)
        self.assertEqual(update.changes_dict['price'], ['$1.50', '$1.25'])

        label = f'{model._meta.app_label}.{model._meta.model_name}'

        self.assertEqual(
            sorted(
                e['action'] for e in self.part_history() if e['model_type'] == label
            ),
            [ACTION.CREATE, ACTION.UPDATE, ACTION.DELETE],
        )

    def test_sale_price_breaks(self):
        """Sale price break changes are recorded against the part."""
        self.check_price_breaks(
            PartSellPriceBreak, 'api-part-sale-price-list', 'api-part-sale-price-detail'
        )

    def test_internal_price_breaks(self):
        """Internal price break changes are recorded against the part."""
        self.check_price_breaks(
            PartInternalPriceBreak,
            'api-part-internal-price-list',
            'api-part-internal-price-detail',
        )

    def test_pricing_overrides(self):
        """Only the user-specified pricing overrides are recorded."""
        url = reverse('api-part-pricing', kwargs={'pk': self.part.pk})

        # Creating the pricing record (with no overrides) is not recorded
        # Note: Part.pricing returns an unsaved instance, which is saved on first update
        pricing = self.part.pricing
        pricing.save()
        self.assertFalse(self.entries(PartPricing).exists())

        self.patch(url, {'override_max': 25, 'override_max_currency': 'USD'})

        entry = self.entries(PartPricing, pricing.pk, action=ACTION.UPDATE).get()

        self.assertEqual(entry.actor, self.user)
        self.assertEqual(entry.parent_object_pk, str(self.part.pk))
        self.assertEqual(entry.changes_dict['override_max'], [None, '$25.00'])
        self.assertEqual(entry.object_repr, f'{self.part} pricing')

        # Only override fields are ever recorded
        for field in entry.changes_dict:
            self.assertTrue(field.startswith('override_'), field)

    def test_recalculation_not_recorded(self):
        """Automatic pricing recalculation (cached values) is not recorded."""
        PartSellPriceBreak.objects.create(part=self.part, quantity=1, price=5)

        pricing = self.part.pricing
        pricing.update_pricing()

        pricing.refresh_from_db()
        self.assertIsNotNone(pricing.sale_price_min)

        self.assertFalse(self.entries(PartPricing).exists())

    def test_pricing_permission(self):
        """Pricing entries require the 'pricing' role, even via the part history."""
        PartSellPriceBreak.objects.create(part=self.part, quantity=1, price=5)

        def pricing_entries():
            return [
                e for e in self.part_history() if e['model_type'].startswith('pricing.')
            ]

        self.assertEqual(len(pricing_entries()), 1)

        # Remove the pricing role (keep 'part.view')
        self.clearRoles()
        self.assignRole('part.view')

        self.assertEqual(pricing_entries(), [])


class StockItemCostAuditPermissionTest(InvenTreeAPITestCase):
    """Audit history of stock item cost entries requires permission to view the stock item.

    Regression test: the cost entry API requires both the 'pricing' and 'stock' roles,
    but the audit history of cost entries was visible with only the 'pricing' role.
    """

    roles = ['pricing.view', 'stock.view']

    @classmethod
    def setUpTestData(cls):
        """Create a stock item with a cost entry (and an update to it)."""
        super().setUpTestData()

        part = Part.objects.create(name='Widget', description='A widget')
        cls.item = StockItem.objects.create(part=part, quantity=10)

        cls.entry = StockItemCostEntry.objects.create_cost(
            cls.item, CostType.PURCHASE, CostSource.MANUAL, min_cost=10, currency='USD'
        )

        StockItemCostEntry.objects.update_cost(cls.entry, min_cost=12, max_cost=12)

    def audit_entries(self):
        """Return the audit log entries for the cost entry model."""
        return AuditLogEntry.objects.filter(
            content_type=ContentType.objects.get_for_model(StockItemCostEntry)
        )

    def cost_entries(self, params=None):
        """Return the cost entries visible via the audit log API."""
        return [
            e
            for e in self.get(reverse('api-audit-log-list'), params or {}).data
            if e['model_type'] == 'pricing.stockitemcostentry'
        ]

    def check_visible(self, visible: bool):
        """Check whether the cost entry history is visible to the user."""
        expected = 2 if visible else 0

        # Global audit log
        self.assertEqual(len(self.cost_entries()), expected)

        # Filtered by model type
        self.assertEqual(
            len(self.cost_entries({'model_type': 'pricing.stockitemcostentry'})),
            expected,
        )

        # History of the cost entry itself
        self.assertEqual(
            len(
                self.cost_entries({
                    'model_type': 'pricing.stockitemcostentry',
                    'model_id': self.entry.pk,
                })
            ),
            expected,
        )

        # Detail endpoint
        for entry in self.audit_entries():
            self.get(
                reverse('api-audit-log-detail', kwargs={'pk': entry.pk}),
                expected_code=200 if visible else 404,
            )

    def test_parent_permission(self):
        """Cost entry history requires both the 'pricing' and 'stock' view roles."""
        self.assertEqual(self.audit_entries().count(), 2)

        # Both roles - visible (including via the history of the stock item)
        self.check_visible(True)

        self.assertEqual(
            len(
                self.cost_entries({
                    'model_type': 'stock.stockitem',
                    'model_id': self.item.pk,
                })
            ),
            2,
        )

        # Only the 'pricing' role - hidden
        self.clearRoles()
        self.assignRole('pricing.view')
        self.check_visible(False)

        # Only the 'stock' role - hidden
        self.clearRoles()
        self.assignRole('stock.view')
        self.check_visible(False)

        self.assertEqual(
            self.cost_entries({
                'model_type': 'stock.stockitem',
                'model_id': self.item.pk,
            }),
            [],
        )
