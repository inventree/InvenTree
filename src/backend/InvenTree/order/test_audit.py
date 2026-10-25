"""Audit log tests for the order models."""

from decimal import Decimal

from django.contrib.contenttypes.models import ContentType
from django.urls import reverse

from audit.models import AuditLogEntry
from order import models
from order.status_codes import PurchaseOrderStatus
from order.test_api import OrderTest
from stock.models import StockLocation

ACTION = AuditLogEntry.Action


class OrderAuditTestBase(OrderTest):
    """Base class for order audit tests."""

    roles = [
        f'{ruleset}.{perm}'
        for ruleset in [
            'purchase_order',
            'sales_order',
            'return_order',
            'transfer_order',
        ]
        for perm in ['view', 'add', 'change', 'delete']
    ] + ['part.view', 'stock.view', 'stock.add', 'stock_location.view']

    def entries(self, model, pk, **filters):
        """Return audit entries for a given object (by PK - which survives deletion)."""
        return AuditLogEntry.objects.filter(
            content_type=ContentType.objects.get_for_model(model),
            object_pk=str(pk),
            **filters,
        )

    def history(self, model_type: str, pk, **params):
        """Return the audit history for an object (including child entries)."""
        return self.get(
            reverse('api-audit-log-list'),
            {'model_type': model_type, 'model_id': pk, **params},
        ).data

    def check_child_crud(
        self, parent, child_model, list_url, detail_url, create, update
    ):
        """Create / update / delete a child (line) object via the API.

        Checks that each entry is linked to the parent order, and appears in its history.

        Returns:
            The UPDATE entry
        """
        pk = self.post(reverse(list_url), create).data['pk']

        url = reverse(detail_url, kwargs={'pk': pk})
        self.patch(url, update)
        self.delete(url)

        entries = self.entries(child_model, pk)

        self.assertEqual(
            sorted(entries.values_list('action', flat=True)),
            [ACTION.CREATE, ACTION.UPDATE, ACTION.DELETE],
        )

        for entry in entries:
            self.assertEqual(entry.actor, self.user)
            self.assertEqual(entry.parent_object_pk, str(parent.pk))
            self.assertNotIn('context', entry.changes_dict)
            self.assertNotIn('line_int', entry.changes_dict)

            # A meaningful string representation (not the Django default)
            self.assertNotIn(' object (', entry.object_repr)

        label = f'{child_model._meta.app_label}.{child_model._meta.model_name}'
        parent_label = f'{parent._meta.app_label}.{parent._meta.model_name}'

        child_actions = [
            e['action']
            for e in self.history(parent_label, parent.pk)
            if e['model_type'] == label
        ]

        self.assertEqual(
            sorted(child_actions), [ACTION.CREATE, ACTION.UPDATE, ACTION.DELETE]
        )

        return entries.get(action=ACTION.UPDATE)


