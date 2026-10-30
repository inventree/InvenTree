"""Audit log tests for the pricing models."""

from django.contrib.contenttypes.models import ContentType
from django.urls import reverse

from audit.models import AuditLogEntry
from InvenTree.unit_test import InvenTreeAPITestCase
from part.models import Part
from pricing.models import PartInternalPriceBreak, PartPricing, PartSellPriceBreak

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
