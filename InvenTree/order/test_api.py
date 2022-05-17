"""
Tests for the Order API
"""

import io

from datetime import datetime, timedelta

from rest_framework import status

from django.urls import reverse

from InvenTree.api_tester import InvenTreeAPITestCase
from InvenTree.status_codes import PurchaseOrderStatus, SalesOrderStatus

from part.models import Part
from stock.models import StockItem

import order.models as models


class OrderTest(InvenTreeAPITestCase):

    fixtures = [
        'category',
        'part',
        'company',
        'location',
        'supplier_part',
        'stock',
        'order',
        'sales_order',
    ]

    roles = [
        'purchase_order.change',
        'sales_order.change',
    ]

    def setUp(self):
        super().setUp()

    def filter(self, filters, count):
        """
        Test API filters
        """

        response = self.get(
            self.LIST_URL,
            filters
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), count)

        return response


class PurchaseOrderTest(OrderTest):
    """
    Tests for the PurchaseOrder API
    """

    LIST_URL = reverse('api-po-list')

    def test_po_list(self):

        # List *ALL* PurchaseOrder items
        self.filter({}, 7)

        # Filter by supplier
        self.filter({'supplier': 1}, 1)
        self.filter({'supplier': 3}, 5)

        # Filter by "outstanding"
        self.filter({'outstanding': True}, 5)
        self.filter({'outstanding': False}, 2)

        # Filter by "status"
        self.filter({'status': 10}, 3)
        self.filter({'status': 40}, 1)

    def test_overdue(self):
        """
        Test "overdue" status
        """

        self.filter({'overdue': True}, 0)
        self.filter({'overdue': False}, 7)

        order = models.PurchaseOrder.objects.get(pk=1)
        order.target_date = datetime.now().date() - timedelta(days=10)
        order.save()

        self.filter({'overdue': True}, 1)
        self.filter({'overdue': False}, 6)

    def test_po_detail(self):

        url = '/api/order/po/1/'

        response = self.get(url)

        self.assertEqual(response.status_code, 200)

        data = response.data

        self.assertEqual(data['pk'], 1)
        self.assertEqual(data['description'], 'Ordering some screws')

    def test_po_reference(self):
        """test that a reference with a too big / small reference is not possible"""
        # get permissions
        self.assignRole('purchase_order.add')

        url = reverse('api-po-list')
        huge_number = 9223372036854775808

        self.post(
            url,
            {
                'supplier': 1,
                'reference': huge_number,
                'description': 'PO not created via the API',
            },
            expected_code=201,
        )

    def test_po_attachments(self):

        url = reverse('api-po-attachment-list')

        response = self.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_po_operations(self):
        """
        Test that we can create / edit and delete a PurchaseOrder via the API
        """

        n = models.PurchaseOrder.objects.count()

        url = reverse('api-po-list')

        # Initially we do not have "add" permission for the PurchaseOrder model,
        # so this POST request should return 403
        response = self.post(
            url,
            {
                'supplier': 1,
                'reference': '123456789-xyz',
                'description': 'PO created via the API',
            },
            expected_code=403
        )

        # And no new PurchaseOrder objects should have been created
        self.assertEqual(models.PurchaseOrder.objects.count(), n)

        # Ok, now let's give this user the correct permission
        self.assignRole('purchase_order.add')

        # Initially we do not have "add" permission for the PurchaseOrder model,
        # so this POST request should return 403
        response = self.post(
            url,
            {
                'supplier': 1,
                'reference': '123456789-xyz',
                'description': 'PO created via the API',
            },
            expected_code=201
        )

        self.assertEqual(models.PurchaseOrder.objects.count(), n + 1)

        pk = response.data['pk']

        # Try to create a PurchaseOrder with identical reference (should fail!)
        response = self.post(
            url,
            {
                'supplier': 1,
                'reference': '123456789-xyz',
                'description': 'A different description',
            },
            expected_code=400
        )

        self.assertEqual(models.PurchaseOrder.objects.count(), n + 1)

        url = reverse('api-po-detail', kwargs={'pk': pk})

        # Get detail info!
        response = self.get(url)
        self.assertEqual(response.data['pk'], pk)
        self.assertEqual(response.data['reference'], '123456789-xyz')

        # Try to alter (edit) the PurchaseOrder
        response = self.patch(
            url,
            {
                'reference': '12345-abc',
            },
            expected_code=200
        )

        # Reference should have changed
        self.assertEqual(response.data['reference'], '12345-abc')

        # Now, let's try to delete it!
        # Initially, we do *not* have the required permission!
        response = self.delete(url, expected_code=403)

        # Now, add the "delete" permission!
        self.assignRole("purchase_order.delete")

        response = self.delete(url, expected_code=204)

        # Number of PurchaseOrder objects should have decreased
        self.assertEqual(models.PurchaseOrder.objects.count(), n)

        # And if we try to access the detail view again, it has gone
        response = self.get(url, expected_code=404)

    def test_po_create(self):
        """
        Test that we can create a new PurchaseOrder via the API
        """

        self.assignRole('purchase_order.add')

        self.post(
            reverse('api-po-list'),
            {
                'reference': '12345678',
                'supplier': 1,
                'description': 'A test purchase order',
            },
            expected_code=201
        )

    def test_po_cancel(self):
        """
        Test the PurchaseOrderCancel API endpoint
        """

        po = models.PurchaseOrder.objects.get(pk=1)

        self.assertEqual(po.status, PurchaseOrderStatus.PENDING)

        url = reverse('api-po-cancel', kwargs={'pk': po.pk})

        # Try to cancel the PO, but without reqiured permissions
        self.post(url, {}, expected_code=403)

        self.assignRole('purchase_order.add')

        self.post(
            url,
            {},
            expected_code=201,
        )

        po.refresh_from_db()

        self.assertEqual(po.status, PurchaseOrderStatus.CANCELLED)

        # Try to cancel again (should fail)
        self.post(url, {}, expected_code=400)

    def test_po_complete(self):
        """ Test the PurchaseOrderComplete API endpoint """

        po = models.PurchaseOrder.objects.get(pk=3)

        url = reverse('api-po-complete', kwargs={'pk': po.pk})

        self.assertEqual(po.status, PurchaseOrderStatus.PLACED)

        # Try to complete the PO, without required permissions
        self.post(url, {}, expected_code=403)

        self.assignRole('purchase_order.add')

        self.post(url, {}, expected_code=201)

        po.refresh_from_db()

        self.assertEqual(po.status, PurchaseOrderStatus.COMPLETE)

    def test_po_issue(self):
        """ Test the PurchaseOrderIssue API endpoint """

        po = models.PurchaseOrder.objects.get(pk=2)

        url = reverse('api-po-issue', kwargs={'pk': po.pk})

        # Try to issue the PO, without required permissions
        self.post(url, {}, expected_code=403)

        self.assignRole('purchase_order.add')

        self.post(url, {}, expected_code=201)

        po.refresh_from_db()

        self.assertEqual(po.status, PurchaseOrderStatus.PLACED)

    def test_po_metadata(self):
        url = reverse('api-po-metadata', kwargs={'pk': 1})

        self.patch(
            url,
            {
                'metadata': {
                    'yam': 'yum',
                }
            },
            expected_code=200
        )

        order = models.PurchaseOrder.objects.get(pk=1)
        self.assertEqual(order.get_metadata('yam'), 'yum')


