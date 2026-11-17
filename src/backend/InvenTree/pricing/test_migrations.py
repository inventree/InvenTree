"""Unit tests for the 'pricing' app database migrations."""

from decimal import Decimal

from django_test_migrations.contrib.unittest_case import MigratorTestCase

from InvenTree import unit_test

# Models which have been moved from the 'part' app to the 'pricing' app
MODELS = ['partpricing', 'partsellpricebreak', 'partinternalpricebreak']


class TestMovePricingModels(MigratorTestCase):
    """Test that pricing data is retained when moving models from 'part' to 'pricing'."""

    migrate_from = ('part', '0154_remove_part_notes')
    migrate_to = ('pricing', unit_test.getNewestMigrationFile('pricing'))

    def prepare(self):
        """Create pricing data against the 'part' app models."""
        Part = self.old_state.apps.get_model('part', 'part')
        PartPricing = self.old_state.apps.get_model('part', 'partpricing')
        PartSellPriceBreak = self.old_state.apps.get_model('part', 'partsellpricebreak')
        PartInternalPriceBreak = self.old_state.apps.get_model(
            'part', 'partinternalpricebreak'
        )

        part = Part.objects.create(
            name='Priced part',
            description='A part with pricing',
            salable=True,
            level=0,
            lft=0,
            rght=0,
            tree_id=0,
        )

        PartPricing.objects.create(
            part=part,
            overall_min=10,
            overall_min_currency='USD',
            overall_max=20,
            overall_max_currency='USD',
        )

        for qty in [1, 10, 100]:
            PartSellPriceBreak.objects.create(
                part=part, quantity=qty, price=qty * 2, price_currency='USD'
            )
            PartInternalPriceBreak.objects.create(
                part=part, quantity=qty, price=qty, price_currency='USD'
            )

        # Replicate the content types (and permissions) present in a database
        # created before these models were moved to the 'pricing' app
        ContentType = self.old_state.apps.get_model('contenttypes', 'contenttype')
        Permission = self.old_state.apps.get_model('auth', 'permission')

        ContentType.objects.filter(app_label='pricing').delete()

        for model in MODELS:
            ct, _ = ContentType.objects.get_or_create(app_label='part', model=model)
            Permission.objects.get_or_create(
                content_type=ct, codename=f'view_{model}', defaults={'name': model}
            )

    def test_pricing_data(self):
        """Pricing data should be available via the 'pricing' app models."""
        Part = self.new_state.apps.get_model('part', 'part')
        PartPricing = self.new_state.apps.get_model('pricing', 'partpricing')
        PartSellPriceBreak = self.new_state.apps.get_model(
            'pricing', 'partsellpricebreak'
        )
        PartInternalPriceBreak = self.new_state.apps.get_model(
            'pricing', 'partinternalpricebreak'
        )

        part = Part.objects.get(name='Priced part')

        pricing = PartPricing.objects.get(part=part)
        self.assertEqual(pricing.overall_min.amount, 10)
        self.assertEqual(pricing.overall_max.amount, 20)

        self.assertEqual(PartSellPriceBreak.objects.filter(part=part).count(), 3)
        self.assertEqual(PartInternalPriceBreak.objects.filter(part=part).count(), 3)

        self.assertEqual(
            PartSellPriceBreak.objects.get(part=part, quantity=10).price.amount, 20
        )

        # Reverse relations are retained
        self.assertEqual(part.salepricebreaks.count(), 3)
        self.assertEqual(part.internalpricebreaks.count(), 3)
        self.assertEqual(part.pricing_data.pk, pricing.pk)

    def test_content_types(self):
        """Content types (and linked permissions) should move to the 'pricing' app."""
        ContentType = self.new_state.apps.get_model('contenttypes', 'contenttype')
        Permission = self.new_state.apps.get_model('auth', 'permission')

        for model in MODELS:
            self.assertFalse(
                ContentType.objects.filter(app_label='part', model=model).exists()
            )

            ct = ContentType.objects.get(app_label='pricing', model=model)

            self.assertTrue(
                Permission.objects.filter(
                    content_type=ct, codename=f'view_{model}'
                ).exists()
            )


