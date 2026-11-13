"""Unit tests for the stock item cost models in the 'pricing' app."""

from decimal import Decimal

from django.core.cache import cache
from django.core.exceptions import ValidationError

from djmoney.contrib.exchange.models import Rate, get_default_backend_name
from djmoney.money import Money

from common.models import InvenTreeSetting
from InvenTree.unit_test import InvenTreeTestCase
from pricing.models import CostSource, StockItemCost, StockItemCostEntry
from pricing.status_codes import CostType
from stock.models import StockItem


class StockItemCostTestBase(InvenTreeTestCase):
    """Base class for stock item cost tests."""

    fixtures = ['category', 'part', 'location', 'stock']

    def setUp(self):
        """Set the default currency, and select stock items to work with."""
        super().setUp()

        InvenTreeSetting.set_setting('INVENTREE_DEFAULT_CURRENCY', 'USD', None)

        items = StockItem.objects.all().order_by('pk')
        self.item = items[0]
        self.other_item = items[1]

        self.clear_rate_cache()

    def clear_rate_cache(self):
        """Clear cached exchange rates (djmoney caches rates between lookups)."""
        currencies = ['AUD', 'CAD', 'GBP', 'USD']
        backend = get_default_backend_name()

        cache.delete_many([
            f'djmoney:get_rate:{source}:{target}:{backend}'
            for source in currencies
            for target in currencies
        ])

    def summary(self, item=None):
        """Return the (freshly loaded) cost summary for a stock item, or None."""
        item = item or self.item
        return StockItemCost.objects.filter(stock_item=item).first()


class StockItemCostEntryValidationTests(StockItemCostTestBase):
    """Tests for validation of StockItemCostEntry values."""

    def test_single_value(self):
        """A single value is treated as both the minimum and maximum."""
        entry = StockItemCostEntry.objects.create_cost(
            self.item,
            CostType.PURCHASE,
            CostSource.MANUAL,
            min_cost=Decimal('4.5'),
            currency='USD',
        )

        self.assertEqual(entry.min_cost, Decimal('4.5'))
        self.assertEqual(entry.max_cost, Decimal('4.5'))

        entry = StockItemCostEntry.objects.create_cost(
            self.item,
            CostType.LANDED,
            CostSource.MANUAL,
            max_cost=Decimal('2'),
            currency='USD',
        )

        self.assertEqual(entry.min_cost, Decimal('2'))
        self.assertEqual(entry.max_cost, Decimal('2'))

    def test_no_values(self):
        """At least one of min_cost / max_cost must be provided."""
        with self.assertRaises(ValidationError) as err:
            StockItemCostEntry.objects.create_cost(
                self.item, CostType.PURCHASE, CostSource.MANUAL
            )

        self.assertIn('min_cost', err.exception.message_dict)
        self.assertFalse(StockItemCostEntry.objects.exists())

    def test_min_greater_than_max(self):
        """The minimum cost may not exceed the maximum cost."""
        with self.assertRaises(ValidationError) as err:
            StockItemCostEntry.objects.create_cost(
                self.item, CostType.PURCHASE, CostSource.MANUAL, min_cost=5, max_cost=4
            )

        self.assertIn('max_cost', err.exception.message_dict)
        self.assertFalse(StockItemCostEntry.objects.exists())

    def test_negative_values(self):
        """Negative values are allowed (e.g. rebates)."""
        StockItemCostEntry.objects.create_cost(
            self.item, CostType.PURCHASE, CostSource.MANUAL, min_cost=10, max_cost=12
        )

        entry = StockItemCostEntry.objects.create_cost(
            self.item, CostType.ADJUSTMENT, CostSource.MANUAL, min_cost=-3
        )

        self.assertEqual(entry.min_cost, Decimal('-3'))
        self.assertEqual(entry.converted_min_cost, Decimal('-3'))

        summary = self.summary()
        self.assertEqual(summary.min_cost, Decimal('7'))
        self.assertEqual(summary.max_cost, Decimal('9'))

    def test_rounding(self):
        """Values are rounded to the stored precision, and floats are accepted."""
        entry = StockItemCostEntry.objects.create_cost(
            self.item,
            CostType.PURCHASE,
            CostSource.MANUAL,
            min_cost=1.1,
            max_cost='2.1234567',
        )

        entry.refresh_from_db()

        self.assertEqual(entry.min_cost, Decimal('1.1'))
        self.assertEqual(entry.max_cost, Decimal('2.123457'))

    def test_invalid_currency(self):
        """An invalid currency code is rejected."""
        with self.assertRaises(ValidationError) as err:
            StockItemCostEntry.objects.create_cost(
                self.item,
                CostType.PURCHASE,
                CostSource.MANUAL,
                min_cost=1,
                currency='XYZ',
            )

        self.assertIn('currency', err.exception.message_dict)

    def test_money_values(self):
        """Money values set the currency of the entry."""
        entry = StockItemCostEntry.objects.create_cost(
            self.item,
            CostType.PURCHASE,
            CostSource.MANUAL,
            min_cost=Money(3, 'USD'),
            max_cost=Money(4, 'USD'),
        )

        self.assertEqual(entry.currency, 'USD')
        self.assertEqual(entry.min_cost_money, Money(3, 'USD'))
        self.assertEqual(entry.max_cost_money, Money(4, 'USD'))

        # Mismatched currencies are rejected
        for kwargs in [
            {'min_cost': Money(3, 'USD'), 'max_cost': Money(4, 'AUD')},
            {'min_cost': Money(3, 'USD'), 'currency': 'AUD'},
        ]:
            with self.assertRaises(ValidationError):
                StockItemCostEntry.objects.create_cost(
                    self.item, CostType.PURCHASE, CostSource.MANUAL, **kwargs
                )

        self.assertEqual(StockItemCostEntry.objects.count(), 1)