class PurchaseOrderDownloadTest(OrderTest):
    """Unit tests for downloading PurchaseOrder data via the API endpoint"""

    required_cols = [
        'id',
        'line_items',
        'description',
        'issue_date',
        'notes',
        'reference',
        'status',
        'supplier_reference',
    ]

    excluded_cols = [
        'metadata',
    ]

    def test_download_wrong_format(self):
        """Incorrect format should default raise an error"""

        url = reverse('api-po-list')

        with self.assertRaises(ValueError):
            self.download_file(
                url,
                {
                    'export': 'xyz',
                }
            )

    def test_download_csv(self):
        """Download PurchaseOrder data as .csv"""

        with self.download_file(
            reverse('api-po-list'),
            {
                'export': 'csv',
            },
            expected_code=200,
            expected_fn='InvenTree_PurchaseOrders.csv',
        ) as fo:

            data = self.process_csv(
                fo,
                required_cols=self.required_cols,
                excluded_cols=self.excluded_cols,
                required_rows=models.PurchaseOrder.objects.count()
            )

            for row in data:
                order = models.PurchaseOrder.objects.get(pk=row['id'])

                self.assertEqual(order.description, row['description'])
                self.assertEqual(order.reference, row['reference'])


class PurchaseOrderReceiveTest(OrderTest):
    """
    Unit tests for receiving items against a PurchaseOrder
    """

    def setUp(self):
        super().setUp()

        self.assignRole('purchase_order.add')

        self.url = reverse('api-po-receive', kwargs={'pk': 1})

        # Number of stock items which exist at the start of each test
        self.n = StockItem.objects.count()

        # Mark the order as "placed" so we can receive line items
        order = models.PurchaseOrder.objects.get(pk=1)
        order.status = PurchaseOrderStatus.PLACED
        order.save()

    def test_empty(self):
        """
        Test without any POST data
        """

        data = self.post(self.url, {}, expected_code=400).data

        self.assertIn('This field is required', str(data['items']))
        self.assertIn('This field is required', str(data['location']))

        # No new stock items have been created
        self.assertEqual(self.n, StockItem.objects.count())

    def test_no_items(self):
        """
        Test with an empty list of items
        """

        data = self.post(
            self.url,
            {
                "items": [],
                "location": None,
            },
            expected_code=400
        ).data

        self.assertIn('Line items must be provided', str(data))

        # No new stock items have been created
        self.assertEqual(self.n, StockItem.objects.count())

    def test_invalid_items(self):
        """
        Test than errors are returned as expected for invalid data
        """

        data = self.post(
            self.url,
            {
                "items": [
                    {
                        "line_item": 12345,
                        "location": 12345
                    }
                ]
            },
            expected_code=400
        ).data

        items = data['items'][0]

        self.assertIn('Invalid pk "12345"', str(items['line_item']))
        self.assertIn("object does not exist", str(items['location']))

        # No new stock items have been created
        self.assertEqual(self.n, StockItem.objects.count())

    def test_invalid_status(self):
        """
        Test with an invalid StockStatus value
        """

        data = self.post(
            self.url,
            {
                "items": [
                    {
                        "line_item": 22,
                        "location": 1,
                        "status": 99999,
                        "quantity": 5,
                    }
                ]
            },
            expected_code=400
        ).data

        self.assertIn('"99999" is not a valid choice.', str(data))

        # No new stock items have been created
        self.assertEqual(self.n, StockItem.objects.count())

    def test_mismatched_items(self):
        """
        Test for supplier parts which *do* exist but do not match the order supplier
        """

        data = self.post(
            self.url,
            {
                'items': [
                    {
                        'line_item': 22,
                        'quantity': 123,
                        'location': 1,
                    }
                ],
                'location': None,
            },
            expected_code=400
        ).data

        self.assertIn('Line item does not match purchase order', str(data))

        # No new stock items have been created
        self.assertEqual(self.n, StockItem.objects.count())

    def test_null_barcode(self):
        """
        Test than a "null" barcode field can be provided
        """

        # Set stock item barcode
        item = StockItem.objects.get(pk=1)
        item.save()

        # Test with "null" value
        self.post(
            self.url,
            {
                'items': [
                    {
                        'line_item': 1,
                        'quantity': 50,
                        'barcode': None,
                    }
                ],
                'location': 1,
            },
            expected_code=201
        )

    def test_invalid_barcodes(self):
        """
        Tests for checking in items with invalid barcodes:

        - Cannot check in "duplicate" barcodes
        - Barcodes cannot match UID field for existing StockItem
        """

        # Set stock item barcode
        item = StockItem.objects.get(pk=1)
        item.uid = 'MY-BARCODE-HASH'
        item.save()

        response = self.post(
            self.url,
            {
                'items': [
                    {
                        'line_item': 1,
                        'quantity': 50,
                        'barcode': 'MY-BARCODE-HASH',
                    }
                ],
                'location': 1,
            },
            expected_code=400
        )

        self.assertIn('Barcode is already in use', str(response.data))

        response = self.post(
            self.url,
            {
                'items': [
                    {
                        'line_item': 1,
                        'quantity': 5,
                        'barcode': 'MY-BARCODE-HASH-1',
                    },
                    {
                        'line_item': 1,
                        'quantity': 5,
                        'barcode': 'MY-BARCODE-HASH-1'
                    },
                ],
                'location': 1,
            },
            expected_code=400
        )

        self.assertIn('barcode values must be unique', str(response.data))

        # No new stock items have been created
        self.assertEqual(self.n, StockItem.objects.count())

    def test_valid(self):
        """
        Test receipt of valid data
        """

        line_1 = models.PurchaseOrderLineItem.objects.get(pk=1)
        line_2 = models.PurchaseOrderLineItem.objects.get(pk=2)

        self.assertEqual(StockItem.objects.filter(supplier_part=line_1.part).count(), 0)
        self.assertEqual(StockItem.objects.filter(supplier_part=line_2.part).count(), 0)

        self.assertEqual(line_1.received, 0)
        self.assertEqual(line_2.received, 50)

        valid_data = {
            'items': [
                {
                    'line_item': 1,
                    'quantity': 50,
                    'barcode': 'MY-UNIQUE-BARCODE-123',
                },
                {
                    'line_item': 2,
                    'quantity': 200,
                    'location': 2,  # Explicit location
                    'barcode': 'MY-UNIQUE-BARCODE-456',
                }
            ],
            'location': 1,  # Default location
        }

        # Before posting "valid" data, we will mark the purchase order as "pending"
        # In this case we do expect an error!
        order = models.PurchaseOrder.objects.get(pk=1)
        order.status = PurchaseOrderStatus.PENDING
        order.save()

        response = self.post(
            self.url,
            valid_data,
            expected_code=400
        )

        self.assertIn('can only be received against', str(response.data))

        # Now, set the PurchaseOrder back to "PLACED" so the items can be received
        order.status = PurchaseOrderStatus.PLACED
        order.save()

        # Receive two separate line items against this order
        self.post(
            self.url,
            valid_data,
            expected_code=201,
        )

        # There should be two newly created stock items
        self.assertEqual(self.n + 2, StockItem.objects.count())

        line_1 = models.PurchaseOrderLineItem.objects.get(pk=1)
        line_2 = models.PurchaseOrderLineItem.objects.get(pk=2)

        self.assertEqual(line_1.received, 50)
        self.assertEqual(line_2.received, 250)

        stock_1 = StockItem.objects.filter(supplier_part=line_1.part)
        stock_2 = StockItem.objects.filter(supplier_part=line_2.part)

        # 1 new stock item created for each supplier part
        self.assertEqual(stock_1.count(), 1)
        self.assertEqual(stock_2.count(), 1)

        # Different location for each received item
        self.assertEqual(stock_1.last().location.pk, 1)
        self.assertEqual(stock_2.last().location.pk, 2)

        # Barcodes should have been assigned to the stock items
        self.assertTrue(StockItem.objects.filter(uid='MY-UNIQUE-BARCODE-123').exists())
        self.assertTrue(StockItem.objects.filter(uid='MY-UNIQUE-BARCODE-456').exists())

    def test_batch_code(self):
        """
        Test that we can supply a 'batch code' when receiving items
        """

        line_1 = models.PurchaseOrderLineItem.objects.get(pk=1)
        line_2 = models.PurchaseOrderLineItem.objects.get(pk=2)

        self.assertEqual(StockItem.objects.filter(supplier_part=line_1.part).count(), 0)
        self.assertEqual(StockItem.objects.filter(supplier_part=line_2.part).count(), 0)

        data = {
            'items': [
                {
                    'line_item': 1,
                    'quantity': 10,
                    'batch_code': 'abc-123',
                },
                {
                    'line_item': 2,
                    'quantity': 10,
                    'batch_code': 'xyz-789',
                }
            ],
            'location': 1,
        }

        n = StockItem.objects.count()

        self.post(
            self.url,
            data,
            expected_code=201,
        )

        # Check that two new stock items have been created!
        self.assertEqual(n + 2, StockItem.objects.count())

        item_1 = StockItem.objects.filter(supplier_part=line_1.part).first()
        item_2 = StockItem.objects.filter(supplier_part=line_2.part).first()

        self.assertEqual(item_1.batch, 'abc-123')
        self.assertEqual(item_2.batch, 'xyz-789')

    def test_serial_numbers(self):
        """
        Test that we can supply a 'serial number' when receiving items
        """

        line_1 = models.PurchaseOrderLineItem.objects.get(pk=1)
        line_2 = models.PurchaseOrderLineItem.objects.get(pk=2)

        self.assertEqual(StockItem.objects.filter(supplier_part=line_1.part).count(), 0)
        self.assertEqual(StockItem.objects.filter(supplier_part=line_2.part).count(), 0)

        data = {
            'items': [
                {
                    'line_item': 1,
                    'quantity': 10,
                    'batch_code': 'abc-123',
                    'serial_numbers': '100+',
                },
                {
                    'line_item': 2,
                    'quantity': 10,
                    'batch_code': 'xyz-789',
                }
            ],
            'location': 1,
        }

        n = StockItem.objects.count()

        self.post(
            self.url,
            data,
            expected_code=201,
        )

        # Check that the expected number of stock items has been created
        self.assertEqual(n + 11, StockItem.objects.count())

        # 10 serialized stock items created for the first line item
        self.assertEqual(StockItem.objects.filter(supplier_part=line_1.part).count(), 10)

        # Check that the correct serial numbers have been allocated
        for i in range(100, 110):
            item = StockItem.objects.get(serial_int=i)
            self.assertEqual(item.serial, str(i))
            self.assertEqual(item.quantity, 1)
            self.assertEqual(item.batch, 'abc-123')

        # A single stock item (quantity 10) created for the second line item
        items = StockItem.objects.filter(supplier_part=line_2.part)
        self.assertEqual(items.count(), 1)

        item = items.first()

        self.assertEqual(item.quantity, 10)
        self.assertEqual(item.batch, 'xyz-789')