class PurchaseOrderAuditTest(OrderAuditTestBase):
    """Audit tests for PurchaseOrder, PurchaseOrderLineItem and PurchaseOrderExtraLine."""

    def test_order_edit(self):
        """Order edits are recorded - without the (derived) total price."""
        po = models.PurchaseOrder.objects.get(pk=1)

        self.patch(
            reverse('api-po-detail', kwargs={'pk': po.pk}),
            {'description': 'Audited description', 'supplier_reference': 'SUP-1'},
        )

        entry = self.entries(models.PurchaseOrder, po.pk, action=ACTION.UPDATE).get()

        self.assertEqual(entry.actor, self.user)
        self.assertEqual(entry.changes_dict['description'][1], 'Audited description')
        self.assertEqual(entry.changes_dict['supplier_reference'][1], 'SUP-1')

        for field in ['total_price', 'total_price_currency', 'updated_at']:
            self.assertNotIn(field, entry.changes_dict)

    def test_order_currency(self):
        """Changes to the order currency (not a MoneyField currency) are recorded."""
        po = models.PurchaseOrder.objects.get(pk=1)
        po.order_currency = 'AUD'
        po.save()

        entry = (
            self
            .entries(models.PurchaseOrder, po.pk, action=ACTION.UPDATE)
            .order_by('pk')
            .last()
        )
        self.assertEqual(entry.changes_dict['order_currency'][1], 'AUD')

    def test_total_price_not_recorded(self):
        """Saving an order (which recalculates the total price) records no entry."""
        po = models.PurchaseOrder.objects.get(pk=1)

        # Initial save (fixture data has no creation_date, which is set on save)
        po.save()
        n = self.entries(models.PurchaseOrder, po.pk, action=ACTION.UPDATE).count()

        po.refresh_from_db()
        total = po.total_price

        # Change the price of a line, then re-save the order (total price changes)
        line = po.lines.first()
        line.purchase_price = 123.45
        line.save()

        po.save()
        po.refresh_from_db()

        # Sanity check - the total price has changed
        self.assertNotEqual(po.total_price, total)

        self.assertEqual(
            self.entries(models.PurchaseOrder, po.pk, action=ACTION.UPDATE).count(), n
        )

    def test_status_change(self):
        """Issuing an order (status change) is recorded."""
        po = models.PurchaseOrder.objects.get(pk=1)
        self.assertEqual(po.status, PurchaseOrderStatus.PENDING)

        self.post(reverse('api-po-issue', kwargs={'pk': po.pk}), {}, expected_code=201)

        entry = self.entries(models.PurchaseOrder, po.pk, action=ACTION.UPDATE).get()

        self.assertEqual(entry.actor, self.user)
        self.assertEqual(
            entry.changes_dict['status'],
            [PurchaseOrderStatus.PENDING.value, PurchaseOrderStatus.PLACED.value],
        )

    def test_line_items(self):
        """Line item changes are recorded against the order."""
        po = models.PurchaseOrder.objects.get(pk=1)
        supplier_part = po.lines.first().part

        update = self.check_child_crud(
            po,
            models.PurchaseOrderLineItem,
            'api-po-line-list',
            'api-po-line-detail',
            {'order': po.pk, 'part': supplier_part.pk, 'quantity': 5},
            # Note: the serializer requires 'order' and 'part', even for PATCH requests
            # (pre-existing: validate() does not fall back to the instance values)
            {
                'order': po.pk,
                'part': supplier_part.pk,
                'quantity': 8,
                'reference': 'Audit',
            },
        )

        # Note: decimal values are recorded as strings
        self.assertEqual([Decimal(v) for v in update.changes_dict['quantity']], [5, 8])
        self.assertEqual(update.changes_dict['reference'], ['', 'Audit'])

        # Numeric fields are flagged for display formatting (decimals are stored as strings)
        [entry] = [
            e
            for e in self.history(
                'order.purchaseorder', po.pk, changes_detail=True, action=ACTION.UPDATE
            )
            if e['pk'] == update.pk
        ]
        rows = {row['field']: row for row in entry['changes_detail']}

        self.assertTrue(rows['quantity']['numeric'])
        self.assertFalse(rows['reference']['numeric'])

    def test_extra_lines(self):
        """Extra line changes are recorded against the order."""
        po = models.PurchaseOrder.objects.get(pk=1)

        update = self.check_child_crud(
            po,
            models.PurchaseOrderExtraLine,
            'api-po-extra-line-list',
            'api-po-extra-line-detail',
            {
                'order': po.pk,
                'quantity': 1,
                'description': 'Freight',
                'price': '10.00',
                'price_currency': 'USD',
            },
            {'description': 'Express freight', 'price': '25.00'},
        )

        self.assertEqual(
            update.changes_dict['description'], ['Freight', 'Express freight']
        )
        self.assertIn('price', update.changes_dict)

    def test_receive(self):
        """Received quantities (updated in bulk) are recorded against the user."""
        po = models.PurchaseOrder.objects.get(pk=1)
        po.status = PurchaseOrderStatus.PLACED.value
        po.save()

        lines = list(po.lines.all()[:2])
        location = StockLocation.objects.filter(structural=False).first()

        self.post(
            reverse('api-po-receive', kwargs={'pk': po.pk}),
            {
                'items': [
                    {'line_item': line.pk, 'quantity': 3, 'status': 10}
                    for line in lines
                ],
                'location': location.pk,
            },
            expected_code=201,
        )

        for line in lines:
            entry = self.entries(
                models.PurchaseOrderLineItem,
                line.pk,
                action=ACTION.UPDATE,
                changes__has_key='received',
            ).get()

            self.assertEqual(entry.actor, self.user)
            old, new = (Decimal(v) for v in entry.changes_dict['received'])
            self.assertEqual(old, line.received)
            self.assertEqual(new, line.received + 3)
            self.assertEqual(entry.parent_object_pk, str(po.pk))

        # Each received stock item records a single entry (creation, with the event)
        from stock.models import StockItem
        from stock.status_codes import StockHistoryCode

        items = StockItem.objects.filter(purchase_order=po)
        self.assertEqual(items.count(), 2)

        for item in items:
            [entry] = self.entries(StockItem, item.pk)

            self.assertEqual(entry.action, ACTION.CREATE)
            self.assertEqual(
                entry.event_type, StockHistoryCode.RECEIVED_AGAINST_PURCHASE_ORDER
            )
            self.assertEqual(entry.actor, self.user)
            self.assertEqual(entry.changes_dict['location'][1], location.pk)


