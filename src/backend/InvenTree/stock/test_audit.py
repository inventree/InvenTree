"""Audit log tests for the StockItem model (stock tracking events)."""

from decimal import Decimal

from django.contrib.contenttypes.models import ContentType
from django.urls import reverse

from audit.models import AuditLogEntry
from InvenTree.unit_test import InvenTreeAPITestCase
from part.models import Part
from stock.models import StockItem, StockLocation
from stock.status_codes import StockHistoryCode, StockStatus

ACTION = AuditLogEntry.Action


class StockAuditTestBase(InvenTreeAPITestCase):
    """Base class for stock item audit tests."""

    roles = ['stock.view', 'stock.add', 'stock.change', 'stock.delete', 'part.view']

    @classmethod
    def setUpTestData(cls):
        """Create test data."""
        super().setUpTestData()

        cls.part = Part.objects.create(
            name='Audit Widget', description='A widget', component=True
        )
        cls.assembly = Part.objects.create(
            name='Audit Assembly', description='An assembly', assembly=True
        )
        cls.trackable = Part.objects.create(
            name='Audit Trackable', description='A trackable part', trackable=True
        )

        cls.loc_a = StockLocation.objects.create(name='Location A')
        cls.loc_b = StockLocation.objects.create(name='Location B')

    def setUp(self):
        """Create a stock item for each test."""
        super().setUp()

        self.item = StockItem.objects.create(
            part=self.part, quantity=100, location=self.loc_a
        )

    def entries(self, item):
        """Return the audit entries for a stock item (oldest first)."""
        return AuditLogEntry.objects.filter(
            content_type=ContentType.objects.get_for_model(StockItem),
            object_pk=str(item.pk),
        ).order_by('pk')

    def new_entries(self, item, n):
        """Return the audit entries for a stock item, recorded after the first n entries."""
        return list(self.entries(item)[n:])