class TestMigrateQueuedTasks(MigratorTestCase):
    """Test that queued tasks referencing the legacy model identities are migrated."""

    migrate_from = ('pricing', '0001_initial')
    migrate_to = ('pricing', '0002_migrate_queued_tasks')

    def prepare(self):
        """Queue tasks with legacy (pre-migration) pickled model instances."""
        from django.db.models.base import model_unpickle
        from django.utils import timezone

        from django_q.conf import Conf
        from django_q.signing import SignedPackage

        from pricing.models import PartPricing, PartSellPriceBreak

        OrmQ = self.old_state.apps.get_model('django_q', 'OrmQ')

        def legacy(instance, model_name):
            """Return an object which pickles exactly as a pre-migration model instance."""
            state = instance.__reduce__()[2]

            class Legacy:
                def __reduce__(self):
                    return (model_unpickle, (('part', model_name),), state)

            return Legacy()

        # Map of task name to OrmQ primary key
        self.task_ids = {}

        def enqueue(name, payload):
            task = OrmQ.objects.create(
                key=Conf.PREFIX, payload=payload, lock=timezone.now()
            )
            self.task_ids[name] = task.pk

        # A queued pricing update, with a legacy PartPricing instance as an argument
        enqueue(
            'legacy-pricing',
            SignedPackage.dumps({
                'id': 'legacy-pricing',
                'name': 'legacy-pricing',
                'func': 'part.tasks.update_part_pricing',
                'args': (legacy(PartPricing(pk=123, part_id=4), 'PartPricing'),),
                'kwargs': {'counter': 2},
                'group': 'pricing',
            }),
        )

        # Before migration, the legacy payload cannot be loaded
        with self.assertRaises(LookupError):
            SignedPackage.loads(
                OrmQ.objects.get(pk=self.task_ids['legacy-pricing']).payload
            )

        # A legacy price break nested within the task kwargs
        enqueue(
            'legacy-pricebreak',
            SignedPackage.dumps({
                'id': 'legacy-pricebreak',
                'name': 'legacy-pricebreak',
                'func': 'some.task',
                'args': (),
                'kwargs': {
                    'items': [
                        legacy(
                            PartSellPriceBreak(pk=7, part_id=4), 'PartSellPriceBreak'
                        )
                    ]
                },
            }),
        )

        # An unrelated task, which should not be modified
        self.unrelated = SignedPackage.dumps({
            'id': 'unrelated',
            'name': 'unrelated',
            'func': 'some.other.task',
            'args': (1, 'a'),
            'kwargs': {},
        })
        enqueue('unrelated', self.unrelated)

        # A payload which cannot be decoded at all, which should not be modified
        enqueue('invalid', 'not-a-valid-payload')

    def test_queued_tasks(self):
        """Legacy payloads are rewritten, and other payloads are left untouched."""
        from django_q.signing import SignedPackage

        from pricing.models import PartPricing, PartSellPriceBreak

        OrmQ = self.new_state.apps.get_model('django_q', 'OrmQ')
        tasks = {name: OrmQ.objects.get(pk=pk) for name, pk in self.task_ids.items()}

        self.assertEqual(len(tasks), 4)

        data = SignedPackage.loads(tasks['legacy-pricing'].payload)
        pricing = data['args'][0]
        self.assertIsInstance(pricing, PartPricing)
        self.assertEqual(pricing.pk, 123)
        self.assertEqual(pricing.part_id, 4)
        self.assertEqual(data['kwargs'], {'counter': 2})
        self.assertEqual(data['func'], 'part.tasks.update_part_pricing')

        data = SignedPackage.loads(tasks['legacy-pricebreak'].payload)
        price_break = data['kwargs']['items'][0]
        self.assertIsInstance(price_break, PartSellPriceBreak)
        self.assertEqual(price_break.pk, 7)

        self.assertEqual(tasks['unrelated'].payload, self.unrelated)
        self.assertEqual(tasks['invalid'].payload, 'not-a-valid-payload')