class SalesOrderAuditTest(OrderAuditTestBase):
    """Audit tests for SalesOrder, line items, extra lines and shipments."""

    @classmethod
    def setUpTestData(cls):
        """Create a simple sales order to test against."""
        from company.models import Company
        from part.models import Part
        from stock.models import StockItem

        super().setUpTestData()

        cls.customer = Company.objects.create(name='Audit Customer', is_customer=True)
        cls.part = Part.objects.create(
            name='Audit Widget', description='A widget', salable=True
        )
        cls.stock = StockItem.objects.create(part=cls.part, quantity=100)

        cls.order = models.SalesOrder.objects.create(
            customer=cls.customer, reference='SO-9001'
        )

    def test_order_edit(self):
        """Order edits are recorded - without the (derived) total price."""
        self.patch(
            reverse('api-so-detail', kwargs={'pk': self.order.pk}),
            {'description': 'Audited', 'customer_reference': 'CUST-9'},
        )

        entry = self.entries(
            models.SalesOrder, self.order.pk, action=ACTION.UPDATE
        ).get()

        self.assertEqual(entry.actor, self.user)
        self.assertEqual(entry.changes_dict['customer_reference'][1], 'CUST-9')
        self.assertNotIn('total_price', entry.changes_dict)

    def test_line_items(self):
        """Line item changes are recorded against the order."""
        update = self.check_child_crud(
            self.order,
            models.SalesOrderLineItem,
            'api-so-line-list',
            'api-so-line-detail',
            {'order': self.order.pk, 'part': self.part.pk, 'quantity': 5},
            {'quantity': 7, 'sale_price': '12.50', 'sale_price_currency': 'USD'},
        )

        self.assertEqual([Decimal(v) for v in update.changes_dict['quantity']], [5, 7])
        self.assertIn('sale_price', update.changes_dict)
        self.assertEqual(
            update.object_repr, f'7 x {self.part.full_name} - {self.order}'
        )

    def test_extra_lines(self):
        """Extra line changes are recorded against the order."""
        update = self.check_child_crud(
            self.order,
            models.SalesOrderExtraLine,
            'api-so-extra-line-list',
            'api-so-extra-line-detail',
            {'order': self.order.pk, 'quantity': 1, 'description': 'Packaging'},
            {'description': 'Gift wrapping'},
        )

        self.assertEqual(
            update.changes_dict['description'], ['Packaging', 'Gift wrapping']
        )
        self.assertEqual(update.object_repr, f'1 x Gift wrapping - {self.order}')

    def test_shipments(self):
        """Shipment changes are recorded against the order, and the shipment itself."""
        update = self.check_child_crud(
            self.order,
            models.SalesOrderShipment,
            'api-so-shipment-list',
            'api-so-shipment-detail',
            {'order': self.order.pk, 'reference': 'SHIP-1'},
            {'tracking_number': 'TRACK-123', 'invoice_number': 'INV-9'},
        )

        self.assertEqual(update.changes_dict['tracking_number'], ['', 'TRACK-123'])
        self.assertNotIn('barcode_hash', update.changes_dict)

    def test_shipment_history(self):
        """The shipment History tab shows the shipment's own entries."""
        shipment = models.SalesOrderShipment.objects.create(
            order=self.order, reference='SHIP-2'
        )

        self.patch(
            reverse('api-so-shipment-detail', kwargs={'pk': shipment.pk}),
            {'tracking_number': 'ABC'},
        )

        history = self.history('order.salesordershipment', shipment.pk)

        self.assertEqual(
            sorted(e['action'] for e in history), [ACTION.CREATE, ACTION.UPDATE]
        )

        for entry in history:
            self.assertEqual(entry['model_type'], 'order.salesordershipment')
            self.assertEqual(entry['parent_object_pk'], str(self.order.pk))

    def test_complete_shipment(self):
        """Shipped quantities (updated in bulk) are recorded against the user."""
        line = models.SalesOrderLineItem.objects.create(
            order=self.order, part=self.part, quantity=10
        )
        shipment = models.SalesOrderShipment.objects.create(
            order=self.order, reference='SHIP-3'
        )

        self.order.issue_order()

        models.SalesOrderAllocation.objects.create(
            line=line, shipment=shipment, item=self.stock, quantity=4
        )

        # Run in the request context of the test user (e.g. as via the API)
        from auditlog.context import set_actor

        with set_actor(self.user):
            shipment.complete_shipment(self.user)

        entry = self.entries(
            models.SalesOrderLineItem,
            line.pk,
            action=ACTION.UPDATE,
            changes__has_key='shipped',
        ).get()

        self.assertEqual(entry.actor, self.user)
        self.assertEqual([Decimal(v) for v in entry.changes_dict['shipped']], [0, 4])
        self.assertEqual(entry.parent_object_pk, str(self.order.pk))

        # Shipment completion is recorded too
        shipment_entry = self.entries(
            models.SalesOrderShipment,
            shipment.pk,
            action=ACTION.UPDATE,
            changes__has_key='shipment_date',
        ).get()

        self.assertIsNone(shipment_entry.changes_dict['shipment_date'][0])

        # Stock items record a single entry each
        from stock.models import StockItem
        from stock.status_codes import StockHistoryCode

        [source_entry] = self.entries(
            StockItem, self.stock.pk, event_type__isnull=False
        ).exclude(event_type=StockHistoryCode.CREATED)

        self.assertEqual(source_entry.event_type, StockHistoryCode.SPLIT_CHILD_ITEM)
        self.assertEqual(source_entry.actor, self.user)

        shipped = StockItem.objects.get(parent=self.stock)

        [shipped_entry] = self.entries(StockItem, shipped.pk)

        self.assertEqual(shipped_entry.action, ACTION.CREATE)
        self.assertEqual(
            shipped_entry.event_type, StockHistoryCode.SHIPPED_AGAINST_SALES_ORDER
        )
        self.assertEqual(shipped_entry.changes_dict['customer'][1], self.customer.pk)