class StockAuditTest(StockAuditTestBase):
    """Stock operations are recorded as named events in the audit log.

    Each operation records a single audit entry for each affected stock item.
    """

    def test_create(self):
        """Creating a stock item records a single CREATE entry, with the CREATED event."""
        [entry] = self.entries(self.item)

        self.assertEqual(entry.action, ACTION.CREATE)
        self.assertEqual(entry.event_type, StockHistoryCode.CREATED)
        self.assertEqual(entry.event_label, 'Stock item created')

        # The entry is linked to the part
        self.assertEqual(entry.parent_object_pk, str(self.part.pk))

        # Derived fields are not recorded
        self.assertNotIn('serial_int', entry.changes_dict)
        self.assertNotIn('barcode_hash', entry.changes_dict)

    def test_create_via_api(self):
        """Creating a stock item via the API records the user."""
        response = self.post(
            reverse('api-stock-list'),
            {'part': self.part.pk, 'quantity': 5, 'location': self.loc_a.pk},
            expected_code=201,
        )

        item = StockItem.objects.get(pk=response.data[0]['pk'])

        [entry] = self.entries(item)

        self.assertEqual(entry.event_type, StockHistoryCode.CREATED)
        self.assertEqual(entry.actor, self.user)

    def test_create_serialized_via_api(self):
        """Serialized items created via the API are recorded (with status)."""
        response = self.post(
            reverse('api-stock-list'),
            {
                'part': self.trackable.pk,
                'quantity': 3,
                'serial_numbers': '1-3',
                'location': self.loc_a.pk,
                'status': StockStatus.DAMAGED.value,
            },
            expected_code=201,
        )

        self.assertEqual(len(response.data), 3)

        for data in response.data:
            item = StockItem.objects.get(pk=data['pk'])
            self.assertEqual(item.status, StockStatus.DAMAGED.value)

            # A single entry, which records the creation (including the status)
            [entry] = self.entries(item)

            self.assertEqual(entry.action, ACTION.CREATE)
            self.assertEqual(entry.event_type, StockHistoryCode.CREATED)
            self.assertEqual(entry.actor, self.user)
            self.assertEqual(entry.changes_dict['status'][1], StockStatus.DAMAGED.value)

    def test_move(self):
        """Moving the entire stock item records a single entry."""
        n = self.entries(self.item).count()

        self.item.move(self.loc_b, 'Moved', self.user)

        [entry] = self.new_entries(self.item, n)

        self.assertEqual(entry.action, ACTION.UPDATE)
        self.assertEqual(entry.event_type, StockHistoryCode.STOCK_MOVE)
        self.assertEqual(entry.notes, 'Moved')
        self.assertEqual(entry.actor, self.user)
        self.assertEqual(entry.changes_dict['location'], [self.loc_a.pk, self.loc_b.pk])

        # The location is recorded as a field change - not duplicated in the deltas
        self.assertEqual(entry.additional_data['deltas'], {'quantity': 100.0})

    def test_partial_move(self):
        """Moving part of a stock item records an entry for each item."""
        n = self.entries(self.item).count()

        self.item.move(self.loc_b, 'Split', self.user, quantity=30)

        new_item = StockItem.objects.get(parent=self.item)

        # The original item
        [entry] = self.new_entries(self.item, n)

        self.assertEqual(entry.event_type, StockHistoryCode.SPLIT_CHILD_ITEM)
        self.assertEqual(entry.changes_dict['quantity'], ['100.00000', '70.00000'])
        self.assertEqual(
            entry.additional_data['deltas']['stockitem'],
            {'model_type': 'stock.stockitem', 'pk': new_item.pk, 'str': str(new_item)},
        )

        # The new item
        [new_entry] = self.entries(new_item)

        self.assertEqual(new_entry.action, ACTION.CREATE)
        self.assertEqual(new_entry.event_type, StockHistoryCode.SPLIT_FROM_PARENT)
        self.assertEqual(new_entry.changes_dict['location'][1], self.loc_b.pk)

    def test_add_remove_stock(self):
        """Adding / removing stock records a single entry for each operation."""
        n = self.entries(self.item).count()

        self.item.add_stock(10, self.user, notes='Added', batch='B-123')
        self.item.take_stock(5, self.user, notes='Removed')

        add, remove = self.new_entries(self.item, n)

        self.assertEqual(add.event_type, StockHistoryCode.STOCK_ADD)
        self.assertEqual(add.changes_dict['quantity'], ['100.00000', '110.00000'])
        self.assertEqual(add.changes_dict['batch'], ['', 'B-123'])
        self.assertEqual(add.additional_data['deltas'], {'added': 10.0})

        self.assertEqual(remove.event_type, StockHistoryCode.STOCK_REMOVE)
        self.assertEqual(remove.notes, 'Removed')
        self.assertEqual(remove.additional_data['deltas'], {'removed': 5.0})

    def test_stocktake(self):
        """A stocktake is always recorded - even if the quantity is unchanged."""
        n = self.entries(self.item).count()

        # Unchanged quantity
        self.item.stocktake(100, self.user, notes='Counted')

        # Changed quantity
        self.item.stocktake(90, self.user)

        unchanged, changed = self.new_entries(self.item, n)

        self.assertEqual(unchanged.event_type, StockHistoryCode.STOCK_COUNT)
        self.assertEqual(unchanged.notes, 'Counted')

        # Nothing has changed - but the event (and counted quantity) is recorded
        self.assertEqual(unchanged.changes_dict, {})
        self.assertEqual(unchanged.additional_data['deltas'], {'quantity': 100.0})

        self.assertEqual(changed.event_type, StockHistoryCode.STOCK_COUNT)
        self.assertEqual(
            [Decimal(value) for value in changed.changes_dict['quantity']],
            [Decimal(100), Decimal(90)],
        )

    def test_deplete(self):
        """Depleting a stock item (which is then deleted) records the event against the deletion."""
        self.item.delete_on_deplete = True
        self.item.save()

        pk = self.item.pk
        n = self.entries(self.item).count()

        self.item.take_stock(100, self.user)

        self.assertFalse(StockItem.objects.filter(pk=pk).exists())

        [entry] = list(
            AuditLogEntry.objects.filter(
                content_type=ContentType.objects.get_for_model(StockItem),
                object_pk=str(pk),
            ).order_by('pk')[n:]
        )

        self.assertEqual(entry.action, ACTION.DELETE)
        self.assertEqual(entry.event_type, StockHistoryCode.STOCK_REMOVE)

    def test_status_change(self):
        """Changing the status of stock items (via the API) records a single entry for each item."""
        n = self.entries(self.item).count()

        self.post(
            reverse('api-stock-change-status'),
            {
                'items': [self.item.pk],
                'status': StockStatus.DAMAGED.value,
                'note': 'Damaged',
            },
            expected_code=201,
        )

        [entry] = self.new_entries(self.item, n)

        # A regular update (not a named event) - but the note is retained
        self.assertEqual(entry.action, ACTION.UPDATE)
        self.assertIsNone(entry.event_type)
        self.assertEqual(entry.notes, 'Damaged')
        self.assertEqual(entry.actor, self.user)
        self.assertEqual(
            entry.changes_dict['status'],
            [StockStatus.OK.value, StockStatus.DAMAGED.value],
        )

        # Status information is recorded as field changes (not as deltas)
        self.assertIsNone(entry.additional_data)

    def test_edit(self):
        """Editing a stock item (e.g. changing the status) records a regular update entry."""
        n = self.entries(self.item).count()

        self.patch(
            reverse('api-stock-detail', kwargs={'pk': self.item.pk}),
            {'status': StockStatus.DAMAGED.value, 'batch': 'B-999'},
        )

        [entry] = self.new_entries(self.item, n)

        self.assertEqual(entry.action, ACTION.UPDATE)
        self.assertIsNone(entry.event_type)
        self.assertEqual(entry.actor, self.user)
        self.assertEqual(
            entry.changes_dict['status'],
            [StockStatus.OK.value, StockStatus.DAMAGED.value],
        )
        self.assertEqual(entry.changes_dict['batch'], ['', 'B-999'])

    def test_install(self):
        """Installing an item records an entry against both items."""
        assembly = StockItem.objects.create(part=self.assembly, quantity=1)

        n_item = self.entries(self.item).count()
        n_assembly = self.entries(assembly).count()

        assembly.installStockItem(self.item, 100, self.user, 'Installed')

        [item_entry] = self.new_entries(self.item, n_item)
        [assembly_entry] = self.new_entries(assembly, n_assembly)

        self.assertEqual(
            item_entry.event_type, StockHistoryCode.INSTALLED_INTO_ASSEMBLY
        )
        self.assertEqual(item_entry.changes_dict['belongs_to'], [None, assembly.pk])

        # Nothing has changed for the assembly - the event is still recorded
        self.assertEqual(
            assembly_entry.event_type, StockHistoryCode.INSTALLED_CHILD_ITEM
        )
        self.assertEqual(assembly_entry.changes_dict, {})
        self.assertEqual(
            assembly_entry.additional_data['deltas']['stockitem']['pk'], self.item.pk
        )

        # Uninstall
        self.item.refresh_from_db()

        n_item = self.entries(self.item).count()
        n_assembly = self.entries(assembly).count()

        self.item.uninstall_into_location(self.loc_b, self.user, 'Removed')

        [item_entry] = self.new_entries(self.item, n_item)
        [assembly_entry] = self.new_entries(assembly, n_assembly)

        self.assertEqual(item_entry.event_type, StockHistoryCode.REMOVED_FROM_ASSEMBLY)
        self.assertEqual(assembly_entry.event_type, StockHistoryCode.REMOVED_CHILD_ITEM)

    def test_serialize(self):
        """Serializing stock records an entry for each new item, and the original item."""
        item = StockItem.objects.create(part=self.trackable, quantity=5)

        n = self.entries(item).count()

        item.serializeStock(3, ['A1', 'A2', 'A3'], self.user, notes='Serialized')

        [entry] = self.new_entries(item, n)
        self.assertEqual(entry.event_type, StockHistoryCode.STOCK_SERIALIZED)

        for child in StockItem.objects.filter(parent=item):
            [child_entry] = self.entries(child)

            self.assertEqual(child_entry.action, ACTION.CREATE)
            self.assertEqual(child_entry.event_type, StockHistoryCode.SPLIT_FROM_PARENT)
            self.assertEqual(child_entry.actor, self.user)
            self.assertEqual(child_entry.changes_dict['serial'][1], child.serial)

    def test_merge(self):
        """Merging stock items records the event against the merged item."""
        other = StockItem.objects.create(
            part=self.part, quantity=50, location=self.loc_a
        )
        other_pk = other.pk

        n = self.entries(self.item).count()

        self.item.merge_stock_items([other], user=self.user, location=self.loc_a)

        [entry] = self.new_entries(self.item, n)

        self.assertEqual(entry.event_type, StockHistoryCode.MERGED_STOCK_ITEMS)
        self.assertEqual(entry.changes_dict['quantity'], ['100.00000', '150.00000'])

        # The other item was deleted
        self.assertTrue(
            AuditLogEntry.objects.filter(
                object_pk=str(other_pk), action=ACTION.DELETE
            ).exists()
        )

    def test_part_history(self):
        """Stock item entries are included in the history of the part."""
        self.item.move(self.loc_b, '', self.user)

        data = self.get(
            reverse('api-audit-log-list'),
            {'model_type': 'part.part', 'model_id': self.part.pk},
        ).data

        stock_entries = [e for e in data if e['model_type'] == 'stock.stockitem']

        self.assertEqual(len(stock_entries), 2)
        self.assertEqual(stock_entries[0]['event_label'], 'Location changed')

    def test_permissions(self):
        """Stock history is visible to (non-staff) users with permission to view stock."""
        self.user.is_staff = False
        self.user.save()

        url = reverse('api-audit-log-list')
        params = {'model_type': 'stock.stockitem', 'model_id': self.item.pk}

        self.assertEqual(len(self.get(url, params).data), 1)

        self.clearRoles()
        self.assignRole('part.view')

        self.assertEqual(self.get(url, params).data, [])


