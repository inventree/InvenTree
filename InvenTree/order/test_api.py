"""Tests for the Order API."""

import base64
import io
from datetime import datetime, timedelta

from django.core.exceptions import ValidationError
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from djmoney.money import Money
from icalendar import Calendar
from rest_framework import status

from common.settings import currency_codes
from company.models import Company
from InvenTree.status_codes import (PurchaseOrderStatus, ReturnOrderLineStatus,
                                    ReturnOrderStatus, SalesOrderStatus,
                                    SalesOrderStatusGroups, StockStatus)
from InvenTree.unit_test import InvenTreeAPITestCase
from order import models
from part.models import Part
from stock.models import StockItem


class OrderTest(InvenTreeAPITestCase):
    """Base class for order API unit testing"""
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

    def filter(self, filters, count):
        """Test API filters."""
        response = self.get(
            self.LIST_URL,
            filters
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), count)

        return response


class PurchaseOrderTest(OrderTest):
    """Tests for the PurchaseOrder API."""

    LIST_URL = reverse('api-po-list')

    def test_options(self):
        """Test the PurchaseOrder OPTIONS endpoint."""
        self.assignRole('purchase_order.add')

        response = self.options(self.LIST_URL, expected_code=200)

        data = response.data
        self.assertEqual(data['name'], 'Purchase Order List')

        post = data['actions']['POST']

        def check_options(data, field_name, spec):
            """Helper function to check that the options are configured correctly."""
            field_data = data[field_name]

            for k, v in spec.items():
                self.assertIn(k, field_data)
                self.assertEqual(field_data[k], v)

        # Checks for the 'order_currency' field
        check_options(post, 'order_currency', {
            'type': 'choice',
            'required': False,
            'read_only': False,
            'label': 'Order Currency',
            'help_text': 'Currency for this order (leave blank to use company default)',
        })

        # Checks for the 'reference' field
        check_options(post, 'reference', {
            'type': 'string',
            'required': True,
            'read_only': False,
            'label': 'Reference',
        })

        # Checks for the 'supplier' field
        check_options(post, 'supplier', {
            'type': 'related field',
            'required': True,
            'api_url': '/api/company/',
        })

    def test_po_list(self):
        """Test the PurchaseOrder list API endpoint"""
        # List *ALL* PurchaseOrder items
        self.filter({}, 7)

        # Filter by assigned-to-me
        self.filter({'assigned_to_me': 1}, 0)
        self.filter({'assigned_to_me': 0}, 7)

        # Filter by supplier
        self.filter({'supplier': 1}, 1)
        self.filter({'supplier': 3}, 5)

        # Filter by "outstanding"
        self.filter({'outstanding': True}, 5)
        self.filter({'outstanding': False}, 2)

        # Filter by "status"
        self.filter({'status': 10}, 3)
        self.filter({'status': 40}, 1)

        # Filter by "reference"
        self.filter({'reference': 'PO-0001'}, 1)
        self.filter({'reference': 'PO-9999'}, 0)

        # Filter by "assigned_to_me"
        self.filter({'assigned_to_me': 1}, 0)
        self.filter({'assigned_to_me': 0}, 7)

        # Filter by "part"
        self.filter({'part': 1}, 2)
        self.filter({'part': 2}, 0)  # Part not assigned to any PO

        # Filter by "supplier_part"
        self.filter({'supplier_part': 1}, 1)
        self.filter({'supplier_part': 3}, 2)
        self.filter({'supplier_part': 4}, 0)

    def test_total_price(self):
        """Unit tests for the 'total_price' field"""
        # Ensure we have exchange rate data
        self.generate_exchange_rates()

        currencies = currency_codes()
        n = len(currencies)

        idx = 0

        new_orders = []

        # Let's generate some more orders
        for supplier in Company.objects.filter(is_supplier=True):
            for _idx in range(10):
                new_orders.append(
                    models.PurchaseOrder(
                        supplier=supplier,
                        reference=f'PO-{idx + 100}'
                    )
                )

                idx += 1

        models.PurchaseOrder.objects.bulk_create(new_orders)

        idx = 0

        # Create some purchase order line items
        lines = []

        for po in models.PurchaseOrder.objects.all():
            for sp in po.supplier.supplied_parts.all():
                lines.append(
                    models.PurchaseOrderLineItem(
                        order=po,
                        part=sp,
                        quantity=idx + 1,
                        purchase_price=Money((idx + 1) / 10, currencies[idx % n]),
                    )
                )

                idx += 1

        models.PurchaseOrderLineItem.objects.bulk_create(lines)

        # List all purchase orders
        for limit in [1, 5, 10, 100]:
            with CaptureQueriesContext(connection) as ctx:
                response = self.get(self.LIST_URL, data={'limit': limit}, expected_code=200)

                # Total database queries must be below 15, independent of the number of results
                self.assertLess(len(ctx), 15)

                for result in response.data['results']:
                    self.assertIn('total_price', result)
                    self.assertIn('order_currency', result)

    def test_overdue(self):
        """Test "overdue" status."""
        self.filter({'overdue': True}, 0)
        self.filter({'overdue': False}, 7)

        order = models.PurchaseOrder.objects.get(pk=1)
        order.target_date = datetime.now().date() - timedelta(days=10)
        order.save()

        self.filter({'overdue': True}, 1)
        self.filter({'overdue': False}, 6)

    def test_po_detail(self):
        """Test the PurchaseOrder detail API endpoint"""
        url = '/api/order/po/1/'

        response = self.get(url)

        self.assertEqual(response.status_code, 200)

        data = response.data

        self.assertEqual(data['pk'], 1)
        self.assertEqual(data['description'], 'Ordering some screws')

    def test_po_reference(self):
        """Test that a reference with a too big / small reference is handled correctly."""
        # get permissions
        self.assignRole('purchase_order.add')

        url = reverse('api-po-list')
        huge_number = "PO-92233720368547758089999999999999999"

        response = self.post(
            url,
            {
                'supplier': 1,
                'reference': huge_number,
                'description': 'PO created via the API',
            },
            expected_code=201,
        )

        order = models.PurchaseOrder.objects.get(pk=response.data['pk'])

        self.assertEqual(order.reference, 'PO-92233720368547758089999999999999999')
        self.assertEqual(order.reference_int, 0x7fffffff)

    def test_po_attachments(self):
        """Test the list endpoint for the PurchaseOrderAttachment model"""
        url = reverse('api-po-attachment-list')

        response = self.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_po_operations(self):
        """Test that we can create / edit and delete a PurchaseOrder via the API."""
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
                'reference': 'PO-123456789',
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
        self.assertEqual(response.data['reference'], 'PO-123456789')

        # Try to alter (edit) the PurchaseOrder
        response = self.patch(
            url,
            {
                'reference': 'PO-12345',
            },
            expected_code=200
        )

        # Reference should have changed
        self.assertEqual(response.data['reference'], 'PO-12345')

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
        """Test that we can create a new PurchaseOrder via the API."""
        self.assignRole('purchase_order.add')

        self.post(
            reverse('api-po-list'),
            {
                'reference': 'PO-12345678',
                'supplier': 1,
                'description': 'A test purchase order',
            },
            expected_code=201
        )

    def test_po_duplicate(self):
        """Test that we can duplicate a PurchaseOrder via the API"""
        self.assignRole('purchase_order.add')

        po = models.PurchaseOrder.objects.get(pk=1)

        self.assertTrue(po.lines.count() > 0)

        lines = []

        # Add some extra line items to this order
        for idx in range(5):
            lines.append(models.PurchaseOrderExtraLine(
                order=po,
                quantity=idx + 10,
                reference='some reference',
            ))

        # bulk create orders
        models.PurchaseOrderExtraLine.objects.bulk_create(lines)

        data = self.get(reverse('api-po-detail', kwargs={'pk': 1})).data

        del data['pk']
        del data['reference']

        # Duplicate with non-existent PK to provoke error
        data['duplicate_order'] = 10000001
        data['duplicate_line_items'] = True
        data['duplicate_extra_lines'] = False

        data['reference'] = 'PO-9999'

        # Duplicate via the API
        response = self.post(
            reverse('api-po-list'),
            data,
            expected_code=400
        )

        data['duplicate_order'] = 1
        data['duplicate_line_items'] = True
        data['duplicate_extra_lines'] = False

        data['reference'] = 'PO-9999'

        # Duplicate via the API
        response = self.post(
            reverse('api-po-list'),
            data,
            expected_code=201
        )

        # Order is for the same supplier
        self.assertEqual(response.data['supplier'], po.supplier.pk)

        po_dup = models.PurchaseOrder.objects.get(pk=response.data['pk'])

        self.assertEqual(po_dup.extra_lines.count(), 0)
        self.assertEqual(po_dup.lines.count(), po.lines.count())

        data['reference'] = 'PO-9998'
        data['duplicate_line_items'] = False
        data['duplicate_extra_lines'] = True

        response = self.post(
            reverse('api-po-list'),
            data,
            expected_code=201,
        )

        po_dup = models.PurchaseOrder.objects.get(pk=response.data['pk'])

        self.assertEqual(po_dup.extra_lines.count(), po.extra_lines.count())
        self.assertEqual(po_dup.lines.count(), 0)

    def test_po_cancel(self):
        """Test the PurchaseOrderCancel API endpoint."""
        po = models.PurchaseOrder.objects.get(pk=1)

        self.assertEqual(po.status, PurchaseOrderStatus.PENDING)

        url = reverse('api-po-cancel', kwargs={'pk': po.pk})

        # Try to cancel the PO, but without required permissions
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
        """Test the PurchaseOrderComplete API endpoint."""
        po = models.PurchaseOrder.objects.get(pk=3)

        url = reverse('api-po-complete', kwargs={'pk': po.pk})

        self.assertEqual(po.status, PurchaseOrderStatus.PLACED)

        # Try to complete the PO, without required permissions
        self.post(url, {}, expected_code=403)

        self.assignRole('purchase_order.add')

        # Should fail due to incomplete lines
        response = self.post(url, {}, expected_code=400)

        self.assertIn('Order has incomplete line items', str(response.data['accept_incomplete']))

        # Post again, accepting incomplete line items
        self.post(
            url,
            {
                'accept_incomplete': True,
            },
            expected_code=201
        )

        po.refresh_from_db()

        self.assertEqual(po.status, PurchaseOrderStatus.COMPLETE)

    def test_po_issue(self):
        """Test the PurchaseOrderIssue API endpoint."""
        po = models.PurchaseOrder.objects.get(pk=2)

        url = reverse('api-po-issue', kwargs={'pk': po.pk})

        # Try to issue the PO, without required permissions
        self.post(url, {}, expected_code=403)

        self.assignRole('purchase_order.add')

        self.post(url, {}, expected_code=201)

        po.refresh_from_db()

        self.assertEqual(po.status, PurchaseOrderStatus.PLACED)

    def test_po_calendar(self):
        """Test the calendar export endpoint"""
        # Create required purchase orders
        self.assignRole('purchase_order.add')

        for i in range(1, 9):
            self.post(
                reverse('api-po-list'),
                {
                    'reference': f'PO-1100000{i}',
                    'supplier': 1,
                    'description': f'Calendar PO {i}',
                    'target_date': f'2024-12-{i:02d}',
                },
                expected_code=201
            )

        # Get some of these orders with target date, complete or cancel them
        for po in models.PurchaseOrder.objects.filter(target_date__isnull=False):
            if po.reference in ['PO-11000001', 'PO-11000002', 'PO-11000003', 'PO-11000004']:
                # Set issued status for these POs
                self.post(
                    reverse('api-po-issue', kwargs={'pk': po.pk}),
                    {},
                    expected_code=201
                )

                if po.reference in ['PO-11000001', 'PO-11000002']:
                    # Set complete status for these POs
                    self.post(
                        reverse('api-po-complete', kwargs={'pk': po.pk}),
                        {
                            'accept_incomplete': True,
                        },
                        expected_code=201
                    )

            elif po.reference in ['PO-11000005', 'PO-11000006']:
                # Set cancel status for these POs
                self.post(
                    reverse('api-po-cancel', kwargs={'pk': po.pk}),
                    {
                        'accept_incomplete': True,
                    },
                    expected_code=201
                )

        url = reverse('api-po-so-calendar', kwargs={'ordertype': 'purchase-order'})

        # Test without completed orders
        response = self.get(url, expected_code=200, format=None)

        number_orders = len(models.PurchaseOrder.objects.filter(target_date__isnull=False).filter(status__lt=PurchaseOrderStatus.COMPLETE.value))

        # Transform content to a Calendar object
        calendar = Calendar.from_ical(response.content)
        n_events = 0
        # Count number of events in calendar
        for component in calendar.walk():
            if component.name == 'VEVENT':
                n_events += 1

        self.assertGreaterEqual(n_events, 1)
        self.assertEqual(number_orders, n_events)

        # Test with completed orders
        response = self.get(url, data={'include_completed': 'True'}, expected_code=200, format=None)

        number_orders_incl_completed = len(models.PurchaseOrder.objects.filter(target_date__isnull=False))

        self.assertGreater(number_orders_incl_completed, number_orders)

        # Transform content to a Calendar object
        calendar = Calendar.from_ical(response.content)
        n_events = 0
        # Count number of events in calendar
        for component in calendar.walk():
            if component.name == 'VEVENT':
                n_events += 1

        self.assertGreaterEqual(n_events, 1)
        self.assertEqual(number_orders_incl_completed, n_events)

    def test_po_calendar_noauth(self):
        """Test accessing calendar without authorization"""
        self.client.logout()
        response = self.client.get(reverse('api-po-so-calendar', kwargs={'ordertype': 'purchase-order'}), format='json')

        self.assertEqual(response.status_code, 401)

        resp_dict = response.json()
        self.assertEqual(resp_dict['detail'], "Authentication credentials were not provided.")

    def test_po_calendar_auth(self):
        """Test accessing calendar with header authorization"""
        self.client.logout()
        base64_token = base64.b64encode(f'{self.username}:{self.password}'.encode('ascii')).decode('ascii')
        response = self.client.get(
            reverse('api-po-so-calendar', kwargs={'ordertype': 'purchase-order'}),
            format='json',
            headers={"authorization": f'basic {base64_token}'}
        )
        self.assertEqual(response.status_code, 200)