class SalesOrderTest(OrderTest):
    """
    Tests for the SalesOrder API
    """

    LIST_URL = reverse('api-so-list')

    def test_so_list(self):

        # All orders
        self.filter({}, 5)

        # Filter by customer
        self.filter({'customer': 4}, 3)
        self.filter({'customer': 5}, 2)

        # Filter by outstanding
        self.filter({'outstanding': True}, 3)
        self.filter({'outstanding': False}, 2)

        # Filter by status
        self.filter({'status': 10}, 3)  # PENDING
        self.filter({'status': 20}, 1)  # SHIPPED
        self.filter({'status': 99}, 0)  # Invalid

    def test_overdue(self):
        """
        Test "overdue" status
        """

        self.filter({'overdue': True}, 0)
        self.filter({'overdue': False}, 5)

        for pk in [1, 2]:
            order = models.SalesOrder.objects.get(pk=pk)
            order.target_date = datetime.now().date() - timedelta(days=10)
            order.save()

        self.filter({'overdue': True}, 2)
        self.filter({'overdue': False}, 3)

    def test_so_detail(self):

        url = '/api/order/so/1/'

        response = self.get(url)

        data = response.data

        self.assertEqual(data['pk'], 1)

    def test_so_attachments(self):

        url = reverse('api-so-attachment-list')

        self.get(url)

    def test_so_operations(self):
        """
        Test that we can create / edit and delete a SalesOrder via the API
        """

        n = models.SalesOrder.objects.count()

        url = reverse('api-so-list')

        # Initially we do not have "add" permission for the SalesOrder model,
        # so this POST request should return 403 (denied)
        response = self.post(
            url,
            {
                'customer': 4,
                'reference': '12345',
                'description': 'Sales order',
            },
            expected_code=403,
        )

        self.assignRole('sales_order.add')

        # Now we should be able to create a SalesOrder via the API
        response = self.post(
            url,
            {
                'customer': 4,
                'reference': '12345',
                'description': 'Sales order',
            },
            expected_code=201
        )

        # Check that the new order has been created
        self.assertEqual(models.SalesOrder.objects.count(), n + 1)

        # Grab the PK for the newly created SalesOrder
        pk = response.data['pk']

        # Try to create a SO with identical reference (should fail)
        response = self.post(
            url,
            {
                'customer': 4,
                'reference': '12345',
                'description': 'Another sales order',
            },
            expected_code=400
        )

        url = reverse('api-so-detail', kwargs={'pk': pk})

        # Extract detail info for the SalesOrder
        response = self.get(url)
        self.assertEqual(response.data['reference'], '12345')

        # Try to alter (edit) the SalesOrder
        response = self.patch(
            url,
            {
                'reference': '12345-a',
            },
            expected_code=200
        )

        # Reference should have changed
        self.assertEqual(response.data['reference'], '12345-a')

        # Now, let's try to delete this SalesOrder
        # Initially, we do not have the required permission
        response = self.delete(url, expected_code=403)

        self.assignRole('sales_order.delete')

        response = self.delete(url, expected_code=204)

        # Check that the number of sales orders has decreased
        self.assertEqual(models.SalesOrder.objects.count(), n)

        # And the resource should no longer be available
        response = self.get(url, expected_code=404)

    def test_so_create(self):
        """
        Test that we can create a new SalesOrder via the API
        """

        self.assignRole('sales_order.add')

        self.post(
            reverse('api-so-list'),
            {
                'reference': '1234566778',
                'customer': 4,
                'description': 'A test sales order',
            },
            expected_code=201
        )

    def test_so_cancel(self):
        """ Test API endpoint for cancelling a SalesOrder """

        so = models.SalesOrder.objects.get(pk=1)

        self.assertEqual(so.status, SalesOrderStatus.PENDING)

        url = reverse('api-so-cancel', kwargs={'pk': so.pk})

        # Try to cancel, without permission
        self.post(url, {}, expected_code=403)

        self.assignRole('sales_order.add')

        self.post(url, {}, expected_code=201)

        so.refresh_from_db()

        self.assertEqual(so.status, SalesOrderStatus.CANCELLED)

    def test_so_metadata(self):
        url = reverse('api-so-metadata', kwargs={'pk': 1})

        self.patch(
            url,
            {
                'metadata': {
                    'xyz': 'abc',
                }
            },
            expected_code=200
        )

        order = models.SalesOrder.objects.get(pk=1)
        self.assertEqual(order.get_metadata('xyz'), 'abc')


