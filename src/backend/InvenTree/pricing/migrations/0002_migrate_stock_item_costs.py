# Generated for the 'pricing' app on 2026-08-15

from django.db import migrations
from tqdm import tqdm

from pricing.status_codes import CostType

BATCH_SIZE = 500


def migrate_stock_item_costs(apps, schema_editor):
    """Populate StockItemCost entries from existing StockItem.purchase_price data.

    Fetches StockItem rows in batches (via iterator) and bulk-creates the
    corresponding StockItemCost rows in the same batches, so the whole table
    is never held in memory at once. Uses ignore_conflicts so the migration
    is safe to re-run against stock items that already have a PURCHASE cost
    entry (e.g. if the migration is faked forward then re-applied).
    """
    StockItem = apps.get_model('stock', 'StockItem')
    StockItemCost = apps.get_model('pricing', 'StockItemCost')

    items = StockItem.objects.filter(purchase_price__isnull=False)

    n = items.count()

    if n == 0:
        return

    buffer = []

    progress = tqdm(total=n, desc='pricing.0002: Migrating StockItem purchase price data')

    for item in items.iterator(chunk_size=BATCH_SIZE):
        buffer.append(
            StockItemCost(
                stock_item_id=item.pk,
                cost_type=CostType.PURCHASE.value,
                min_cost=item.purchase_price,
                min_cost_currency=item.purchase_price_currency,
                max_cost=item.purchase_price,
                max_cost_currency=item.purchase_price_currency,
            )
        )

        if len(buffer) >= BATCH_SIZE:
            StockItemCost.objects.bulk_create(
                buffer, batch_size=BATCH_SIZE, ignore_conflicts=True
            )
            progress.update(len(buffer))
            buffer = []

    if buffer:
        StockItemCost.objects.bulk_create(
            buffer, batch_size=BATCH_SIZE, ignore_conflicts=True
        )
        progress.update(len(buffer))

    progress.close()


def remove_migrated_stock_item_costs(apps, schema_editor):
    """Reverse the migration.

    Writes each PURCHASE StockItemCost entry's min_cost back onto the linked
    StockItem.purchase_price (batched fetch + batched update), then removes
    the StockItemCost entries.
    """
    StockItem = apps.get_model('stock', 'StockItem')
    StockItemCost = apps.get_model('pricing', 'StockItemCost')

    costs = StockItemCost.objects.filter(cost_type=CostType.PURCHASE.value)

    n = costs.count()

    if n == 0:
        return

    buffer = []

    progress = tqdm(total=n, desc='pricing.0002: Restoring StockItem purchase price data')

    for cost in costs.iterator(chunk_size=BATCH_SIZE):
        buffer.append(
            StockItem(
                pk=cost.stock_item_id,
                purchase_price=cost.min_cost,
                purchase_price_currency=cost.min_cost_currency,
            )
        )

        if len(buffer) >= BATCH_SIZE:
            StockItem.objects.bulk_update(
                buffer, ['purchase_price', 'purchase_price_currency'], batch_size=BATCH_SIZE
            )
            progress.update(len(buffer))
            buffer = []

    if buffer:
        StockItem.objects.bulk_update(
            buffer, ['purchase_price', 'purchase_price_currency'], batch_size=BATCH_SIZE
        )
        progress.update(len(buffer))

    progress.close()

    costs.delete()


class Migration(migrations.Migration):
    dependencies = [
        ('pricing', '0001_initial'),
        ('stock', '0126_serial_number_concurrency_guard'),
    ]

    operations = [
        migrations.RunPython(
            migrate_stock_item_costs, reverse_code=remove_migrated_stock_item_costs
        )
    ]