class PurchaseOrderLineItemTest(OrderTest):
    """Unit tests for PurchaseOrderLineItems."""

    LIST_URL = reverse('api-po-line-list')

    def test_po_line_list(self):
        """Test the PurchaseOrderLine list API endpoint"""
        # List *ALL* PurchaseOrderLine items
        self.filter({}, 5)

        # Filter by pending status
        self.filter({'pending': 1}, 5)
        self.filter({'pending': 0}, 0)

        # Filter by received status
        self.filter({'received': 1}, 0)
        self.filter({'received': 0}, 5)

        # Filter by has_pricing status
        self.filter({'has_pricing': 1}, 0)
        self.filter({'has_pricing': 0}, 5)

    def test_po_line_bulk_delete(self):
        """Test that we can bulk delete multiple PurchaseOrderLineItems via the API."""
        n = models.PurchaseOrderLineItem.objects.count()

        self.assignRole('purchase_order.delete')

        url = reverse('api-po-line-list')

        # Try to delete a set of line items via their IDs
        self.delete(
            url,
            {
                'items': [1, 2],
            },
            expected_code=204,
        )

        # We should have 2 less PurchaseOrderLineItems after deletign them
        self.assertEqual(models.PurchaseOrderLineItem.objects.count(), n - 2)


class PurchaseOrderDownloadTest(OrderTest):
    """Unit tests for downloading PurchaseOrder data via the API endpoint."""

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
        """Incorrect format should default raise an error."""
        url = reverse('api-po-list')

        with self.assertRaises(ValueError):
            self.download_file(
                url,
                {
                    'export': 'xyz',
                }
            )

    def test_download_csv(self):
        """Download PurchaseOrder data as .csv."""
        with self.download_file(
            reverse('api-po-list'),
            {
                'export': 'csv',
            },
            expected_code=200,
            expected_fn='InvenTree_PurchaseOrders.csv',
        ) as file:

            data = self.process_csv(
                file,
                required_cols=self.required_cols,
                excluded_cols=self.excluded_cols,
                required_rows=models.PurchaseOrder.objects.count()
            )

            for row in data:
                order = models.PurchaseOrder.objects.get(pk=row['id'])

                self.assertEqual(order.description, row['description'])
                self.assertEqual(order.reference, row['reference'])

    def test_download_line_items(self):
        """Test that the PurchaseOrderLineItems can be downloaded to a file"""
        with self.download_file(
            reverse('api-po-line-list'),
            {
                'export': 'xlsx',
            },
            decode=False,
            expected_code=200,
            expected_fn='InvenTree_PurchaseOrderItems.xlsx',
        ) as file:

            self.assertTrue(isinstance(file, io.BytesIO))