class StockItemCostConversionTests(StockItemCostTestBase):
    """Tests for currency conversion of StockItemCostEntry values."""

    def test_default_currency(self):
        """Values in the default currency are copied across without conversion."""
        entry = StockItemCostEntry.objects.create_cost(
            self.item,
            CostType.PURCHASE,
            CostSource.MANUAL,
            min_cost=3,
            max_cost=4,
            currency='USD',
        )

        self.assertEqual(entry.converted_currency, 'USD')
        self.assertEqual(entry.converted_min_cost, Decimal('3'))
        self.assertEqual(entry.converted_max_cost, Decimal('4'))

    def test_conversion_is_stored(self):
        """Converted values are stored, and not affected by later exchange rate changes."""
        self.generate_exchange_rates()

        entry = StockItemCostEntry.objects.create_cost(
            self.item,
            CostType.PURCHASE,
            CostSource.MANUAL,
            min_cost=15,
            max_cost=30,
            currency='AUD',
        )

        entry.refresh_from_db()

        # Original values are retained
        self.assertEqual(entry.currency, 'AUD')
        self.assertEqual(entry.min_cost, Decimal('15'))
        self.assertEqual(entry.max_cost, Decimal('30'))

        # Converted values (1 USD = 1.5 AUD)
        self.assertEqual(entry.converted_currency, 'USD')
        self.assertEqual(entry.converted_min_cost, Decimal('10'))
        self.assertEqual(entry.converted_max_cost, Decimal('20'))

        summary = self.summary()
        self.assertEqual(summary.currency, 'USD')
        self.assertEqual(summary.min_cost, Decimal('10'))
        self.assertEqual(summary.max_cost, Decimal('20'))
        self.assertEqual(summary.min_cost_money, Money(10, 'USD'))
        self.assertFalse(summary.incomplete)

        # Change the exchange rate
        Rate.objects.filter(currency='AUD').update(value=3)
        self.clear_rate_cache()

        # Saving the entry without changing its costs does not re-convert
        entry = StockItemCostEntry.objects.get(pk=entry.pk)
        entry.notes = 'Updated notes'
        entry.save()

        entry.refresh_from_db()
        self.assertEqual(entry.converted_min_cost, Decimal('10'))

        summary = self.summary()
        self.assertEqual(summary.min_cost, Decimal('10'))
        self.assertEqual(summary.max_cost, Decimal('20'))

        # Changing the cost re-converts at the current rate
        entry.min_cost = Decimal('30')
        entry.save()

        entry.refresh_from_db()
        self.assertEqual(entry.converted_min_cost, Decimal('10'))
        self.assertEqual(entry.converted_max_cost, Decimal('10'))

        summary = self.summary()
        self.assertEqual(summary.min_cost, Decimal('10'))
        self.assertEqual(summary.max_cost, Decimal('10'))

    def test_missing_rate(self):
        """Entries which cannot be converted are excluded, and the summary is marked incomplete."""
        # No exchange rates are available
        entry = StockItemCostEntry.objects.create_cost(
            self.item, CostType.PURCHASE, CostSource.MANUAL, min_cost=15, currency='AUD'
        )

        self.assertEqual(entry.converted_currency, '')
        self.assertIsNone(entry.converted_min_cost)
        self.assertIsNone(entry.converted_max_cost)

        summary = self.summary()
        self.assertIsNotNone(summary)
        self.assertIsNone(summary.min_cost)
        self.assertIsNone(summary.max_cost)
        self.assertTrue(summary.incomplete)

        # Add an entry which *can* be included
        StockItemCostEntry.objects.create_cost(
            self.item,
            CostType.LANDED,
            CostSource.MANUAL,
            min_cost=2,
            max_cost=3,
            currency='USD',
        )

        summary = self.summary()
        self.assertEqual(summary.min_cost, Decimal('2'))
        self.assertEqual(summary.max_cost, Decimal('3'))
        self.assertTrue(summary.incomplete)

        # Once exchange rates are available, the entry can be re-converted
        self.generate_exchange_rates()

        self.assertEqual(StockItemCostEntry.objects.reconvert_costs(), 1)

        entry.refresh_from_db()
        self.assertEqual(entry.converted_currency, 'USD')
        self.assertEqual(entry.converted_min_cost, Decimal('10'))

        summary = self.summary()
        self.assertEqual(summary.min_cost, Decimal('12'))
        self.assertEqual(summary.max_cost, Decimal('13'))
        self.assertFalse(summary.incomplete)

        # Nothing left to convert
        self.assertEqual(StockItemCostEntry.objects.reconvert_costs(), 0)

    def test_default_currency_change(self):
        """Entries converted to a previous default currency are excluded until re-converted."""
        self.generate_exchange_rates()

        StockItemCostEntry.objects.create_cost(
            self.item,
            CostType.PURCHASE,
            CostSource.MANUAL,
            min_cost=10,
            max_cost=20,
            currency='USD',
        )

        InvenTreeSetting.set_setting('INVENTREE_DEFAULT_CURRENCY', 'AUD', None)

        # Recalculating the summary excludes the stale entry
        StockItemCost.objects.update_for_stock_items([self.item.pk])

        summary = self.summary()
        self.assertEqual(summary.currency, 'AUD')
        self.assertIsNone(summary.min_cost)
        self.assertTrue(summary.incomplete)

        self.assertEqual(StockItemCostEntry.objects.reconvert_costs(), 1)

        summary = self.summary()
        self.assertEqual(summary.currency, 'AUD')
        self.assertEqual(summary.min_cost, Decimal('15'))
        self.assertEqual(summary.max_cost, Decimal('30'))
        self.assertFalse(summary.incomplete)

    def test_reconvert_updates_stale_summary(self):
        """Re-conversion recalculates summaries, even where an entry still cannot be converted."""
        StockItemCostEntry.objects.create_cost(
            self.item, CostType.PURCHASE, CostSource.MANUAL, min_cost=10, currency='USD'
        )

        summary = self.summary()
        self.assertFalse(summary.incomplete)

        # Change the default currency - no exchange rates are available
        InvenTreeSetting.set_setting('INVENTREE_DEFAULT_CURRENCY', 'AUD', None)

        self.assertEqual(StockItemCostEntry.objects.reconvert_costs(), 0)

        summary = self.summary()
        self.assertEqual(summary.currency, 'AUD')
        self.assertIsNone(summary.min_cost)
        self.assertTrue(summary.incomplete)


