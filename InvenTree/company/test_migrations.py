"""
Tests for the company model database migrations
"""

from django_test_migrations.contrib.unittest_case import MigratorTestCase

from InvenTree import helpers


class TestForwardMigrations(MigratorTestCase):

    migrate_from = ('company', helpers.getOldestMigrationFile('company'))
    migrate_to = ('company', helpers.getNewestMigrationFile('company'))

    def prepare(self):
        """
        Create some simple Company data, and ensure that it migrates OK
        """

        Company = self.old_state.apps.get_model('company', 'company')

        Company.objects.create(
            name='MSPC',
            description='Michael Scotts Paper Company',
            is_supplier=True
        )

    def test_migrations(self):

        Company = self.new_state.apps.get_model('company', 'company')

        self.assertEqual(Company.objects.count(), 1)


class TestManufacturerField(MigratorTestCase):
    """
    Tests for migration 0019 which migrates from old 'manufacturer_name' field to new 'manufacturer' field
    """

    migrate_from = ('company', '0018_supplierpart_manufacturer')
    migrate_to = ('company', '0019_auto_20200413_0642')

    def prepare(self):
        """
        Prepare the database by adding some test data 'before' the change:

        - Part object
        - Company object (supplier)
        - SupplierPart object
        """
        
        Part = self.old_state.apps.get_model('part', 'part')
        Company = self.old_state.apps.get_model('company', 'company')
        SupplierPart = self.old_state.apps.get_model('company', 'supplierpart')

        # Create an initial part
        part = Part.objects.create(
            name='Screw',
            description='A single screw'
        )

        # Create a company to act as the supplier
        supplier = Company.objects.create(
            name='Supplier',
            description='A supplier of parts',
            is_supplier=True,
            is_customer=False,
        )

        # Add some SupplierPart objects
        SupplierPart.objects.create(
            part=part,
            supplier=supplier,
            SKU='SCREW.001',
            manufacturer_name='ACME',
        )

        SupplierPart.objects.create(
            part=part,
            supplier=supplier,
            SKU='SCREW.002',
            manufacturer_name='Zero Corp'
        )

        self.assertEqual(Company.objects.count(), 1)

    def test_company_objects(self):
        """
        Test that the new companies have been created successfully
        """

        # Two additional company objects should have been created
        Company = self.new_state.apps.get_model('company', 'company')
        self.assertEqual(Company.objects.count(), 3)

        # The new company/ies must be marked as "manufacturers"
        acme = Company.objects.get(name='ACME')
        self.assertTrue(acme.is_manufacturer)

        SupplierPart = self.new_state.apps.get_model('company', 'supplierpart')
        parts = SupplierPart.objects.filter(manufacturer=acme)
        self.assertEqual(parts.count(), 1)
        part = parts.first()

        # Checks on the SupplierPart object
        self.assertEqual(part.manufacturer_name, 'ACME')
        self.assertEqual(part.manufacturer.name, 'ACME')


class TestCurrencyMigration(MigratorTestCase):
    """
    Tests for upgrade from basic currency support to django-money
    """

    migrate_from = ('company', '0025_auto_20201110_1001')
    migrate_to = ('company', '0026_auto_20201110_1011')

    def prepare(self):
        """
        Prepare some data:

        - A part to buy
        - A supplier to buy from
        - A supplier part
        - Multiple currency objects
        - Multiple supplier price breaks
        """

        Part = self.old_state.apps.get_model('part', 'part')

        part = Part.objects.create(
            name="PART", description="A purchaseable part",
            purchaseable=True,
            level=0,
            tree_id=0,
            lft=0,
            rght=0
        )

        Company = self.old_state.apps.get_model('company', 'company')

        supplier = Company.objects.create(name='Supplier', description='A supplier', is_supplier=True)

        SupplierPart = self.old_state.apps.get_model('company', 'supplierpart')

        sp = SupplierPart.objects.create(part=part, supplier=supplier, SKU='12345')

        Currency = self.old_state.apps.get_model('common', 'currency')

        aud = Currency.objects.create(symbol='$', suffix='AUD', description='Australian Dollars', value=1.0)
        usd = Currency.objects.create(symbol='$', suffix='USD', description='US Dollars', value=1.0)

        PB = self.old_state.apps.get_model('company', 'supplierpricebreak')

        PB.objects.create(part=sp, quantity=10, cost=5, currency=aud)
        PB.objects.create(part=sp, quantity=20, cost=3, currency=aud)
        PB.objects.create(part=sp, quantity=30, cost=2, currency=aud)

        PB.objects.create(part=sp, quantity=40, cost=2, currency=usd)
        PB.objects.create(part=sp, quantity=50, cost=2, currency=usd)

        for pb in PB.objects.all():
            self.assertIsNone(pb.price)

    def test_currency_migration(self):
        
        PB = self.new_state.apps.get_model('company', 'supplierpricebreak')

        for pb in PB.objects.all():
            # Test that a price has been assigned
            self.assertIsNotNone(pb.price)
