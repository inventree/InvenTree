"""Copy existing StockItem.purchase_price values into StockItemCostEntry records.

Each stock item with a purchase price (including a zero price) receives one
PURCHASE cost entry with source='legacy', and its StockItemCost summary is (re)calculated.

Note: This migration uses historical models only, so exchange rates and the
default currency are read directly from the database (rather than via the
djmoney / InvenTree helper functions, which use the live models).
"""

from decimal import Decimal

from django.conf import settings
from django.db import migrations
from django.db.models import Count, Q, Sum
from django.utils.module_loading import import_string

BATCH_SIZE = 500

# Values duplicated from the live code, so that this migration does not change if they do
COST_TYPE_PURCHASE = 10
SOURCE_LEGACY = 'legacy'
COST_DECIMAL_PLACES = 6
FALLBACK_CURRENCY = 'USD'


def get_default_currency(apps) -> str:
    """Return the default currency code, as stored in the database."""
    InvenTreeSetting = apps.get_model('common', 'InvenTreeSetting')

    setting = InvenTreeSetting.objects.filter(
        key__iexact='INVENTREE_DEFAULT_CURRENCY'
    ).first()

    code = (setting.value if setting else '') or FALLBACK_CURRENCY

    return code.strip().upper()


class RateLookup:
    """Exchange rate lookup against the stored (historical) djmoney exchange rates.

    Mirrors djmoney.contrib.exchange.models.get_rate - rates are stored relative to the
    base currency of the exchange backend.
    """

    def __init__(self, apps):
        """Load the stored exchange rates for the default exchange backend."""
        ExchangeBackend = apps.get_model('exchange', 'ExchangeBackend')
        Rate = apps.get_model('exchange', 'Rate')

        backend_name = import_string(settings.EXCHANGE_BACKEND).name
        backend = ExchangeBackend.objects.filter(name=backend_name).first()

        self.base_currency = backend.base_currency if backend else None
        self.rates = {
            rate.currency: rate.value for rate in Rate.objects.filter(backend=backend)
        }

        # The base currency is not necessarily stored as a rate
        if self.base_currency:
            self.rates.setdefault(self.base_currency, Decimal(1))

    def convert(self, value, currency: str, target: str):
        """Convert a value between currencies, or return None if no rate is available."""
        if currency == target:
            return value

        source_rate = self.rates.get(currency)
        target_rate = self.rates.get(target)

        if not source_rate or not target_rate:
            return None

        return round(value * target_rate / source_rate, COST_DECIMAL_PLACES)


def update_summaries(apps, stock_item_ids, currency: str):
    """(Re)calculate the StockItemCost summary for each provided stock item.

    Mirrors StockItemCostManager.update_for_stock_items (which cannot be used here,
    as it is not available on the historical model manager).
    """
    StockItemCostEntry = apps.get_model('pricing', 'StockItemCostEntry')
    StockItemCost = apps.get_model('pricing', 'StockItemCost')

    valid = Q(
        converted_currency=currency,
        converted_min_cost__isnull=False,
        converted_max_cost__isnull=False,
    )

    stock_item_ids = sorted(set(stock_item_ids))

    for idx in range(0, len(stock_item_ids), BATCH_SIZE):
        batch = stock_item_ids[idx : idx + BATCH_SIZE]

        totals = (
            StockItemCostEntry.objects
            .filter(stock_item_id__in=batch)
            .order_by()
            .values('stock_item_id')
            .annotate(
                min_total=Sum('converted_min_cost', filter=valid),
                max_total=Sum('converted_max_cost', filter=valid),
                entry_count=Count('pk'),
                valid_count=Count('pk', filter=valid),
            )
        )

        summaries = [
            StockItemCost(
                stock_item_id=row['stock_item_id'],
                currency=currency,
                min_cost=row['min_total'] if row['valid_count'] else None,
                max_cost=row['max_total'] if row['valid_count'] else None,
                incomplete=row['valid_count'] < row['entry_count'],
            )
            for row in totals
        ]

        # Replace any existing summaries (stock items without entries have no summary)
        StockItemCost.objects.filter(stock_item_id__in=batch).delete()
        StockItemCost.objects.bulk_create(summaries, batch_size=BATCH_SIZE)


def create_legacy_entries(apps, schema_editor):
    """Create a legacy PURCHASE cost entry for each stock item with a purchase price."""
    StockItem = apps.get_model('stock', 'StockItem')
    StockItemCostEntry = apps.get_model('pricing', 'StockItemCostEntry')

    currency = get_default_currency(apps)
    rates = RateLookup(apps)

    # Stock items which already have a legacy entry are skipped (e.g. if re-applied)
    existing = StockItemCostEntry.objects.filter(source=SOURCE_LEGACY).values(
        'stock_item_id'
    )

    items = (
        StockItem.objects
        .filter(purchase_price__isnull=False)
        .exclude(pk__in=existing)
        .order_by('pk')
        .values_list('pk', 'purchase_price', 'purchase_price_currency')
    )

    stock_item_ids = []
    entries = []
    unconverted = 0

    def flush():
        StockItemCostEntry.objects.bulk_create(entries, batch_size=BATCH_SIZE)
        entries.clear()

    for pk, price, price_currency in items.iterator(chunk_size=BATCH_SIZE):
        price_currency = (price_currency or currency).strip().upper()
        price = round(price, COST_DECIMAL_PLACES)
        converted = rates.convert(price, price_currency, currency)

        if converted is None:
            unconverted += 1

        entries.append(
            StockItemCostEntry(
                stock_item_id=pk,
                cost_type=COST_TYPE_PURCHASE,
                source=SOURCE_LEGACY,
                currency=price_currency,
                min_cost=price,
                max_cost=price,
                converted_currency=currency if converted is not None else '',
                converted_min_cost=converted,
                converted_max_cost=converted,
                notes='Migrated from stock item purchase price',
            )
        )

        stock_item_ids.append(pk)

        if len(entries) >= BATCH_SIZE:
            flush()

    flush()

    update_summaries(apps, stock_item_ids, currency)

    if stock_item_ids:
        print(
            f'\npricing.0004: Created {len(stock_item_ids)} legacy purchase cost entries'
        )

    if unconverted:
        # These are excluded from the summary (marked 'incomplete') until converted,
        # e.g. via StockItemCostEntry.objects.reconvert_costs()
        print(
            f'pricing.0004: {unconverted} entries could not be converted to {currency} (no exchange rate available)'
        )


def remove_legacy_entries(apps, schema_editor):
    """Remove the legacy cost entries, and recalculate the affected summaries."""
    StockItemCostEntry = apps.get_model('pricing', 'StockItemCostEntry')

    legacy = StockItemCostEntry.objects.filter(source=SOURCE_LEGACY)

    stock_item_ids = list(
        legacy.order_by().values_list('stock_item_id', flat=True).distinct()
    )

    legacy.delete()

    update_summaries(apps, stock_item_ids, get_default_currency(apps))


class Migration(migrations.Migration):
    """Create legacy cost entries from existing stock item purchase prices."""

    dependencies = [
        ('common', '0053_inventreesetting_touched_inventreesetting_updated_and_more'),
        ('exchange', '0001_initial'),
        ('pricing', '0003_stock_item_cost'),
        ('stock', '0131_stocklocation_exclude_from_stock'),
    ]

    operations = [
        migrations.RunPython(
            create_legacy_entries, reverse_code=remove_legacy_entries
        )
    ]