class StockItemCostSummaryTests(StockItemCostTestBase):
    """Tests for the StockItemCost summary model."""

    def test_summary_totals(self):
        """The summary is the sum of all cost entries for the stock item."""
        self.assertIsNone(self.summary())

        StockItemCostEntry.objects.create_cost(
            self.item, CostType.PURCHASE, CostSource.MANUAL, min_cost=10, max_cost=12
        )
        StockItemCostEntry.objects.create_cost(
            self.item, CostType.LANDED, CostSource.MANUAL, min_cost=1, max_cost=2
        )
        StockItemCostEntry.objects.create_cost(
            self.item, CostType.LANDED, CostSource.MANUAL, min_cost='0.5'
        )

        summary = self.summary()
        self.assertEqual(summary.min_cost, Decimal('11.5'))
        self.assertEqual(summary.max_cost, Decimal('14.5'))
        self.assertFalse(summary.estimated)
        self.assertFalse(summary.incomplete)

        # Accessible via the stock item
        item = StockItem.objects.get(pk=self.item.pk)
        self.assertEqual(item.cost.min_cost, Decimal('11.5'))
        self.assertEqual(item.cost_entries.count(), 3)

        # Other stock items are not affected
        self.assertIsNone(self.summary(self.other_item))

    def test_estimated(self):
        """The summary is marked as estimated if any entry is estimated."""
        entry = StockItemCostEntry.objects.create_cost(
            self.item, CostType.PURCHASE, CostSource.MANUAL, min_cost=10
        )

        self.assertFalse(self.summary().estimated)

        estimate = StockItemCostEntry.objects.create_cost(
            self.item,
            CostType.MATERIAL,
            CostSource.MANUAL,
            min_cost=5,
            max_cost=8,
            estimated=True,
        )

        self.assertTrue(self.summary().estimated)

        estimate.delete()
        self.assertFalse(self.summary().estimated)

        entry.estimated = True
        entry.save()
        self.assertTrue(self.summary().estimated)

    def test_update_and_delete(self):
        """The summary is updated when entries are edited or deleted."""
        entry = StockItemCostEntry.objects.create_cost(
            self.item, CostType.PURCHASE, CostSource.MANUAL, min_cost=10
        )
        other = StockItemCostEntry.objects.create_cost(
            self.item, CostType.LANDED, CostSource.MANUAL, min_cost=2
        )

        self.assertEqual(self.summary().min_cost, Decimal('12'))

        entry.min_cost = Decimal('20')
        entry.max_cost = Decimal('25')
        entry.save()

        summary = self.summary()
        self.assertEqual(summary.min_cost, Decimal('22'))
        self.assertEqual(summary.max_cost, Decimal('27'))

        other.delete()

        summary = self.summary()
        self.assertEqual(summary.min_cost, Decimal('20'))
        self.assertEqual(summary.max_cost, Decimal('25'))

        # Removing the last entry removes the summary
        entry.delete()
        self.assertIsNone(self.summary())

    def test_bulk_create(self):
        """Bulk-created entries update the summaries immediately."""
        created = StockItemCostEntry.objects.bulk_create_costs([
            {
                'stock_item': self.item,
                'cost_type': CostType.PURCHASE,
                'min_cost': Money(10, 'USD'),
                'source': 'purchase_order',
            },
            {
                'stock_item': self.item,
                'cost_type': CostType.LANDED,
                'min_cost': 1,
                'max_cost': 2,
                'estimated': True,
                'source': CostSource.MANUAL,
            },
            {
                'stock_item_id': self.other_item.pk,
                'cost_type': CostType.PURCHASE,
                'min_cost': 4,
                'source': CostSource.plugin('my-plugin'),
            },
        ])

        self.assertEqual(len(created), 3)

        summary = self.summary()
        self.assertEqual(summary.min_cost, Decimal('11'))
        self.assertEqual(summary.max_cost, Decimal('12'))
        self.assertTrue(summary.estimated)

        other = self.summary(self.other_item)
        self.assertEqual(other.min_cost, Decimal('4'))
        self.assertEqual(other.max_cost, Decimal('4'))
        self.assertFalse(other.estimated)

        entry = StockItemCostEntry.objects.get(source='purchase_order')
        self.assertEqual(entry.converted_min_cost, Decimal('10'))
        self.assertEqual(entry.max_cost, Decimal('10'))

        # Bulk creating more entries updates the existing summary
        StockItemCostEntry.objects.bulk_create_costs([
            {
                'stock_item': self.item,
                'cost_type': CostType.FEES,
                'min_cost': 3,
                'source': CostSource.MANUAL,
            }
        ])

        summary = self.summary()
        self.assertEqual(summary.min_cost, Decimal('14'))
        self.assertEqual(StockItemCost.objects.filter(stock_item=self.item).count(), 1)

        self.assertEqual(StockItemCostEntry.objects.bulk_create_costs([]), [])

    def test_bulk_create_invalid(self):
        """If any entry is invalid, no entries are created."""
        with self.assertRaises(ValidationError):
            StockItemCostEntry.objects.bulk_create_costs([
                {'stock_item': self.item, 'min_cost': 10, 'source': 'manual'},
                {
                    'stock_item': self.item,
                    'min_cost': 5,
                    'max_cost': 1,
                    'source': 'manual',
                },
            ])

        self.assertFalse(StockItemCostEntry.objects.exists())
        self.assertIsNone(self.summary())

    def test_delete_stock_item(self):
        """Deleting a stock item removes its cost entries and summary."""
        StockItemCostEntry.objects.create_cost(
            self.item, CostType.PURCHASE, CostSource.MANUAL, min_cost=10
        )
        StockItemCostEntry.objects.create_cost(
            self.other_item, CostType.PURCHASE, CostSource.MANUAL, min_cost=5
        )

        StockItem.objects.filter(pk=self.item.pk).delete()

        self.assertFalse(
            StockItemCostEntry.objects.filter(stock_item=self.item.pk).exists()
        )
        self.assertIsNone(StockItemCost.objects.filter(stock_item=self.item.pk).first())

        # Other stock items are unaffected
        self.assertEqual(self.summary(self.other_item).min_cost, Decimal('5'))