class StockEventCoverageTest(StockAuditTestBase):
    """Regression tests for the remaining stock tracking event types."""

    def latest(self, item):
        """Return the most recent audit entry for a stock item."""
        return self.entries(item).last()

    def test_update_same_location(self):
        """Moving stock into its current location records a STOCK_UPDATE event."""
        n = self.entries(self.item).count()

        self.item.move(self.loc_a, 'Same place', self.user, batch='B-2')

        [entry] = self.new_entries(self.item, n)

        self.assertEqual(entry.event_type, StockHistoryCode.STOCK_UPDATE)
        self.assertEqual(entry.notes, 'Same place')
        self.assertEqual(entry.changes_dict['batch'], ['', 'B-2'])

    def test_customer(self):
        """Sending stock to a customer (and returning it) records the expected events."""
        from company.models import Company

        customer = Company.objects.create(name='Audit Customer', is_customer=True)

        n = self.entries(self.item).count()

        self.item.allocateToCustomer(customer, user=self.user, notes='Sent')

        [entry] = self.new_entries(self.item, n)

        self.assertEqual(entry.event_type, StockHistoryCode.SENT_TO_CUSTOMER)
        self.assertEqual(entry.changes_dict['customer'], [None, customer.pk])
        self.assertEqual(entry.additional_data['deltas']['quantity'], 100.0)

        # Return the item from the customer
        self.item.refresh_from_db()
        n = self.entries(self.item).count()

        self.item.return_from_customer(self.loc_b, user=self.user, notes='Returned')

        [entry] = self.new_entries(self.item, n)

        self.assertEqual(entry.event_type, StockHistoryCode.RETURNED_FROM_CUSTOMER)
        self.assertEqual(entry.notes, 'Returned')

        # The customer is recorded as a field change (not duplicated in the deltas)
        self.assertEqual(entry.changes_dict['customer'], [customer.pk, None])
        self.assertNotIn('customer', entry.additional_data['deltas'])

    def test_ship_against_order(self):
        """Allocating stock against a sales order records the SHIPPED_AGAINST_SALES_ORDER event."""
        from company.models import Company
        from order.models import SalesOrder

        customer = Company.objects.create(name='Order Customer', is_customer=True)
        order = SalesOrder.objects.create(customer=customer, reference='SO-7777')

        n = self.entries(self.item).count()

        self.item.allocateToCustomer(customer, quantity=40, order=order, user=self.user)

        # The original item is split - the remaining stock records the split
        [entry] = self.new_entries(self.item, n)
        self.assertEqual(entry.event_type, StockHistoryCode.SPLIT_CHILD_ITEM)

        shipped = StockItem.objects.get(parent=self.item)

        # The split item records its creation, and the shipment
        [created, shipped_entry] = self.entries(shipped)

        self.assertEqual(created.event_type, StockHistoryCode.SPLIT_FROM_PARENT)
        self.assertEqual(
            shipped_entry.event_type, StockHistoryCode.SHIPPED_AGAINST_SALES_ORDER
        )
        self.assertEqual(
            shipped_entry.additional_data['deltas']['salesorder']['pk'], order.pk
        )

    def test_return_to_stock(self):
        """Returning (consumed) stock to stock records the RETURNED_TO_STOCK event."""
        from company.models import Company

        customer = Company.objects.create(name='Return Customer', is_customer=True)

        self.item.customer = customer
        self.item.location = None
        self.item.save()

        n = self.entries(self.item).count()

        self.item.return_to_stock(self.loc_b, self.user, notes='Back in stock')

        [entry] = self.new_entries(self.item, n)

        self.assertEqual(entry.event_type, StockHistoryCode.RETURNED_TO_STOCK)
        self.assertEqual(entry.notes, 'Back in stock')
        self.assertEqual(entry.changes_dict['location'], [None, self.loc_b.pk])

    def test_convert_to_variant(self):
        """Converting a stock item to a variant records the CONVERTED_TO_VARIANT event."""
        template = Part.objects.create(
            name='Template', description='A template', is_template=True
        )
        variant = Part.objects.create(
            name='Variant', description='A variant', variant_of=template
        )

        item = StockItem.objects.create(part=template, quantity=5)
        n = self.entries(item).count()

        item.convert_to_variant(variant, self.user)

        [entry] = self.new_entries(item, n)

        self.assertEqual(entry.event_type, StockHistoryCode.CONVERTED_TO_VARIANT)
        self.assertEqual(entry.changes_dict['part'], [template.pk, variant.pk])

    def test_disassemble(self):
        """Disassembling stock records DISASSEMBLED and CREATED_FROM_DISASSEMBLY events."""
        from part.models import BomItem

        bom_item = BomItem.objects.create(
            part=self.assembly, sub_part=self.part, quantity=2
        )

        assembly = StockItem.objects.create(part=self.assembly, quantity=5)
        n = self.entries(assembly).count()

        components = assembly.disassemble(
            2,
            [{'bom_item': bom_item, 'quantity': 4, 'location': self.loc_b}],
            self.user,
            notes='Broken down',
        )

        [entry] = self.new_entries(assembly, n)

        self.assertEqual(entry.event_type, StockHistoryCode.DISASSEMBLED)
        self.assertEqual(entry.additional_data['deltas'], {'removed': 2.0})

        [component] = components
        [entry] = self.entries(component)

        self.assertEqual(entry.action, ACTION.CREATE)
        self.assertEqual(entry.event_type, StockHistoryCode.CREATED_FROM_DISASSEMBLY)
        self.assertEqual(
            entry.additional_data['deltas']['stockitem']['pk'], assembly.pk
        )

    def test_transfer_merge(self):
        """Transferring stock into an existing item (merge) records the event against the merged item."""
        target = StockItem.objects.create(
            part=self.part, quantity=10, location=self.loc_b
        )

        n = self.entries(target).count()

        self.post(
            reverse('api-stock-transfer'),
            {
                'items': [{'pk': self.item.pk, 'quantity': 100, 'merge': True}],
                'location': self.loc_b.pk,
                'notes': 'Merged on transfer',
            },
            expected_code=201,
        )

        target.refresh_from_db()
        self.assertEqual(target.quantity, 110)

        [entry] = self.new_entries(target, n)

        self.assertEqual(entry.event_type, StockHistoryCode.MERGED_STOCK_ITEMS)
        self.assertEqual(entry.notes, 'Merged on transfer')
        self.assertEqual(
            entry.additional_data['deltas']['stockitem']['pk'], self.item.pk
        )
