"""
Unit tests for the 'order' model data migrations
"""

from django_test_migrations.contrib.unittest_case import MigratorTestCase

from InvenTree import helpers
from InvenTree.status_codes import SalesOrderStatus


class TestForwardMigrations(MigratorTestCase):
    """
    Test entire schema migration
    """

    migrate_from = ('order', helpers.getOldestMigrationFile('order'))
    migrate_to = ('order', helpers.getNewestMigrationFile('order'))

    def prepare(self):
        """
        Create initial data set
        """

        # Create a purchase order from a supplier
        Company = self.old_state.apps.get_model('company', 'company')

        supplier = Company.objects.create(
            name='Supplier A',
            description='A great supplier!',
            is_supplier=True
        )

        PurchaseOrder = self.old_state.apps.get_model('order', 'purchaseorder')

        # Create some orders
        for ii in range(10):

            order = PurchaseOrder.objects.create(
                supplier=supplier,
                reference=f"{ii}-abcde",
                description="Just a test order"
            )

            # Initially, the 'reference_int' field is unavailable
            with self.assertRaises(AttributeError):
                print(order.reference_int)

    def test_ref_field(self):
        """
        Test that the 'reference_int' field has been created and is filled out correctly
        """

        PurchaseOrder = self.new_state.apps.get_model('order', 'purchaseorder')

        for ii in range(10):

            order = PurchaseOrder.objects.get(reference=f"{ii}-abcde")

            # The integer reference field must have been correctly updated
        self.assertEqual(order.reference_int, ii)


class TestShipmentMigration(MigratorTestCase):
    """
    Test data migration for the "SalesOrderShipment" model
    """

    migrate_from = ('order', '0051_auto_20211014_0623')
    migrate_to = ('order', '0055_auto_20211025_0645')

    def prepare(self):
        """
        Create an initial SalesOrder
        """

        Company = self.old_state.apps.get_model('company', 'company')

        customer = Company.objects.create(
            name='My customer',
            description='A customer we sell stuff too',
            is_customer=True
        )

        SalesOrder = self.old_state.apps.get_model('order', 'salesorder')

        for ii in range(5):
            order = SalesOrder.objects.create(
                reference=f'SO{ii}',
                customer=customer,
                description='A sales order for stuffs',
                status=SalesOrderStatus.PENDING,
            )

        order.save()

    def test_shipment_creation(self):
        """
        Check that a SalesOrderShipment has been created
        """

        SalesOrder = self.new_state.apps.get_model('order', 'salesorder')
        Shipment = self.new_state.apps.get_model('order', 'salesordershipment')

        # Check that the correct number of Shipments have been created
        self.assertEqual(SalesOrder.objects.count(), 5)
        self.assertEqual(Shipment.objects.count(), 5)