class SalesOrderDownloadTest(OrderTest):
    """Unit tests for downloading SalesOrder data via the API endpoint"""

    def test_download_fail(self):
        """Test that downloading without the 'export' option fails"""

        url = reverse('api-so-list')

        with self.assertRaises(ValueError):
            self.download_file(url, {}, expected_code=200)

    def test_download_xls(self):
        url = reverse('api-so-list')

        # Download .xls file
        with self.download_file(
            url,
            {
                'export': 'xls',
            },
            expected_code=200,
            expected_fn='InvenTree_SalesOrders.xls',
            deode=False,
        ) as fo:
            self.assertTrue(isinstance(fo, io.BytesIO))

    def test_download_csv(self):

        url = reverse('api-so-list')

        required_cols = [
            'line_items',
            'id',
            'reference',
            'customer',
            'status',
            'shipment_date',
            'notes',
            'description',
        ]

        excluded_cols = [
            'metadata'
        ]

        # Download .xls file
        with self.download_file(
            url,
            {
                'export': 'csv',
            },
            expected_code=200,
            expected_fn='InvenTree_SalesOrders.csv',
            decode=True
        ) as fo:

            data = self.process_csv(
                fo,
                required_cols=required_cols,
                excluded_cols=excluded_cols,
                required_rows=models.SalesOrder.objects.count()
            )

            for line in data:

                order = models.SalesOrder.objects.get(pk=line['id'])

                self.assertEqual(line['description'], order.description)
                self.assertEqual(line['status'], str(order.status))

        # Download only outstanding sales orders
        with self.download_file(
            url,
            {
                'export': 'tsv',
                'outstanding': True,
            },
            expected_code=200,
            expected_fn='InvenTree_SalesOrders.tsv',
            decode=True,
        ) as fo:

            self.process_csv(
                fo,
                required_cols=required_cols,
                excluded_cols=excluded_cols,
                required_rows=models.SalesOrder.objects.filter(status__in=SalesOrderStatus.OPEN).count(),
                delimiter='\t',
            )