class StockItemCostSourceTests(StockItemCostTestBase):
    """Tests for the cost entry source naming convention."""

    def test_is_valid(self):
        """Core sources use a bare name, plugins use 'plugin:<slug>'."""
        for source in CostSource.CORE_SOURCES:
            self.assertTrue(CostSource.is_valid(source))

        self.assertEqual(CostSource.plugin('my-plugin'), 'plugin:my-plugin')

        for source in ['plugin:my-plugin', 'plugin:abc_123', 'plugin:x']:
            self.assertTrue(CostSource.is_valid(source), source)

        for source in [
            'unknown',
            'Manual',
            'plugin:',
            'plugin:My Plugin',
            'plugin:-slug',
            'plugin:slug\n',
            'core:purchase_order',
        ]:
            self.assertFalse(CostSource.is_valid(source), source)

    def test_validation(self):
        """Entries with an invalid source are rejected."""
        with self.assertRaises(ValidationError) as err:
            StockItemCostEntry.objects.create_cost(
                self.item, CostType.PURCHASE, 'my-plugin', min_cost=1
            )

        self.assertIn('source', err.exception.message_dict)

        with self.assertRaises(ValidationError):
            StockItemCostEntry.objects.bulk_create_costs([
                {'stock_item': self.item, 'min_cost': 1, 'source': 'bad source'}
            ])

        # A source must be provided when creating entries in bulk
        with self.assertRaises(ValidationError):
            StockItemCostEntry.objects.bulk_create_costs([
                {'stock_item': self.item, 'min_cost': 1}
            ])

        self.assertFalse(StockItemCostEntry.objects.exists())

        entry = StockItemCostEntry.objects.create_cost(
            self.item, CostType.PURCHASE, CostSource.plugin('my-plugin'), min_cost=1
        )

        self.assertEqual(entry.source, 'plugin:my-plugin')