class PurchaseOrderReceiveTest(OrderTest):
    """Unit tests for receiving items against a PurchaseOrder."""

    def setUp(self):
        """Init routines for this unit test class"""
        super().setUp()

        self.assignRole('purchase_order.add')

        self.url = reverse('api-po-receive', kwargs={'pk': 1})

        # Number of stock items which exist at the start of each test
        self.n = StockItem.objects.count()

        # Mark the order as "placed" so we can receive line items
        order = models.PurchaseOrder.objects.get(pk=1)
        order.status = PurchaseOrderStatus.PLACED.value
        order.save()

    def test_empty(self):
        """Test without any POST data."""
        data = self.post(self.url, {}, expected_code=400).data

        self.assertIn('This field is required', str(data['items']))
        self.assertIn('This field is required', str(data['location']))

        # No new stock items have been created
        self.assertEqual(self.n, StockItem.objects.count())

    def test_no_items(self):
        """Test with an empty list of items."""
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
        """Test than errors are returned as expected for invalid data."""
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
        """Test with an invalid StockStatus value."""
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
        """Test for supplier parts which *do* exist but do not match the order supplier."""
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
        """Test than a "null" barcode field can be provided."""
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
        """Tests for checking in items with invalid barcodes:

        - Cannot check in "duplicate" barcodes
        - Barcodes cannot match 'barcode_hash' field for existing StockItem
        """
        # Set stock item barcode
        item = StockItem.objects.get(pk=1)
        item.assign_barcode(barcode_data='MY-BARCODE-HASH')

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
        """Test receipt of valid data."""
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
        order.status = PurchaseOrderStatus.PENDING.value
        order.save()

        response = self.post(
            self.url,
            valid_data,
            expected_code=400
        )

        self.assertIn('can only be received against', str(response.data))

        # Now, set the PurchaseOrder back to "PLACED" so the items can be received
        order.status = PurchaseOrderStatus.PLACED.value
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

        # Same location for each received item, as overall 'location' field is provided
        self.assertEqual(stock_1.last().location.pk, 1)
        self.assertEqual(stock_2.last().location.pk, 1)

        # Barcodes should have been assigned to the stock items
        self.assertTrue(StockItem.objects.filter(barcode_data='MY-UNIQUE-BARCODE-123').exists())
        self.assertTrue(StockItem.objects.filter(barcode_data='MY-UNIQUE-BARCODE-456').exists())

    def test_batch_code(self):
        """Test that we can supply a 'batch code' when receiving items."""
        line_1 = models.PurchaseOrderLineItem.objects.get(pk=1)
        line_2 = models.PurchaseOrderLineItem.objects.get(pk=2)

        self.assertEqual(StockItem.objects.filter(supplier_part=line_1.part).count(), 0)
        self.assertEqual(StockItem.objects.filter(supplier_part=line_2.part).count(), 0)

        data = {
            'items': [
                {
                    'line_item': 1,
                    'quantity': 10,
                    'batch_code': 'B-abc-123',
                },
                {
                    'line_item': 2,
                    'quantity': 10,
                    'batch_code': 'B-xyz-789',
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

        self.assertEqual(item_1.batch, 'B-abc-123')
        self.assertEqual(item_2.batch, 'B-xyz-789')

    def test_serial_numbers(self):
        """Test that we can supply a 'serial number' when receiving items."""
        line_1 = models.PurchaseOrderLineItem.objects.get(pk=1)
        line_2 = models.PurchaseOrderLineItem.objects.get(pk=2)

        self.assertEqual(StockItem.objects.filter(supplier_part=line_1.part).count(), 0)
        self.assertEqual(StockItem.objects.filter(supplier_part=line_2.part).count(), 0)

        data = {
            'items': [
                {
                    'line_item': 1,
                    'quantity': 10,
                    'batch_code': 'B-abc-123',
                    'serial_numbers': '100+',
                },
                {
                    'line_item': 2,
                    'quantity': 10,
                    'batch_code': 'B-xyz-789',
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
            self.assertEqual(item.batch, 'B-abc-123')

        # A single stock item (quantity 10) created for the second line item
        items = StockItem.objects.filter(supplier_part=line_2.part)
        self.assertEqual(items.count(), 1)

        item = items.first()

        self.assertEqual(item.quantity, 10)
        self.assertEqual(item.batch, 'B-xyz-789')


class SalesOrderTest(OrderTest):
    """Tests for the SalesOrder API."""

    LIST_URL = reverse('api-so-list')

    def test_so_list(self):
        """Test the SalesOrder list API endpoint"""
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

        # Filter by "reference"
        self.filter({'reference': 'ABC123'}, 1)
        self.filter({'reference': 'XXX999'}, 0)

        # Filter by "assigned_to_me"
        self.filter({'assigned_to_me': 1}, 0)
        self.filter({'assigned_to_me': 0}, 5)

    def test_total_price(self):
        """Unit tests for the 'total_price' field"""
        # Ensure we have exchange rate data
        self.generate_exchange_rates()

        currencies = currency_codes()
        n = len(currencies)

        idx = 0
        new_orders = []

        # Generate some new SalesOrders
        for customer in Company.objects.filter(is_customer=True):
            for _idx in range(10):
                new_orders.append(
                    models.SalesOrder(
                        customer=customer,
                        reference=f'SO-{idx + 100}',
                    )
                )

                idx += 1

        models.SalesOrder.objects.bulk_create(new_orders)

        idx = 0

        # Create some new SalesOrderLineItem objects

        lines = []
        extra_lines = []

        for so in models.SalesOrder.objects.all():
            for p in Part.objects.filter(salable=True):
                lines.append(
                    models.SalesOrderLineItem(
                        order=so,
                        part=p,
                        quantity=idx + 1,
                        sale_price=Money((idx + 1) / 5, currencies[idx % n])
                    )
                )

                idx += 1

            # Create some extra lines against this order
            for _ in range(3):
                extra_lines.append(
                    models.SalesOrderExtraLine(
                        order=so,
                        quantity=(idx + 2) % 10,
                        price=Money(10, 'CAD'),
                    )
                )

        models.SalesOrderLineItem.objects.bulk_create(lines)
        models.SalesOrderExtraLine.objects.bulk_create(extra_lines)

        # List all SalesOrder objects and count queries
        for limit in [1, 5, 10, 100]:
            with CaptureQueriesContext(connection) as ctx:
                response = self.get(self.LIST_URL, data={'limit': limit}, expected_code=200)

                # Total database queries must be less than 15
                self.assertLess(len(ctx), 15)

                n = len(response.data['results'])

                for result in response.data['results']:
                    self.assertIn('total_price', result)
                    self.assertIn('order_currency', result)

    def test_overdue(self):
        """Test "overdue" status."""
        self.filter({'overdue': True}, 0)
        self.filter({'overdue': False}, 5)

        for pk in [1, 2]:
            order = models.SalesOrder.objects.get(pk=pk)
            order.target_date = datetime.now().date() - timedelta(days=10)
            order.save()

        self.filter({'overdue': True}, 2)
        self.filter({'overdue': False}, 3)

    def test_so_detail(self):
        """Test the SalesOrder detail endpoint"""
        url = '/api/order/so/1/'

        response = self.get(url)

        data = response.data

        self.assertEqual(data['pk'], 1)

    def test_so_attachments(self):
        """Test the list endpoint for the SalesOrderAttachment model"""
        url = reverse('api-so-attachment-list')

        self.get(url)

    def test_so_operations(self):
        """Test that we can create / edit and delete a SalesOrder via the API."""
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
                'reference': 'SO-12345',
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
                'reference': 'SO-12345',
                'description': 'Another sales order',
            },
            expected_code=400
        )

        url = reverse('api-so-detail', kwargs={'pk': pk})

        # Extract detail info for the SalesOrder
        response = self.get(url)
        self.assertEqual(response.data['reference'], 'SO-12345')

        # Try to alter (edit) the SalesOrder
        # Initially try with an invalid reference field value
        response = self.patch(
            url,
            {
                'reference': 'SO-12345-a',
            },
            expected_code=400
        )

        response = self.patch(
            url,
            {
                'reference': 'SO-12346',
            },
            expected_code=200
        )

        # Reference should have changed
        self.assertEqual(response.data['reference'], 'SO-12346')

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
        """Test that we can create a new SalesOrder via the API."""
        self.assignRole('sales_order.add')

        url = reverse('api-so-list')

        # Will fail due to invalid reference field
        response = self.post(
            url,
            {
                'reference': '1234566778',
                'customer': 4,
                'description': 'A test sales order',
            },
            expected_code=400,
        )

        self.assertIn('Reference must match required pattern', str(response.data['reference']))

        self.post(
            url,
            {
                'reference': 'SO-12345',
                'customer': 4,
                'description': 'A better test sales order',
            },
            expected_code=201,
        )

    def test_so_cancel(self):
        """Test API endpoint for cancelling a SalesOrder."""
        so = models.SalesOrder.objects.get(pk=1)

        self.assertEqual(so.status, SalesOrderStatus.PENDING)

        url = reverse('api-so-cancel', kwargs={'pk': so.pk})

        # Try to cancel, without permission
        self.post(url, {}, expected_code=403)

        self.assignRole('sales_order.add')

        self.post(url, {}, expected_code=201)

        so.refresh_from_db()

        self.assertEqual(so.status, SalesOrderStatus.CANCELLED)

    def test_so_calendar(self):
        """Test the calendar export endpoint"""
        # Create required sales orders
        self.assignRole('sales_order.add')

        for i in range(1, 9):
            self.post(
                reverse('api-so-list'),
                {
                    'reference': f'SO-1100000{i}',
                    'customer': 4,
                    'description': f'Calendar SO {i}',
                    'target_date': f'2024-12-{i:02d}',
                },
                expected_code=201
            )

        # Cancel a few orders - these will not show in incomplete view below
        for so in models.SalesOrder.objects.filter(target_date__isnull=False):
            if so.reference in ['SO-11000006', 'SO-11000007', 'SO-11000008', 'SO-11000009']:
                self.post(
                    reverse('api-so-cancel', kwargs={'pk': so.pk}),
                    expected_code=201
                )

        url = reverse('api-po-so-calendar', kwargs={'ordertype': 'sales-order'})

        # Test without completed orders
        response = self.get(url, expected_code=200, format=None)

        number_orders = len(models.SalesOrder.objects.filter(target_date__isnull=False).filter(status__lt=SalesOrderStatus.SHIPPED.value))

        # Transform content to a Calendar object
        calendar = Calendar.from_ical(response.content)
        n_events = 0
        # Count number of events in calendar
        for component in calendar.walk():
            if component.name == 'VEVENT':
                n_events += 1

        self.assertGreaterEqual(n_events, 1)
        self.assertEqual(number_orders, n_events)

        # Test with completed orders
        response = self.get(url, data={'include_completed': 'True'}, expected_code=200, format=None)

        number_orders_incl_complete = len(models.SalesOrder.objects.filter(target_date__isnull=False))
        self.assertGreater(number_orders_incl_complete, number_orders)

        # Transform content to a Calendar object
        calendar = Calendar.from_ical(response.content)
        n_events = 0
        # Count number of events in calendar
        for component in calendar.walk():
            if component.name == 'VEVENT':
                n_events += 1

        self.assertGreaterEqual(n_events, 1)
        self.assertEqual(number_orders_incl_complete, n_events)

    def test_export(self):
        """Test we can export the SalesOrder list"""
        n = models.SalesOrder.objects.count()

        # Check there are some sales orders
        self.assertGreater(n, 0)

        for order in models.SalesOrder.objects.all():
            # Reconstruct the total price
            order.save()

        # Download file, check we get a 200 response
        for fmt in ['csv', 'xls', 'xlsx']:
            self.download_file(
                reverse('api-so-list'),
                {'export': fmt},
                decode=True if fmt == 'csv' else False,
                expected_code=200,
                expected_fn=f"InvenTree_SalesOrders.{fmt}"
            )


class SalesOrderLineItemTest(OrderTest):
    """Tests for the SalesOrderLineItem API."""

    LIST_URL = reverse('api-so-line-list')

    @classmethod
    def setUpTestData(cls):
        """Init routine for this unit test class"""
        super().setUpTestData()

        # List of salable parts
        parts = Part.objects.filter(salable=True)

        lines = []

        # Create a bunch of SalesOrderLineItems for each order
        for idx, so in enumerate(models.SalesOrder.objects.all()):

            for part in parts:
                lines.append(
                    models.SalesOrderLineItem(
                        order=so,
                        part=part,
                        quantity=(idx + 1) * 5,
                        reference=f"Order {so.reference} - line {idx}",
                    )
                )

        # Bulk create
        models.SalesOrderLineItem.objects.bulk_create(lines)

        cls.url = reverse('api-so-line-list')

    def test_so_line_list(self):
        """Test list endpoint"""
        response = self.get(
            self.url,
            {},
            expected_code=200,
        )

        n = models.SalesOrderLineItem.objects.count()

        # We should have received *all* lines
        self.assertEqual(len(response.data), n)

        # List *all* lines, but paginate
        response = self.get(
            self.url,
            {
                "limit": 5,
            },
            expected_code=200,
        )

        self.assertEqual(response.data['count'], n)
        self.assertEqual(len(response.data['results']), 5)

        n_orders = models.SalesOrder.objects.count()
        n_parts = Part.objects.filter(salable=True).count()

        # List by part
        for part in Part.objects.filter(salable=True)[:3]:
            response = self.get(
                self.url,
                {
                    'part': part.pk,
                    'limit': 10,
                }
            )

            self.assertEqual(response.data['count'], n_orders)

        # List by order
        for order in models.SalesOrder.objects.all()[:3]:
            response = self.get(
                self.url,
                {
                    'order': order.pk,
                    'limit': 10,
                }
            )

            self.assertEqual(response.data['count'], n_parts)

        # Filter by has_pricing status
        self.filter({'has_pricing': 1}, 0)
        self.filter({'has_pricing': 0}, n)

        # Filter by has_pricing status
        self.filter({'completed': 1}, 0)
        self.filter({'completed': 0}, n)


class SalesOrderDownloadTest(OrderTest):
    """Unit tests for downloading SalesOrder data via the API endpoint."""

    def test_download_fail(self):
        """Test that downloading without the 'export' option fails."""
        url = reverse('api-so-list')

        with self.assertRaises(ValueError):
            self.download_file(url, {}, expected_code=200)

    def test_download_xls(self):
        """Test xls file download"""
        url = reverse('api-so-list')

        # Download .xls file
        with self.download_file(
            url,
            {
                'export': 'xls',
            },
            expected_code=200,
            expected_fn='InvenTree_SalesOrders.xls',
            decode=False,
        ) as file:
            self.assertTrue(isinstance(file, io.BytesIO))

    def test_download_csv(self):
        """Test that the list of sales orders can be downloaded as a .csv file"""
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
        ) as file:

            data = self.process_csv(
                file,
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
        ) as file:

            self.process_csv(
                file,
                required_cols=required_cols,
                excluded_cols=excluded_cols,
                required_rows=models.SalesOrder.objects.filter(status__in=SalesOrderStatusGroups.OPEN).count(),
                delimiter='\t',
            )


class SalesOrderAllocateTest(OrderTest):
    """Unit tests for allocating stock items against a SalesOrder."""

    def setUp(self):
        """Init routines for this unit testing class"""
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
        """Test POST with invalid data."""
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
        """Test that the allocation endpoint acts as expected, when provided with valid data!"""
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

    def test_allocate_variant(self):
        """Test that the allocation endpoint acts as expected, when provided with variant"""
        # First, check that there are no line items allocated against this SalesOrder
        self.assertEqual(self.order.stock_allocations.count(), 0)

        data = {
            "items": [],
            "shipment": self.shipment.pk,
        }

        def check_template(line_item):
            return line_item.part.is_template

        for line in filter(check_template, self.order.lines.all()):

            stock_item = None

            # Allocate a matching variant
            parts = Part.objects.filter(salable=True).filter(variant_of=line.part.pk)
            for part in parts:
                stock_item = part.stock_items.last()
                break

            # Fully-allocate each line
            data['items'].append({
                "line_item": line.pk,
                "stock_item": stock_item.pk,
                "quantity": 5
            })

        self.post(self.url, data, expected_code=201)

        # At least one item should be allocated, and all should be variants
        self.assertGreater(self.order.stock_allocations.count(), 0)
        for allocation in self.order.stock_allocations.all():
            self.assertNotEquals(allocation.item.part.pk, allocation.line.part.pk)

    def test_shipment_complete(self):
        """Test that we can complete a shipment via the API."""
        url = reverse('api-so-shipment-ship', kwargs={'pk': self.shipment.pk})

        self.assertFalse(self.shipment.is_complete())
        self.assertFalse(self.shipment.check_can_complete(raise_error=False))

        with self.assertRaises(ValidationError):
            self.shipment.check_can_complete()

        # Attempting to complete this shipment via the API should fail
        response = self.post(
            url, {},
            expected_code=400
        )

        self.assertIn('Shipment has no allocated stock items', str(response.data))

        # Allocate stock against this shipment
        line = self.order.lines.first()
        part = line.part

        models.SalesOrderAllocation.objects.create(
            shipment=self.shipment,
            line=line,
            item=part.stock_items.last(),
            quantity=5
        )

        # Shipment should now be able to be completed
        self.assertTrue(self.shipment.check_can_complete())

        # Attempt with an invalid date
        response = self.post(
            url,
            {
                'shipment_date': 'asfasd',
            },
            expected_code=400,
        )

        self.assertIn('Date has wrong format', str(response.data))

        response = self.post(
            url,
            {
                'invoice_number': 'INV01234',
                'link': 'http://test.com/link.html',
                'tracking_number': 'TRK12345',
                'shipment_date': '2020-12-05',
                'delivery_date': '2023-12-05',
            },
            expected_code=201,
        )

        self.shipment.refresh_from_db()

        self.assertTrue(self.shipment.is_complete())
        self.assertEqual(self.shipment.tracking_number, 'TRK12345')
        self.assertEqual(self.shipment.invoice_number, 'INV01234')
        self.assertEqual(self.shipment.link, 'http://test.com/link.html')
        self.assertEqual(self.shipment.delivery_date, datetime(2023, 12, 5).date())
        self.assertTrue(self.shipment.is_delivered())

    def test_shipment_delivery_date(self):
        """Test delivery date functions via API."""
        url = reverse('api-so-shipment-detail', kwargs={'pk': self.shipment.pk})

        # Attempt remove delivery_date from shipment
        response = self.patch(
            url,
            {
                'delivery_date': None,
            },
            expected_code=200,
        )

        # Shipment should not be marked as delivered
        self.assertFalse(self.shipment.is_delivered())

        # Attempt to set delivery date
        response = self.patch(
            url,
            {
                'delivery_date': 'asfasd',
            },
            expected_code=400,
        )

        self.assertIn('Date has wrong format', str(response.data))

        response = self.patch(
            url,
            {
                'delivery_date': '2023-05-15',
            },
            expected_code=200,
        )
        self.shipment.refresh_from_db()

        # Shipment should now be marked as delivered
        self.assertTrue(self.shipment.is_delivered())
        self.assertEqual(self.shipment.delivery_date, datetime(2023, 5, 15).date())

    def test_sales_order_shipment_list(self):
        """Test the SalesOrderShipment list API endpoint"""
        url = reverse('api-so-shipment-list')

        # Count before creation
        count_before = models.SalesOrderShipment.objects.count()

        # Create some new shipments via the API
        for order in models.SalesOrder.objects.all():

            for idx in range(3):
                self.post(
                    url,
                    {
                        'order': order.pk,
                        'reference': f"SH{idx + 1}",
                        'tracking_number': f"TRK_{order.pk}_{idx}"
                    },
                    expected_code=201
                )

            # Filter API by order
            response = self.get(
                url,
                {
                    'order': order.pk,
                },
                expected_code=200,
            )

            # 3 shipments returned for each SalesOrder instance
            self.assertGreaterEqual(len(response.data), 3)

        # List *all* shipments
        response = self.get(url, expected_code=200)

        self.assertEqual(len(response.data), count_before + 3 * models.SalesOrder.objects.count())


class ReturnOrderTests(InvenTreeAPITestCase):
    """Unit tests for ReturnOrder API endpoints"""

    fixtures = [
        'category',
        'company',
        'return_order',
        'part',
        'location',
        'supplier_part',
        'stock',
    ]

    def test_options(self):
        """Test the OPTIONS endpoint"""
        self.assignRole('return_order.add')
        data = self.options(reverse('api-return-order-list'), expected_code=200).data

        self.assertEqual(data['name'], 'Return Order List')

        # Some checks on the 'reference' field
        post = data['actions']['POST']
        reference = post['reference']

        self.assertEqual(reference['default'], 'RMA-0007')
        self.assertEqual(reference['label'], 'Reference')
        self.assertEqual(reference['help_text'], 'Return Order reference')
        self.assertEqual(reference['required'], True)
        self.assertEqual(reference['type'], 'string')

    def test_list(self):
        """Tests for the list endpoint"""
        url = reverse('api-return-order-list')

        response = self.get(url, expected_code=200)

        self.assertEqual(len(response.data), 6)

        # Paginated query
        data = self.get(
            url,
            {
                'limit': 1,
                'ordering': 'reference',
                'customer_detail': True,
            },
            expected_code=200
        ).data

        self.assertEqual(data['count'], 6)
        self.assertEqual(len(data['results']), 1)
        result = data['results'][0]
        self.assertEqual(result['reference'], 'RMA-001')
        self.assertEqual(result['customer_detail']['name'], 'A customer')

        # Reverse ordering
        data = self.get(
            url,
            {
                'ordering': '-reference',
            },
            expected_code=200
        ).data

        self.assertEqual(data[0]['reference'], 'RMA-006')

        # Filter by customer
        for cmp_id in [4, 5]:
            data = self.get(
                url,
                {
                    'customer': cmp_id,
                },
                expected_code=200
            ).data

            self.assertEqual(len(data), 3)

            for result in data:
                self.assertEqual(result['customer'], cmp_id)

        # Filter by status
        data = self.get(
            url,
            {
                'status': 20,
            },
            expected_code=200
        ).data

        self.assertEqual(len(data), 2)

        for result in data:
            self.assertEqual(result['status'], 20)

    def test_create(self):
        """Test creation of ReturnOrder via the API"""
        url = reverse('api-return-order-list')

        # Do not have required permissions yet
        self.post(
            url,
            {
                'customer': 1,
                'description': 'a return order',
            },
            expected_code=403
        )

        self.assignRole('return_order.add')

        data = self.post(
            url,
            {
                'customer': 4,
                'customer_reference': 'cr',
                'description': 'a return order',
            },
            expected_code=201
        ).data

        # Reference automatically generated
        self.assertEqual(data['reference'], 'RMA-0007')
        self.assertEqual(data['customer_reference'], 'cr')

    def test_update(self):
        """Test that we can update a ReturnOrder via the API"""
        url = reverse('api-return-order-detail', kwargs={'pk': 1})

        # Test detail endpoint
        data = self.get(url, expected_code=200).data

        self.assertEqual(data['reference'], 'RMA-001')

        # Attempt to update, incorrect permissions
        self.patch(
            url,
            {
                'customer_reference': 'My customer reference',
            },
            expected_code=403
        )

        self.assignRole('return_order.change')

        self.patch(
            url,
            {
                'customer_reference': 'customer ref',
            },
            expected_code=200
        )

        rma = models.ReturnOrder.objects.get(pk=1)
        self.assertEqual(rma.customer_reference, 'customer ref')

    def test_ro_issue(self):
        """Test the 'issue' order for a ReturnOrder"""
        order = models.ReturnOrder.objects.get(pk=1)
        self.assertEqual(order.status, ReturnOrderStatus.PENDING)
        self.assertIsNone(order.issue_date)

        url = reverse('api-return-order-issue', kwargs={'pk': 1})

        # POST without required permissions
        self.post(url, expected_code=403)

        self.assignRole('return_order.add')

        self.post(url, expected_code=201)
        order.refresh_from_db()
        self.assertEqual(order.status, ReturnOrderStatus.IN_PROGRESS)
        self.assertIsNotNone(order.issue_date)

    def test_receive(self):
        """Test that we can receive items against a ReturnOrder"""
        customer = Company.objects.get(pk=4)

        # Create an order
        rma = models.ReturnOrder.objects.create(
            customer=customer,
            description='A return order',
        )

        self.assertEqual(rma.reference, 'RMA-0007')

        # Create some line items
        part = Part.objects.get(pk=25)
        for idx in range(3):
            stock_item = StockItem.objects.create(
                part=part, customer=customer,
                quantity=1, serial=idx
            )

            line_item = models.ReturnOrderLineItem.objects.create(
                order=rma,
                item=stock_item,
            )

            self.assertEqual(line_item.outcome, ReturnOrderLineStatus.PENDING)
            self.assertIsNone(line_item.received_date)
            self.assertFalse(line_item.received)

        self.assertEqual(rma.lines.count(), 3)

        def receive(items, location=None, expected_code=400):
            """Helper function to receive items against this ReturnOrder"""
            url = reverse('api-return-order-receive', kwargs={'pk': rma.pk})

            response = self.post(
                url,
                {
                    'items': items,
                    'location': location,
                },
                expected_code=expected_code
            )

            return response.data

        # Receive without required permissions
        receive([], expected_code=403)

        self.assignRole('return_order.add')

        # Receive, without any location
        data = receive([], expected_code=400)
        self.assertIn('This field may not be null', str(data['location']))

        # Receive, with incorrect order code
        data = receive([], 1, expected_code=400)
        self.assertIn('Items can only be received against orders which are in progress', str(data))

        # Issue the order (via the API)
        self.assertIsNone(rma.issue_date)
        self.post(
            reverse("api-return-order-issue", kwargs={"pk": rma.pk}),
            expected_code=201,
        )

        rma.refresh_from_db()
        self.assertIsNotNone(rma.issue_date)
        self.assertEqual(rma.status, ReturnOrderStatus.IN_PROGRESS)

        # Receive, without any items
        data = receive([], 1, expected_code=400)
        self.assertIn('Line items must be provided', str(data))

        # Get a reference to one of the stock items
        stock_item = rma.lines.first().item

        n_tracking = stock_item.tracking_info.count()

        # Receive items successfully
        data = receive(
            [{'item': line.pk} for line in rma.lines.all()],
            1,
            expected_code=201
        )

        # Check that all line items have been received
        for line in rma.lines.all():
            self.assertTrue(line.received)
            self.assertIsNotNone(line.received_date)

        # A single tracking entry should have been added to the item
        self.assertEqual(stock_item.tracking_info.count(), n_tracking + 1)

        tracking_entry = stock_item.tracking_info.last()
        deltas = tracking_entry.deltas

        self.assertEqual(deltas['status'], StockStatus.QUARANTINED)
        self.assertEqual(deltas['customer'], customer.pk)
        self.assertEqual(deltas['location'], 1)
        self.assertEqual(deltas['returnorder'], rma.pk)

    def test_ro_calendar(self):
        """Test the calendar export endpoint"""
        # Full test is in test_po_calendar. Since these use the same backend, test only
        # that the endpoint is available
        url = reverse('api-po-so-calendar', kwargs={'ordertype': 'return-order'})

        # Test without completed orders
        response = self.get(url, expected_code=200, format=None)
        calendar = Calendar.from_ical(response.content)
        self.assertIsInstance(calendar, Calendar)


class OrderMetadataAPITest(InvenTreeAPITestCase):
    """Unit tests for the various metadata endpoints of API."""

    fixtures = [
        'category',
        'part',
        'company',
        'location',
        'supplier_part',
        'stock',
        'order',
        'sales_order',
        'return_order',
    ]

    roles = [
        'purchase_order.change',
        'sales_order.change',
        'return_order.change',
    ]

    def metatester(self, apikey, model):
        """Generic tester"""
        modeldata = model.objects.first()

        # Useless test unless a model object is found
        self.assertIsNotNone(modeldata)

        url = reverse(apikey, kwargs={'pk': modeldata.pk})

        # Metadata is initially null
        self.assertIsNone(modeldata.metadata)

        numstr = f'12{len(apikey)}'

        self.patch(
            url,
            {
                'metadata': {
                    f'abc-{numstr}': f'xyz-{apikey}-{numstr}',
                }
            },
            expected_code=200
        )

        # Refresh
        modeldata.refresh_from_db()
        self.assertEqual(modeldata.get_metadata(f'abc-{numstr}'), f'xyz-{apikey}-{numstr}')

    def test_metadata(self):
        """Test all endpoints"""
        for apikey, model in {
            'api-po-metadata': models.PurchaseOrder,
            'api-po-line-metadata': models.PurchaseOrderLineItem,
            'api-po-extra-line-metadata': models.PurchaseOrderExtraLine,
            'api-so-shipment-metadata': models.SalesOrderShipment,
            'api-so-metadata': models.SalesOrder,
            'api-so-line-metadata': models.SalesOrderLineItem,
            'api-so-extra-line-metadata': models.SalesOrderExtraLine,
            'api-return-order-metadata': models.ReturnOrder,
            'api-return-order-line-metadata': models.ReturnOrderLineItem,
            'api-return-order-extra-line-metadata': models.ReturnOrderExtraLine,
        }.items():
            self.metatester(apikey, model)
