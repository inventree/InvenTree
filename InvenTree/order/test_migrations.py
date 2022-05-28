"""Unit tests for the 'order' model data migrations"""

from django_test_migrations.contrib.unittest_case import MigratorTestCase

from InvenTree.status_codes import SalesOrderStatus


class TestRefIntMigrations(MigratorTestCase):
    """Test entire schema migration"""

    migrate_from = ('order', '0040_salesorder_target_date')
    migrate_to = ('order', '0061_merge_0054_auto_20211201_2139_0060_auto_20211129_1339')

    def prepare(self):
        """Create initial data set"""
        # Create a purchase order from a supplier
        Company = self.old_state.apps.get_model('company', 'company')

        supplier = Company.objects.create(
            name='Supplier A',
            description='A great supplier!',
            is_supplier=True,
            is_customer=True,
        )

        PurchaseOrder = self.old_state.apps.get_model('order', 'purchaseorder')
        SalesOrder = self.old_state.apps.get_model('order', 'salesorder')

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

            sales_order = SalesOrder.objects.create(
                customer=supplier,
                reference=f"{ii}-xyz",
                description="A test sales order",
            )

            # Initially, the 'reference_int' field is unavailable
            with self.assertRaises(AttributeError):
                print(sales_order.reference_int)

    def test_ref_field(self):
        """Test that the 'reference_int' field has been created and is filled out correctly"""
        PurchaseOrder = self.new_state.apps.get_model('order', 'purchaseorder')
        SalesOrder = self.new_state.apps.get_model('order', 'salesorder')

        for ii in range(10):

            po = PurchaseOrder.objects.get(reference=f"{ii}-abcde")
            so = SalesOrder.objects.get(reference=f"{ii}-xyz")

            # The integer reference field must have been correctly updated
            self.assertEqual(po.reference_int, ii)
            self.assertEqual(so.reference_int, ii)


class TestShipmentMigration(MigratorTestCase):
    """Test data migration for the "SalesOrderShipment" model"""

    migrate_from = ('order', '0051_auto_20211014_0623')
    migrate_to = ('order', '0055_auto_20211025_0645')

    def prepare(self):
        """Create an initial SalesOrder"""
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

        # The "shipment" model does not exist yet
        with self.assertRaises(LookupError):
            self.old_state.apps.get_model('order', 'salesordershipment')

    def test_shipment_creation(self):
        """Check that a SalesOrderShipment has been created"""
        SalesOrder = self.new_state.apps.get_model('order', 'salesorder')
        Shipment = self.new_state.apps.get_model('order', 'salesordershipment')

        # Check that the correct number of Shipments have been created
        self.assertEqual(SalesOrder.objects.count(), 5)
        self.assertEqual(Shipment.objects.count(), 5)


class TestAdditionalLineMigration(MigratorTestCase):
    """Test entire schema migration"""

    migrate_from = ('order', '0063_alter_purchaseorderlineitem_unique_together')
    migrate_to = ('order', '0064_purchaseorderextraline_salesorderextraline')

    def prepare(self):
        """Create initial data set"""
        # Create a purchase order from a supplier
        Company = self.old_state.apps.get_model('company', 'company')
        PurchaseOrder = self.old_state.apps.get_model('order', 'purchaseorder')
        Part = self.old_state.apps.get_model('part', 'part')
        Supplierpart = self.old_state.apps.get_model('company', 'supplierpart')
        # TODO @matmair fix this test!!!
        # SalesOrder = self.old_state.apps.get_model('order', 'salesorder')

        supplier = Company.objects.create(
            name='Supplier A',
            description='A great supplier!',
            is_supplier=True,
            is_customer=True,
        )

        part = Part.objects.create(
            name='Bob',
            description='Can we build it?',
            assembly=True,
            salable=True,
            purchaseable=False,
            tree_id=0,
            level=0,
            lft=0,
            rght=0,
        )
        supplierpart = Supplierpart.objects.create(
            part=part,
            supplier=supplier
        )

        # Create some orders
        for ii in range(10):

            order = PurchaseOrder.objects.create(
                supplier=supplier,
                reference=f"{ii}-abcde",
                description="Just a test order"
            )
            order.lines.create(
                part=supplierpart,
                quantity=12,
                received=1
            )
            order.lines.create(
                quantity=12,
                received=1
            )

            # TODO @matmair fix this test!!!
            # sales_order = SalesOrder.objects.create(
            #     customer=supplier,
            #     reference=f"{ii}-xyz",
            #     description="A test sales order",
            # )
            # sales_order.lines.create(
            #     part=part,
            #     quantity=12,
            #     received=1
            # )

    def test_po_migration(self):
        """Test that the the PO lines where converted correctly"""
        PurchaseOrder = self.new_state.apps.get_model('order', 'purchaseorder')
        for ii in range(10):

            po = PurchaseOrder.objects.get(reference=f"{ii}-abcde")
            self.assertEqual(po.extra_lines.count(), 1)
            self.assertEqual(po.lines.count(), 1)

        # TODO @matmair fix this test!!!
        # SalesOrder = self.new_state.apps.get_model('order', 'salesorder')
        # for ii in range(10):
            # so = SalesOrder.objects.get(reference=f"{ii}-xyz")
            # self.assertEqual(so.extra_lines, 1)
            # self.assertEqual(so.lines.count(), 1)