class StockItemCostManagerTests(StockItemCostTestBase):
    """Tests for the programmatic helpers for editing and removing cost entries."""

    def test_update_cost(self):
        """Entries can be updated, and the summary is recalculated."""
        entry = StockItemCostEntry.objects.create_cost(
            self.item, CostType.PURCHASE, CostSource.MANUAL, min_cost=10, max_cost=12
        )

        StockItemCostEntry.objects.update_cost(
            entry, min_cost=Money(20, 'USD'), max_cost=Money(25, 'USD'), notes='x'
        )

        entry.refresh_from_db()
        self.assertEqual(entry.min_cost, Decimal('20'))
        self.assertEqual(entry.max_cost, Decimal('25'))
        self.assertEqual(entry.converted_min_cost, Decimal('20'))
        self.assertEqual(entry.notes, 'x')

        summary = self.summary()
        self.assertEqual(summary.min_cost, Decimal('20'))
        self.assertEqual(summary.max_cost, Decimal('25'))

        # A single (plain) bound keeps the existing currency
        StockItemCostEntry.objects.update_cost(entry, min_cost=22)
        self.assertEqual(self.summary().min_cost, Decimal('22'))

    def test_update_cost_currency(self):
        """Changing the currency of an entry via Money values."""
        entry = StockItemCostEntry.objects.create_cost(
            self.item, CostType.PURCHASE, CostSource.MANUAL, min_cost=10
        )

        # A single Money bound in another currency would leave the other bound in the old currency
        with self.assertRaises(ValidationError):
            StockItemCostEntry.objects.update_cost(entry, min_cost=Money(5, 'AUD'))

        # Conflicting currencies
        with self.assertRaises(ValidationError):
            StockItemCostEntry.objects.update_cost(
                entry, min_cost=Money(5, 'AUD'), max_cost=Money(6, 'CAD')
            )

        with self.assertRaises(ValidationError):
            StockItemCostEntry.objects.update_cost(
                entry, currency='CAD', min_cost=Money(5, 'AUD')
            )

        entry.refresh_from_db()
        self.assertEqual(entry.currency, 'USD')

        # Both bounds provided - the currency is changed
        StockItemCostEntry.objects.update_cost(
            entry, min_cost=Money(5, 'AUD'), max_cost=None
        )

        entry.refresh_from_db()
        self.assertEqual(entry.currency, 'AUD')
        self.assertEqual(entry.min_cost, Decimal('5'))
        self.assertEqual(entry.max_cost, Decimal('5'))

    def test_update_cost_stock_item(self):
        """Entries cannot be moved between stock items."""
        entry = StockItemCostEntry.objects.create_cost(
            self.item, CostType.PURCHASE, CostSource.MANUAL, min_cost=10
        )

        for key, value in [
            ('stock_item', self.other_item),
            ('stock_item_id', self.other_item.pk),
        ]:
            with self.assertRaises(ValueError):
                StockItemCostEntry.objects.update_cost(entry, **{key: value})

        entry.refresh_from_db()
        self.assertEqual(entry.stock_item, self.item)

    def test_update_cost_invalid(self):
        """Invalid changes are not saved."""
        entry = StockItemCostEntry.objects.create_cost(
            self.item, CostType.PURCHASE, CostSource.MANUAL, min_cost=10
        )

        with self.assertRaises(ValidationError):
            StockItemCostEntry.objects.update_cost(entry, min_cost=30, max_cost=20)

        entry.refresh_from_db()
        self.assertEqual(entry.min_cost, Decimal('10'))
        self.assertEqual(self.summary().min_cost, Decimal('10'))

    def test_delete_costs(self):
        """Deleting entries in bulk updates (or removes) the affected summaries."""
        a = StockItemCostEntry.objects.create_cost(
            self.item, CostType.PURCHASE, CostSource.MANUAL, min_cost=10
        )
        b = StockItemCostEntry.objects.create_cost(
            self.item, CostType.LANDED, CostSource.MANUAL, min_cost=2
        )
        c = StockItemCostEntry.objects.create_cost(
            self.other_item, CostType.PURCHASE, CostSource.MANUAL, min_cost=5
        )

        # Delete from a list of instances
        self.assertEqual(StockItemCostEntry.objects.delete_costs([a, c]), 2)

        self.assertEqual(self.summary().min_cost, Decimal('2'))
        self.assertIsNone(self.summary(self.other_item))

        # Delete from a queryset
        self.assertEqual(
            StockItemCostEntry.objects.delete_costs(
                StockItemCostEntry.objects.filter(pk=b.pk)
            ),
            1,
        )

        self.assertIsNone(self.summary())
        self.assertEqual(StockItemCostEntry.objects.delete_costs([]), 0)

    def test_replace_costs(self):
        """Replacing entries from a single source leaves other sources untouched."""
        source = CostSource.plugin('landed-cost')

        manual = StockItemCostEntry.objects.create_cost(
            self.item, CostType.PURCHASE, CostSource.MANUAL, min_cost=10
        )

        StockItemCostEntry.objects.replace_costs(
            self.item,
            source,
            [
                {'cost_type': CostType.LANDED, 'min_cost': 1},
                {'cost_type': CostType.FEES, 'min_cost': 2},
            ],
        )

        self.assertEqual(self.summary().min_cost, Decimal('13'))

        # Recalculation replaces (rather than adds to) the previous result
        created = StockItemCostEntry.objects.replace_costs(
            self.item, source, [{'cost_type': CostType.LANDED, 'min_cost': 3}]
        )

        self.assertEqual(len(created), 1)
        self.assertEqual(created[0].source, source)
        self.assertEqual(self.summary().min_cost, Decimal('13'))
        self.assertTrue(StockItemCostEntry.objects.filter(pk=manual.pk).exists())

        # Invalid entries leave the existing entries untouched
        with self.assertRaises(ValidationError):
            StockItemCostEntry.objects.replace_costs(
                self.item, source, [{'min_cost': 5, 'max_cost': 1}]
            )

        self.assertEqual(self.summary().min_cost, Decimal('13'))

        # An empty list removes the existing entries
        StockItemCostEntry.objects.replace_costs(self.item, source, [])
        self.assertEqual(self.summary().min_cost, Decimal('10'))
        self.assertEqual(StockItemCostEntry.objects.count(), 1)

    def test_replace_costs_by_type(self):
        """Replacing entries can be limited to a single cost type."""
        source = CostSource.plugin('landed-cost')

        StockItemCostEntry.objects.create_cost(
            self.item, CostType.LANDED, source, min_cost=1
        )
        StockItemCostEntry.objects.create_cost(
            self.item, CostType.FEES, source, min_cost=2
        )

        StockItemCostEntry.objects.replace_costs(
            self.item,
            source,
            [{'cost_type': CostType.FEES, 'min_cost': 5}],
            cost_type=CostType.FEES,
        )

        self.assertEqual(self.summary().min_cost, Decimal('6'))

        # New entries must match the replaced cost type
        with self.assertRaises(ValidationError):
            StockItemCostEntry.objects.replace_costs(
                self.item,
                source,
                [{'cost_type': CostType.LANDED, 'min_cost': 5}],
                cost_type=CostType.FEES,
            )

        self.assertEqual(self.summary().min_cost, Decimal('6'))


