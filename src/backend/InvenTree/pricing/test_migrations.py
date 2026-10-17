"""Unit tests for the 'pricing' app database migrations."""

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