class ReturnOrderAuditTest(OrderAuditTestBase):
    """Audit tests for ReturnOrder, line items and extra lines."""

    @classmethod
    def setUpTestData(cls):
        """Create a simple return order to test against."""
        from company.models import Company
        from part.models import Part
        from stock.models import StockItem

        super().setUpTestData()

        cls.customer = Company.objects.create(name='Returning Co', is_customer=True)
        cls.part = Part.objects.create(
            name='Returned Widget', description='A widget', salable=True
        )
        cls.item = StockItem.objects.create(
            part=cls.part, quantity=1, serial='RMA-1', customer=cls.customer
        )

        cls.order = models.ReturnOrder.objects.create(
            customer=cls.customer, reference='RMA-9001'
        )

    def test_order_edit(self):
        """Order edits are recorded."""
        self.patch(
            reverse('api-return-order-detail', kwargs={'pk': self.order.pk}),
            {'description': 'Faulty units', 'customer_reference': 'C-77'},
        )

        entry = self.entries(
            models.ReturnOrder, self.order.pk, action=ACTION.UPDATE
        ).get()

        self.assertEqual(entry.actor, self.user)
        self.assertEqual(entry.changes_dict['description'][1], 'Faulty units')
        self.assertNotIn('total_price', entry.changes_dict)

    def test_line_items(self):
        """Line item changes (including the outcome status) are recorded against the order."""
        from order.status_codes import ReturnOrderLineStatus

        update = self.check_child_crud(
            self.order,
            models.ReturnOrderLineItem,
            'api-return-order-line-list',
            'api-return-order-line-detail',
            {'order': self.order.pk, 'item': self.item.pk},
            {'outcome': ReturnOrderLineStatus.REFUND.value, 'notes': 'Refund issued'},
        )

        self.assertEqual(
            update.changes_dict['outcome'][1], ReturnOrderLineStatus.REFUND.value
        )

    def test_extra_lines(self):
        """Extra line changes are recorded against the order."""
        update = self.check_child_crud(
            self.order,
            models.ReturnOrderExtraLine,
            'api-return-order-extra-line-list',
            'api-return-order-extra-line-detail',
            {'order': self.order.pk, 'quantity': 1, 'description': 'Restocking fee'},
            {'description': 'Inspection fee'},
        )

        self.assertEqual(
            update.changes_dict['description'], ['Restocking fee', 'Inspection fee']
        )

    def test_receive_stock(self):
        """Receiving an item against a return order records a single entry."""
        from stock.models import StockItem
        from stock.status_codes import StockHistoryCode, StockStatus

        location = StockLocation.objects.create(name='Returns')

        line = models.ReturnOrderLineItem.objects.create(
            order=self.order, item=self.item
        )

        self.order.issue_order()

        n = self.entries(StockItem, self.item.pk).count()

        self.order.receive_line_item(line, location, self.user, note='Inspected')

        [entry] = list(self.entries(StockItem, self.item.pk).order_by('pk')[n:])

        self.assertEqual(
            entry.event_type, StockHistoryCode.RETURNED_AGAINST_RETURN_ORDER
        )
        self.assertEqual(entry.actor, self.user)
        self.assertEqual(entry.notes, 'Inspected')
        self.assertEqual(entry.changes_dict['location'][1], location.pk)
        self.assertEqual(entry.changes_dict['status'][1], StockStatus.QUARANTINED.value)
        self.assertEqual(
            entry.additional_data['deltas']['returnorder']['pk'], self.order.pk
        )