class StockItemCostAuditTests(StockItemCostTestBase):
    """Cost entry changes are recorded in the audit log, against the stock item."""

    def entries(self, **filters):
        """Return audit entries for the StockItemCostEntry model."""
        from django.contrib.contenttypes.models import ContentType

        from audit.models import AuditLogEntry

        return AuditLogEntry.objects.filter(
            content_type=ContentType.objects.get_for_model(StockItemCostEntry),
            **filters,
        )

    def test_audit(self):
        """Create, update and delete operations are recorded (including bulk operations)."""
        from audit.models import AuditLogEntry

        ACTION = AuditLogEntry.Action

        entry = StockItemCostEntry.objects.create_cost(
            self.item, CostType.PURCHASE, CostSource.MANUAL, min_cost=10
        )

        create = self.entries(action=ACTION.CREATE, object_pk=str(entry.pk)).get()
        self.assertEqual(create.parent_object_pk, str(self.item.pk))
        self.assertEqual(create.object_repr, 'Purchase cost (manual)')

        StockItemCostEntry.objects.update_cost(entry, min_cost=12, max_cost=12)

        update = self.entries(action=ACTION.UPDATE, object_pk=str(entry.pk)).get()
        self.assertIn('min_cost', update.changes_dict)
        self.assertNotIn('date', update.changes_dict)

        # Entries created in bulk are also recorded
        created = StockItemCostEntry.objects.bulk_create_costs([
            {'stock_item': self.item, 'min_cost': 1, 'source': 'manual'},
            {'stock_item': self.other_item, 'min_cost': 2, 'source': 'manual'},
        ])

        for obj in created:
            self.assertTrue(
                self.entries(action=ACTION.CREATE, object_pk=str(obj.pk)).exists()
            )

        StockItemCostEntry.objects.delete_costs(created)

        for obj in created:
            self.assertTrue(
                self.entries(action=ACTION.DELETE, object_pk=str(obj.pk)).exists()
            )

        # The cached summary is calculated (not edited), so is not audited
        from auditlog.registry import auditlog

        self.assertTrue(auditlog.contains(StockItemCostEntry))
        self.assertFalse(auditlog.contains(StockItemCost))