class TestLegacyPurchasePriceEntries(MigratorTestCase):
    """Test that stock item purchase prices are migrated into legacy cost entries."""

    migrate_from = ('pricing', '0003_stock_item_cost')
    migrate_to = ('pricing', '0004_legacy_purchase_price_entries')

    def prepare(self):
        """Create stock items with (and without) purchase price data."""
        apps = self.old_state.apps

        InvenTreeSetting = apps.get_model('common', 'InvenTreeSetting')
        ExchangeBackend = apps.get_model('exchange', 'ExchangeBackend')
        Rate = apps.get_model('exchange', 'Rate')
        Part = apps.get_model('part', 'part')
        StockItem = apps.get_model('stock', 'stockitem')
        StockItemCostEntry = apps.get_model('pricing', 'stockitemcostentry')
        StockItemCost = apps.get_model('pricing', 'stockitemcost')

        InvenTreeSetting.objects.update_or_create(
            key='INVENTREE_DEFAULT_CURRENCY', defaults={'value': 'AUD'}
        )

        # Rates are stored relative to the backend base currency (USD)
        backend = ExchangeBackend.objects.create(
            name='InvenTreeExchange', base_currency='USD'
        )
        Rate.objects.create(backend=backend, currency='AUD', value=Decimal('1.5'))
        Rate.objects.create(backend=backend, currency='EUR', value=Decimal('0.75'))

        part = Part.objects.create(
            name='Migration Test Part', level=0, tree_id=0, lft=0, rght=0
        )

        def make_item(price=None, currency='', **kwargs):
            item = StockItem.objects.create(
                part=part,
                quantity=10,
                purchase_price=price,
                purchase_price_currency=currency,
                **kwargs,
            )
            return item.pk

        self.items = {
            # Default currency - copied directly
            'default': make_item(Decimal('10.5'), 'AUD'),
            # USD (base) -> AUD
            'base': make_item(Decimal('10'), 'USD'),
            # EUR -> AUD (via the base currency)
            'cross': make_item(Decimal('3'), 'EUR'),
            # No exchange rate available
            'no_rate': make_item(Decimal('1000'), 'JPY'),
            # Zero price is retained
            'zero': make_item(Decimal('0'), 'AUD'),
            # No price
            'none': make_item(None),
            # Existing cost entry (a range), and a stale summary
            'existing': make_item(Decimal('5'), 'AUD'),
            # Existing legacy entry (e.g. migration re-applied) - not duplicated
            'legacy': make_item(Decimal('7'), 'AUD'),
        }

        StockItemCostEntry.objects.create(
            stock_item_id=self.items['existing'],
            cost_type=20,
            source='manual',
            currency='AUD',
            min_cost=2,
            max_cost=3,
            converted_currency='AUD',
            converted_min_cost=2,
            converted_max_cost=3,
        )

        StockItemCost.objects.create(
            stock_item_id=self.items['existing'],
            currency='AUD',
            min_cost=99,
            max_cost=99,
        )

        StockItemCostEntry.objects.create(
            stock_item_id=self.items['legacy'],
            cost_type=10,
            source='legacy',
            currency='AUD',
            min_cost=7,
            max_cost=7,
            converted_currency='AUD',
            converted_min_cost=7,
            converted_max_cost=7,
        )

        StockItemCost.objects.create(
            stock_item_id=self.items['legacy'], currency='AUD', min_cost=7, max_cost=7
        )

    def test_legacy_entries(self):
        """Legacy entries are created, and the cost summaries are calculated."""
        apps = self.new_state.apps

        StockItemCostEntry = apps.get_model('pricing', 'stockitemcostentry')
        StockItemCost = apps.get_model('pricing', 'stockitemcost')

        def legacy_entry(key):
            return StockItemCostEntry.objects.get(
                stock_item_id=self.items[key], source='legacy'
            )

        def summary(key):
            return StockItemCost.objects.filter(stock_item_id=self.items[key]).first()

        # (key, original currency, original value, converted value)
        expected = [
            ('default', 'AUD', Decimal('10.5'), Decimal('10.5')),
            ('base', 'USD', Decimal('10'), Decimal('15')),
            ('cross', 'EUR', Decimal('3'), Decimal('6')),
            ('zero', 'AUD', Decimal('0'), Decimal('0')),
        ]

        for key, currency, value, converted in expected:
            entry = legacy_entry(key)

            self.assertEqual(entry.cost_type, 10)
            self.assertEqual(entry.currency, currency)
            self.assertEqual(entry.min_cost, value)
            self.assertEqual(entry.max_cost, value)
            self.assertEqual(entry.converted_currency, 'AUD')
            self.assertEqual(entry.converted_min_cost, converted)
            self.assertEqual(entry.converted_max_cost, converted)

            cost = summary(key)

            self.assertEqual(cost.currency, 'AUD')
            self.assertEqual(cost.min_cost, converted)
            self.assertEqual(cost.max_cost, converted)
            self.assertFalse(cost.incomplete)
            self.assertIsNotNone(cost.date)

        # No exchange rate - the entry is retained, but excluded from the summary
        entry = legacy_entry('no_rate')
        self.assertEqual(entry.currency, 'JPY')
        self.assertEqual(entry.min_cost, Decimal('1000'))
        self.assertEqual(entry.converted_currency, '')
        self.assertIsNone(entry.converted_min_cost)
        self.assertIsNone(entry.converted_max_cost)

        cost = summary('no_rate')
        self.assertIsNone(cost.min_cost)
        self.assertIsNone(cost.max_cost)
        self.assertTrue(cost.incomplete)

        # No purchase price - no entry or summary
        self.assertFalse(
            StockItemCostEntry.objects.filter(stock_item_id=self.items['none']).exists()
        )
        self.assertIsNone(summary('none'))

        # Existing entries are retained, and the (stale) summary is recalculated
        self.assertEqual(
            StockItemCostEntry.objects.filter(
                stock_item_id=self.items['existing']
            ).count(),
            2,
        )

        cost = summary('existing')
        self.assertEqual(cost.min_cost, Decimal('7'))
        self.assertEqual(cost.max_cost, Decimal('8'))
        self.assertFalse(cost.incomplete)
        self.assertEqual(
            StockItemCost.objects.filter(stock_item_id=self.items['existing']).count(),
            1,
        )

        # Existing legacy entries are not duplicated (and the stock item is not modified)
        cost = summary('legacy')
        self.assertEqual(cost.min_cost, Decimal('7'))
        self.assertEqual(cost.max_cost, Decimal('7'))

        self.assertEqual(
            StockItemCostEntry.objects.filter(
                stock_item_id=self.items['legacy']
            ).count(),
            1,
        )

        self.assertEqual(StockItemCostEntry.objects.filter(source='legacy').count(), 7)
        self.assertEqual(StockItemCost.objects.count(), 7)