class TransferOrderAuditTest(OrderAuditTestBase):
    """Audit tests for TransferOrder and line items."""

    @classmethod
    def setUpTestData(cls):
        """Create a simple transfer order to test against."""
        from part.models import Part
        from stock.models import StockItem

        super().setUpTestData()

        cls.source = StockLocation.objects.create(name='Audit Source')
        cls.target = StockLocation.objects.create(name='Audit Target')

        cls.part = Part.objects.create(name='Moved Widget', description='A widget')
        cls.stock = StockItem.objects.create(
            part=cls.part, quantity=50, location=cls.source
        )

        cls.order = models.TransferOrder.objects.create(
            reference='TO-9001', take_from=cls.source, destination=cls.target
        )

    def test_order_edit(self):
        """Order edits are recorded."""
        self.patch(
            reverse('api-transfer-order-detail', kwargs={'pk': self.order.pk}),
            {'description': 'Restock line side'},
        )

        entry = self.entries(
            models.TransferOrder, self.order.pk, action=ACTION.UPDATE
        ).get()

        self.assertEqual(entry.actor, self.user)
        self.assertEqual(entry.changes_dict['description'][1], 'Restock line side')

    def test_line_items(self):
        """Line item changes are recorded against the order."""
        update = self.check_child_crud(
            self.order,
            models.TransferOrderLineItem,
            'api-transfer-order-line-list',
            'api-transfer-order-line-detail',
            {'order': self.order.pk, 'part': self.part.pk, 'quantity': 10},
            {'quantity': 12},
        )

        self.assertEqual(
            [Decimal(v) for v in update.changes_dict['quantity']], [10, 12]
        )

    def test_transferred(self):
        """The 'transferred' quantity (updated via an F() expression) is recorded as a number."""
        line = models.TransferOrderLineItem.objects.create(
            order=self.order, part=self.part, quantity=10
        )

        self.order.issue_order()

        allocation = models.TransferOrderAllocation.objects.create(
            line=line, item=self.stock, quantity=6
        )

        allocation.complete_allocation(self.user)

        line.refresh_from_db()
        self.assertEqual(line.transferred, 6)

        entry = self.entries(
            models.TransferOrderLineItem,
            line.pk,
            action=ACTION.UPDATE,
            changes__has_key='transferred',
        ).get()

        self.assertEqual(
            [Decimal(v) for v in entry.changes_dict['transferred']], [0, 6]
        )
        self.assertNotIn('F(', str(entry.changes))
        self.assertEqual(entry.parent_object_pk, str(self.order.pk))

        # The transferred stock records a single STOCK_MOVE event (linked to the order)
        from stock.models import StockItem
        from stock.status_codes import StockHistoryCode

        moved = StockItem.objects.get(parent=self.stock)

        [created] = self.entries(StockItem, moved.pk)

        self.assertEqual(created.event_type, StockHistoryCode.SPLIT_FROM_PARENT)
        self.assertEqual(created.changes_dict['location'][1], self.target.pk)
        self.assertEqual(
            created.additional_data['deltas']['transferorder']['pk'], self.order.pk
        )