class SalesOrderAllocateTest(OrderTest):
    """
    Unit tests for allocating stock items against a SalesOrder
    """

    def setUp(self):
        super().setUp()

        self.assignRole('sales_order.add')

        self.url = reverse('api-so-allocate', kwargs={'pk': 1})

        self.order = models.SalesOrder.objects.get(pk=1)

        # Create some line items for this purchase order
        parts = Part.objects.filter(salable=True)

        for part in parts:

            # Create a new line item
            models.SalesOrderLineItem.objects.create(
                order=self.order,
                part=part,
                quantity=5,
            )

            # Ensure we have stock!
            StockItem.objects.create(
                part=part,
                quantity=100,
            )

        # Create a new shipment against this SalesOrder
        self.shipment = models.SalesOrderShipment.objects.create(
            order=self.order,
        )

    def test_invalid(self):
        """
        Test POST with invalid data
        """

        # No data
        response = self.post(self.url, {}, expected_code=400)

        self.assertIn('This field is required', str(response.data['items']))
        self.assertIn('This field is required', str(response.data['shipment']))

        # Test with a single line items
        line = self.order.lines.first()
        part = line.part

        # Valid stock_item, but quantity is invalid
        data = {
            'items': [{
                "line_item": line.pk,
                "stock_item": part.stock_items.last().pk,
                "quantity": 0,
            }],
        }

        response = self.post(self.url, data, expected_code=400)

        self.assertIn('Quantity must be positive', str(response.data['items']))

        # Valid stock item, too much quantity
        data['items'][0]['quantity'] = 250

        response = self.post(self.url, data, expected_code=400)

        self.assertIn('Available quantity (100) exceeded', str(response.data['items']))

        # Valid stock item, valid quantity
        data['items'][0]['quantity'] = 50

        # Invalid shipment!
        data['shipment'] = 9999

        response = self.post(self.url, data, expected_code=400)

        self.assertIn('does not exist', str(response.data['shipment']))

        # Valid shipment, but points to the wrong order
        shipment = models.SalesOrderShipment.objects.create(
            order=models.SalesOrder.objects.get(pk=2),
        )

        data['shipment'] = shipment.pk

        response = self.post(self.url, data, expected_code=400)

        self.assertIn('Shipment is not associated with this order', str(response.data['shipment']))

    def test_allocate(self):
        """
        Test the the allocation endpoint acts as expected,
        when provided with valid data!
        """

        # First, check that there are no line items allocated against this SalesOrder
        self.assertEqual(self.order.stock_allocations.count(), 0)

        data = {
            "items": [],
            "shipment": self.shipment.pk,
        }

        for line in self.order.lines.all():
            stock_item = line.part.stock_items.last()

            # Fully-allocate each line
            data['items'].append({
                "line_item": line.pk,
                "stock_item": stock_item.pk,
                "quantity": 5
            })

        self.post(self.url, data, expected_code=201)

        # There should have been 1 stock item allocated against each line item
        n_lines = self.order.lines.count()

        self.assertEqual(self.order.stock_allocations.count(), n_lines)

        for line in self.order.lines.all():
            self.assertEqual(line.allocations.count(), 1)