class StockItemCostRecorderTests(StockItemCostTestBase):
    """Tests for the StockItemCostRecorder helper."""

    def test_record(self):
        """Entries are created in bulk, along with the cost summaries."""
        from django.contrib.auth.models import User

        from pricing.helpers import StockItemCostRecorder

        user = User.objects.create(username='cost-user')
        items = list(StockItem.objects.order_by('pk')[:3])

        costs = StockItemCostRecorder(source=CostSource.PURCHASE_ORDER, user=user)

        # The same cost for many items
        self.assertTrue(
            costs.add(
                items[:2],
                CostType.PURCHASE,
                cost=Money(5, 'USD'),
                source_data={'line_item': 1},
            )
        )

        # A range, and an additional entry for the same item
        costs.add(items[2], CostType.PURCHASE, min_cost=1, max_cost=2)
        costs.add(items[2], CostType.LANDED, cost=Money(1, 'USD'), estimated=True)

        # No cost - nothing is recorded
        self.assertFalse(costs.add(items[0], CostType.FEES, cost=None))

        self.assertEqual(len(costs), 4)

        # Nothing is created until saved
        self.assertFalse(StockItemCostEntry.objects.exists())

        created = costs.save()

        self.assertEqual(len(created), 4)
        self.assertEqual(len(costs), 0)

        for entry in StockItemCostEntry.objects.all():
            self.assertEqual(entry.source, CostSource.PURCHASE_ORDER)
            self.assertEqual(entry.user, user)

        for item in items[:2]:
            entry = item.cost_entries.get()
            self.assertEqual(entry.min_cost, Decimal(5))
            self.assertEqual(entry.max_cost, Decimal(5))
            self.assertEqual(entry.source_data, {'line_item': 1})

            summary = self.summary(item)
            self.assertEqual(summary.min_cost, Decimal(5))
            self.assertEqual(summary.max_cost, Decimal(5))
            self.assertFalse(summary.estimated)

        summary = self.summary(items[2])
        self.assertEqual(summary.min_cost, Decimal(2))
        self.assertEqual(summary.max_cost, Decimal(3))
        self.assertTrue(summary.estimated)

        # Saving again creates nothing
        self.assertEqual(costs.save(), [])

    def test_invalid(self):
        """Invalid input is rejected, and no entries are created."""
        from pricing.helpers import StockItemCostRecorder

        costs = StockItemCostRecorder(source=CostSource.MANUAL)

        with self.assertRaises(ValueError):
            costs.add(self.item, CostType.PURCHASE, cost=1, min_cost=1)

        with self.assertRaises(ValueError):
            costs.add(StockItem(part=self.item.part), CostType.PURCHASE, cost=1)

        # One invalid entry prevents all entries from being created
        costs.add(self.item, CostType.PURCHASE, cost=1)
        costs.add(self.other_item, CostType.PURCHASE, min_cost=5, max_cost=1)

        with self.assertRaises(ValidationError):
            costs.save()

        self.assertFalse(StockItemCostEntry.objects.exists())
        self.assertIsNone(self.summary())

        # An invalid source is rejected
        costs = StockItemCostRecorder(source='not a source')
        costs.add(self.item, CostType.PURCHASE, cost=1)

        with self.assertRaises(ValidationError):
            costs.save()

        self.assertFalse(StockItemCostEntry.objects.exists())