class TestRemoveLegacyPurchasePriceEntries(MigratorTestCase):
    """Test that reversing the legacy purchase price migration removes the legacy entries."""

    migrate_from = ('pricing', '0004_legacy_purchase_price_entries')
    migrate_to = ('pricing', '0003_stock_item_cost')

    def prepare(self):
        """Create stock items with legacy (and other) cost entries."""
        apps = self.old_state.apps

        Part = apps.get_model('part', 'part')
        StockItem = apps.get_model('stock', 'stockitem')
        StockItemCostEntry = apps.get_model('pricing', 'stockitemcostentry')
        StockItemCost = apps.get_model('pricing', 'stockitemcost')

        part = Part.objects.create(
            name='Migration Test Part', level=0, tree_id=0, lft=0, rght=0
        )

        self.items = []

        for _ in range(2):
            item = StockItem.objects.create(
                part=part,
                quantity=10,
                purchase_price=Decimal('5'),
                purchase_price_currency='USD',
            )
            self.items.append(item.pk)

            StockItemCostEntry.objects.create(
                stock_item=item,
                cost_type=10,
                source='legacy',
                currency='USD',
                min_cost=5,
                max_cost=5,
                converted_currency='USD',
                converted_min_cost=5,
                converted_max_cost=5,
            )

        # The second item also has a manual entry
        StockItemCostEntry.objects.create(
            stock_item_id=self.items[1],
            cost_type=20,
            source='manual',
            currency='USD',
            min_cost=1,
            max_cost=2,
            converted_currency='USD',
            converted_min_cost=1,
            converted_max_cost=2,
        )

        for pk, total in zip(self.items, [5, 6], strict=True):
            StockItemCost.objects.create(
                stock_item_id=pk, currency='USD', min_cost=total, max_cost=total
            )

    def test_reverse(self):
        """Legacy entries are removed, and the summaries are recalculated."""
        apps = self.new_state.apps

        StockItemCostEntry = apps.get_model('pricing', 'stockitemcostentry')
        StockItemCost = apps.get_model('pricing', 'stockitemcost')

        self.assertFalse(StockItemCostEntry.objects.filter(source='legacy').exists())
        self.assertEqual(StockItemCostEntry.objects.count(), 1)

        # No entries left - the summary is removed
        self.assertFalse(
            StockItemCost.objects.filter(stock_item_id=self.items[0]).exists()
        )

        cost = StockItemCost.objects.get(stock_item_id=self.items[1])
        self.assertEqual(cost.currency, 'USD')
        self.assertEqual(cost.min_cost, Decimal('1'))
        self.assertEqual(cost.max_cost, Decimal('2'))
