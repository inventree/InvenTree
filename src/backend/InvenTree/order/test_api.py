"""Tests for the Order API."""

import base64
import io
import json
from datetime import date, datetime, timedelta
from typing import Optional
from unittest import mock

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from djmoney.money import Money
from icalendar import Calendar
from rest_framework import status

from common.currency import currency_codes
from common.models import InvenTreeCustomUserStateModel, InvenTreeSetting
from common.settings import set_global_setting
from company.models import Company, SupplierPart, SupplierPriceBreak
from InvenTree.unit_test import InvenTreeAPITestCase
from order import models
from order.models import SalesOrderAllocation, SalesOrderLineItem, SalesOrderShipment
from order.status_codes import (
    PurchaseOrderStatus,
    ReturnOrderLineStatus,
    ReturnOrderStatus,
    SalesOrderStatus,
    SalesOrderStatusGroups,
    TransferOrderStatus,
    TransferOrderStatusGroups,
)
from part.models import Part
from stock.models import StockItem, StockLocation, StockSortOrder
from stock.status_codes import StockHistoryCode, StockStatus
from users.models import Owner


class OrderTest(InvenTreeAPITestCase):
    """Base class for order API unit testing."""

    fixtures = [
        'category',
        'part',
        'company',
        'location',
        'supplier_part',
        'stock',
        'order',
        'sales_order',
        'transfer_order',
    ]

    roles = ['purchase_order.change', 'sales_order.change', 'transfer_order.change']

    def filter(self, filters, count):
        """Test API filters."""
        response = self.get(self.LIST_URL, filters)

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
        check_options(
            post,
            'order_currency',
            {
                'type': 'choice',
                'required': False,
                'read_only': False,
                'label': 'Order Currency',
                'help_text': 'Currency for this order (leave blank to use company default)',
            },
        )

        # Checks for the 'reference' field
        check_options(
            post,
            'reference',
            {
                'type': 'string',
                'required': True,
                'read_only': False,
                'label': 'Reference',
            },
        )

        # Checks for the 'supplier' field
        check_options(
            post,
            'supplier',
            {'type': 'related field', 'required': True, 'api_url': '/api/company/'},
        )

    def test_po_list(self):
        """Test the PurchaseOrder list API endpoint."""
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
        self.filter({'status': PurchaseOrderStatus.PENDING.value}, 3)
        self.filter({'status': PurchaseOrderStatus.CANCELLED.value}, 1)

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
        """Unit tests for the 'total_price' field."""
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
                    models.PurchaseOrder(supplier=supplier, reference=f'PO-{idx + 100}')
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
                response = self.get(
                    self.LIST_URL, data={'limit': limit}, expected_code=200
                )

                # Total database queries must be below 25, independent of the number of results
                self.assertLess(len(ctx), 25)

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
        """Test the PurchaseOrder detail API endpoint."""
        url = '/api/order/po/1/'

        response = self.get(url)

        self.assertEqual(response.status_code, 200)

        data = response.data

        self.assertEqual(data['pk'], 1)
        self.assertEqual(data['description'], 'Ordering some screws')

    def test_po_status_custom_key_options(self):
        """Test that status_custom_key is exposed as writable in options."""
        self.assignRole('purchase_order.add')

        response = self.options(self.LIST_URL, expected_code=200)
        post = response.data['actions']['POST']

        self.assertIn('status_custom_key', post)
        self.assertEqual(post['status_custom_key']['required'], False)
        self.assertEqual(post['status_custom_key']['read_only'], False)

    def test_po_status_custom_key_patch_valid(self):
        """Test patching a valid custom status key for the current PO status."""
        self.assignRole('purchase_order.change')

        po = models.PurchaseOrder.objects.get(pk=1)
        self.assertEqual(po.status, PurchaseOrderStatus.PENDING.value)

        custom_status = InvenTreeCustomUserStateModel.objects.create(
            key=901,
            name='PO Pending Custom',
            label='PO Pending Custom',
            color='secondary',
            logical_key=PurchaseOrderStatus.PENDING.value,
            model=ContentType.objects.get_for_model(models.PurchaseOrder),
            reference_status='PurchaseOrderStatus',
        )

        url = reverse('api-po-detail', kwargs={'pk': po.pk})
        response = self.patch(
            url, {'status_custom_key': custom_status.key}, expected_code=200
        )

        self.assertEqual(response.data['status'], PurchaseOrderStatus.PENDING.value)
        self.assertEqual(response.data['status_custom_key'], custom_status.key)

    def test_po_status_custom_key_patch_invalid(self):
        """Test patching an invalid custom status key for a PO."""
        self.assignRole('purchase_order.change')

        po = models.PurchaseOrder.objects.get(pk=1)
        url = reverse('api-po-detail', kwargs={'pk': po.pk})

        response = self.patch(url, {'status_custom_key': 999999}, expected_code=400)

        self.assertIn('status_custom_key', response.data)

    def test_po_status_custom_key_patch_wrong_logical_status(self):
        """Test patching a custom key mapped to a different logical status."""
        self.assignRole('purchase_order.change')

        po = models.PurchaseOrder.objects.get(pk=1)
        self.assertEqual(po.status, PurchaseOrderStatus.PENDING.value)

        custom_status = InvenTreeCustomUserStateModel.objects.create(
            key=902,
            name='PO Placed Custom',
            label='PO Placed Custom',
            color='secondary',
            logical_key=PurchaseOrderStatus.PLACED.value,
            model=ContentType.objects.get_for_model(models.PurchaseOrder),
            reference_status='PurchaseOrderStatus',
        )

        url = reverse('api-po-detail', kwargs={'pk': po.pk})
        response = self.patch(
            url, {'status_custom_key': custom_status.key}, expected_code=400
        )

        self.assertIn('status_custom_key', response.data)

    def test_po_reference(self):
        """Test that a reference with a too big / small reference is handled correctly."""
        # get permissions
        self.assignRole('purchase_order.add')

        url = reverse('api-po-list')
        huge_number = 'PO-92233720368547758089999999999999999'

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

        # Check that the created_by field is set correctly
        self.assertEqual(order.created_by.username, 'testuser')

        self.assertEqual(order.reference, huge_number)
        self.assertEqual(order.reference_int, 0x7FFFFFFF)

    def test_po_reference_wildcard_default(self):
        """Test that a reference with a wildcard default."""
        # get permissions
        self.assignRole('purchase_order.add')

        # set PO reference setting
        set_global_setting('PURCHASEORDER_REFERENCE_PATTERN', '{?:PO}-{ref:04d}')

        url = reverse('api-po-list')

        # first, check that the default character is suggested by OPTIONS
        options = json.loads(self.options(url).content)
        suggested_reference = options['actions']['POST']['reference']['default']
        self.assertTrue(suggested_reference.startswith('PO-'))

        # next, check that certain variations of a provided reference are accepted
        test_accepted_references = ['PO-9991', 'P-9992', 'T-9993', 'ABC-9994']
        for ref in test_accepted_references:
            response = self.post(
                url,
                {
                    'supplier': 1,
                    'reference': ref,
                    'description': 'PO created via the API',
                },
                expected_code=201,
            )
            order = models.PurchaseOrder.objects.get(pk=response.data['pk'])
            self.assertEqual(order.reference, ref)

        # finally, check that certain provided referencees are rejected (because the wildcard character is required!)
        test_rejected_references = ['9995', '-9996']
        for ref in test_rejected_references:
            response = self.post(
                url,
                {
                    'supplier': 1,
                    'reference': ref,
                    'description': 'PO created via the API',
                },
                expected_code=400,
            )

    def test_po_attachments(self):
        """Test the list endpoint for the PurchaseOrderAttachment model."""
        url = reverse('api-attachment-list')

        response = self.get(url, {'model_type': 'purchaseorder'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_output_options(self):
        """Test the various output options for the PurchaseOrder detail endpoint."""
        self.run_output_test(
            reverse('api-po-detail', kwargs={'pk': 1}), ['supplier_detail']
        )

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
            expected_code=403,
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
            expected_code=201,
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
            expected_code=400,
        )

        self.assertEqual(models.PurchaseOrder.objects.count(), n + 1)

        url = reverse('api-po-detail', kwargs={'pk': pk})

        # Get detail info!
        response = self.get(url)
        self.assertEqual(response.data['pk'], pk)
        self.assertEqual(response.data['reference'], 'PO-123456789')

        # Try to alter (edit) the PurchaseOrder
        response = self.patch(url, {'reference': 'PO-12345'}, expected_code=200)

        # Reference should have changed
        self.assertEqual(response.data['reference'], 'PO-12345')

        # Now, let's try to delete it!
        # Initially, we do *not* have the required permission!
        response = self.delete(url, expected_code=403)

        # Now, add the "delete" permission!
        self.assignRole('purchase_order.delete')

        response = self.delete(url, expected_code=204)

        # Number of PurchaseOrder objects should have decreased
        self.assertEqual(models.PurchaseOrder.objects.count(), n)

        # And if we try to access the detail view again, it has gone
        response = self.get(url, expected_code=404)

    def test_po_create(self):
        """Test that we can create a new PurchaseOrder via the API."""
        self.assignRole('purchase_order.add')

        setting = 'PURCHASEORDER_REQUIRE_RESPONSIBLE'
        url = reverse('api-po-list')

        InvenTreeSetting.set_setting(setting, False)

        data = {
            'reference': 'PO-12345678',
            'supplier': 1,
            'description': 'A test purchase order',
        }

        self.post(url, data, expected_code=201)

        # Check the 'responsible required' field
        InvenTreeSetting.set_setting(setting, True)

        data['reference'] = 'PO-12345679'
        data['responsible'] = None

        response = self.post(url, data, expected_code=400)

        self.assertIn('Responsible user or group must be specified', str(response.data))

        owner = Owner.objects.first()
        assert owner
        data['responsible'] = owner.pk

        response = self.post(url, data, expected_code=201)

        # Revert the setting to previous value
        InvenTreeSetting.set_setting(setting, False)

    def test_po_creation_date(self):
        """Test that we can create set the creation_date field of PurchaseOrder via the API."""
        self.assignRole('purchase_order.add')

        response = self.post(
            reverse('api-po-list'),
            {
                'reference': 'PO-19881110',
                'supplier': 1,
                'description': 'PO created on 1988-11-10',
                'creation_date': '1988-11-10',
            },
            expected_code=201,
        )

        po = models.PurchaseOrder.objects.get(pk=response.data['pk'])
        self.assertEqual(po.creation_date, datetime(1988, 11, 10).date())

        """Ensure if we do not pass the creation_date field than the current date will be saved"""
        creation_date = datetime.now().date()
        response = self.post(
            reverse('api-po-list'),
            {
                'reference': 'PO-11111111',
                'supplier': 1,
                'description': 'Check that the creation date is today',
            },
            expected_code=201,
        )

        po = models.PurchaseOrder.objects.get(pk=response.data['pk'])
        self.assertEqual(po.creation_date, creation_date)

    def test_po_duplicate(self):
        """Test that we can duplicate a PurchaseOrder via the API."""
        self.assignRole('purchase_order.add')

        po = models.PurchaseOrder.objects.get(pk=1)

        self.assertGreater(po.lines.count(), 0)

        lines = []

        # Add some extra line items to this order
        for idx in range(5):
            lines.append(
                models.PurchaseOrderExtraLine(
                    order=po, quantity=idx + 10, reference='some reference'
                )
            )

        # bulk create orders
        models.PurchaseOrderExtraLine.objects.bulk_create(lines)

        data = self.get(reverse('api-po-detail', kwargs={'pk': 1})).data

        del data['pk']
        del data['reference']

        # Duplicate with non-existent PK to provoke error
        data['duplicate'] = {
            'original': 10000001,
            'copy_lines': True,
            'copy_extra_lines': False,
        }

        data['reference'] = 'PO-9999'

        # Duplicate via the API
        response = self.post(reverse('api-po-list'), data, expected_code=400)

        data['duplicate'] = {
            'original': 1,
            'copy_lines': True,
            'copy_extra_lines': False,
        }

        data['reference'] = 'PO-9999'

        # Duplicate via the API
        response = self.post(reverse('api-po-list'), data, expected_code=201)

        # Order is for the same supplier
        self.assertEqual(response.data['supplier'], po.supplier.pk)

        po_dup = models.PurchaseOrder.objects.get(pk=response.data['pk'])

        self.assertEqual(po_dup.extra_lines.count(), 0)
        self.assertEqual(po_dup.lines.count(), po.lines.count())

        data['reference'] = 'PO-9998'

        data['duplicate'] = {
            'original': 1,
            'copy_lines': False,
            'copy_extra_lines': True,
        }

        response = self.post(reverse('api-po-list'), data, expected_code=201)

        po_dup = models.PurchaseOrder.objects.get(pk=response.data['pk'])

        self.assertEqual(po_dup.extra_lines.count(), po.extra_lines.count())
        self.assertEqual(po_dup.lines.count(), 0)

    def test_po_cancel(self):
        """Test the PurchaseOrderCancel API endpoint."""
        po = models.PurchaseOrder.objects.get(pk=1)

        self.assertEqual(po.status, PurchaseOrderStatus.PENDING)

        url = reverse('api-po-cancel', kwargs={'pk': po.pk})

        # Get an OPTIONS request from the endpoint
        self.options(url, data={'context': True}, expected_code=200)

        # Try to cancel the PO, but without required permissions
        self.post(url, {}, expected_code=403)

        self.assignRole('purchase_order.add')

        self.post(url, {}, expected_code=201)

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

        # Add a line item
        sp = SupplierPart.objects.filter(supplier=po.supplier).first()

        models.PurchaseOrderLineItem.objects.create(part=sp, order=po, quantity=100)

        # Should fail due to incomplete lines
        response = self.post(url, {}, expected_code=400)

        self.assertIn(
            'Order has incomplete line items', str(response.data['accept_incomplete'])
        )

        # Post again, accepting incomplete line items
        self.post(url, {'accept_incomplete': True}, expected_code=201)

        po.refresh_from_db()

        self.assertEqual(po.status, PurchaseOrderStatus.COMPLETE)

    def test_po_complete_stale_instance_is_noop(self):
        """A second completion attempt with a stale order instance must be a no-op.

        Regression test: _action_complete() checked 'status' on the caller's
        (potentially stale) instance, so two concurrent completion requests could
        both run the completion side effects (duplicate COMPLETED events and
        duplicate pricing-update scheduling). The status is now re-read (under
        lock) from the database before the check.
        """
        po = models.PurchaseOrder.objects.get(pk=3)
        self.assertEqual(po.status, PurchaseOrderStatus.PLACED)

        # Two "concurrent" requests each hold their own instance of the order
        po_a = models.PurchaseOrder.objects.get(pk=po.pk)
        po_b = models.PurchaseOrder.objects.get(pk=po.pk)

        po_a.complete_order()

        po.refresh_from_db()
        self.assertEqual(po.status, PurchaseOrderStatus.COMPLETE)

        # The second (stale) instance still believes the order is PLACED -
        # completion must be skipped based on the database state
        self.assertEqual(po_b.status, PurchaseOrderStatus.PLACED)

        with mock.patch('order.models.trigger_event') as trigger:
            po_b.complete_order()
            trigger.assert_not_called()

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
        """Test the calendar export endpoint."""
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
                expected_code=201,
            )

        # Get some of these orders with target date, complete or cancel them
        for po in models.PurchaseOrder.objects.filter(target_date__isnull=False):
            if po.reference in [
                'PO-11000001',
                'PO-11000002',
                'PO-11000003',
                'PO-11000004',
            ]:
                # Set issued status for these POs
                self.post(
                    reverse('api-po-issue', kwargs={'pk': po.pk}), {}, expected_code=201
                )

                if po.reference in ['PO-11000001', 'PO-11000002']:
                    # Set complete status for these POs
                    self.post(
                        reverse('api-po-complete', kwargs={'pk': po.pk}),
                        {'accept_incomplete': True},
                        expected_code=201,
                    )

            elif po.reference in ['PO-11000005', 'PO-11000006']:
                # Set cancel status for these POs
                self.post(
                    reverse('api-po-cancel', kwargs={'pk': po.pk}),
                    {'accept_incomplete': True},
                    expected_code=201,
                )

        url = reverse('api-po-so-calendar', kwargs={'ordertype': 'purchase-order'})

        # Test without completed orders
        response = self.get(url, expected_code=200, format=None)

        number_orders = len(
            models.PurchaseOrder.objects.filter(target_date__isnull=False).filter(
                status__lt=PurchaseOrderStatus.COMPLETE.value
            )
        )

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
        response = self.get(
            url, data={'include_completed': 'True'}, expected_code=200, format=None
        )

        number_orders_incl_completed = len(
            models.PurchaseOrder.objects.filter(target_date__isnull=False)
        )

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
        """Test accessing calendar without authorization."""
        self.client.logout()
        response = self.client.get(
            reverse('api-po-so-calendar', kwargs={'ordertype': 'purchase-order'}),
            format='json',
        )

        self.assertEqual(response.status_code, 401)

        resp_dict = response.json()
        self.assertEqual(
            resp_dict['detail'], 'Authentication credentials were not provided.'
        )

    def test_po_calendar_auth(self):
        """Test accessing calendar with header authorization."""
        self.client.logout()
        base64_token = base64.b64encode(
            f'{self.username}:{self.password}'.encode('ascii')
        ).decode('ascii')
        response = self.client.get(
            reverse('api-po-so-calendar', kwargs={'ordertype': 'purchase-order'}),
            format='json',
            headers={'authorization': f'basic {base64_token}'},
        )
        self.assertEqual(response.status_code, 200)

    def test_po_custom_status_query_count(self):
        """Test that listing PurchaseOrders with custom statuses does not cause N+1 queries.

        Ensures that resolving the 'status_text' field for custom status values
        is O(1) in database queries, not O(N) relative to the number of results.
        """
        from django.contrib.contenttypes.models import ContentType

        po_content_type = ContentType.objects.get_for_model(models.PurchaseOrder)

        # 10 custom status values - different keys, labels, and logical_keys
        logical_keys = [
            PurchaseOrderStatus.PENDING.value,
            PurchaseOrderStatus.PLACED.value,
            PurchaseOrderStatus.ON_HOLD.value,
            PurchaseOrderStatus.COMPLETE.value,
            PurchaseOrderStatus.CANCELLED.value,
            PurchaseOrderStatus.LOST.value,
            PurchaseOrderStatus.RETURNED.value,
            PurchaseOrderStatus.PENDING.value,
            PurchaseOrderStatus.PLACED.value,
            PurchaseOrderStatus.ON_HOLD.value,
        ]

        custom_statuses = [
            InvenTreeCustomUserStateModel.objects.create(
                key=1000 + i,
                name=f'PoCustomStatus{i}',
                label=f'PO Custom Status Label {i}',
                color='secondary',
                logical_key=logical_keys[i],
                model=po_content_type,
                reference_status='PurchaseOrderStatus',
            )
            for i in range(10)
        ]

        # Create 100 purchase orders, cycling through the custom statuses
        supplier = Company.objects.filter(is_supplier=True).first()
        models.PurchaseOrder.objects.bulk_create([
            models.PurchaseOrder(
                supplier=supplier,
                reference=f'PO-QTEST-{i}',
                status=custom_statuses[i % 10].logical_key,
                status_custom_key=custom_statuses[i % 10].key,
            )
            for i in range(100)
        ])

        # Query count must stay below the fixed threshold for all limit values.
        # An N+1 bug would push limit=50 or limit=100 well over the threshold.
        for limit in [1, 5, 10, 25, 50, 100]:
            response = self.get(
                self.LIST_URL,
                data={'limit': limit},
                expected_code=200,
                max_query_count=50,
            )

            for result in response.data['results']:
                self.assertIn('status_text', result)
                self.assertIsNotNone(result['status_text'])


class PurchaseOrderLineItemTest(OrderTest):
    """Unit tests for PurchaseOrderLineItems."""

    LIST_URL = reverse('api-po-line-list')

    def test_po_line_list(self):
        """Test the PurchaseOrderLine list API endpoint."""
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

        url = reverse('api-po-line-list')

        # Deletion should fail without the correct role
        self.delete(url, {'items': [1, 2]}, expected_code=403)

        self.assignRole('purchase_order.delete')

        # Try to delete a set of line items via their IDs
        self.delete(url, {'items': [1, 2]}, expected_code=200)

        # We should have 2 less PurchaseOrderLineItems after deleting them
        self.assertEqual(models.PurchaseOrderLineItem.objects.count(), n - 2)

    def test_po_extra_line_bulk_delete(self):
        """Test that we can bulk delete multiple PurchaseOrderExtraLine items via the API."""
        po = models.PurchaseOrder.objects.get(pk=1)

        models.PurchaseOrderExtraLine.objects.bulk_create([
            models.PurchaseOrderExtraLine(
                order=po, quantity=idx + 1, reference=f'Extra line {idx}'
            )
            for idx in range(3)
        ])

        n = models.PurchaseOrderExtraLine.objects.count()
        items = list(
            models.PurchaseOrderExtraLine.objects.values_list('pk', flat=True)[:2]
        )

        url = reverse('api-po-extra-line-list')

        # Deletion should fail without the correct role
        self.delete(url, {'items': items}, expected_code=403)

        self.assignRole('purchase_order.delete')

        self.delete(url, {'items': items}, expected_code=200)

        self.assertEqual(models.PurchaseOrderExtraLine.objects.count(), n - 2)

    def test_po_line_merge_pricing(self):
        """Test that we can create a new PurchaseOrderLineItem via the API."""
        self.assignRole('purchase_order.add')
        self.generate_exchange_rates()

        su = Company.objects.get(pk=1)
        sp = SupplierPart.objects.get(pk=1)
        po = models.PurchaseOrder.objects.create(supplier=su, reference='PO-1234567890')
        SupplierPriceBreak.objects.create(part=sp, quantity=1, price=Money(1, 'USD'))
        SupplierPriceBreak.objects.create(part=sp, quantity=10, price=Money(0.5, 'USD'))

        li1 = self.post(
            reverse('api-po-line-list'),
            {
                'order': po.pk,
                'part': sp.pk,
                'quantity': 1,
                'auto_pricing': True,
                'merge_items': False,
            },
            expected_code=201,
        ).json()
        self.assertEqual(float(li1['purchase_price']), 1)

        li2 = self.post(
            reverse('api-po-line-list'),
            {
                'order': po.pk,
                'part': sp.pk,
                'quantity': 10,
                'auto_pricing': True,
                'merge_items': False,
            },
            expected_code=201,
        ).json()
        self.assertEqual(float(li2['purchase_price']), 0.5)

        # test that items where not merged
        self.assertNotEqual(li1['pk'], li2['pk'])

        li3 = self.post(
            reverse('api-po-line-list'),
            {
                'order': po.pk,
                'part': sp.pk,
                'quantity': 9,
                'auto_pricing': True,
                'merge_items': True,
            },
            expected_code=201,
        ).json()

        # test that items where merged
        self.assertEqual(li1['pk'], li3['pk'])

        # test that price was recalculated
        self.assertEqual(float(li3['purchase_price']), 0.5)

        # test that pricing will be not recalculated if auto_pricing is False
        li4 = self.post(
            reverse('api-po-line-list'),
            {
                'order': po.pk,
                'part': sp.pk,
                'quantity': 1,
                'auto_pricing': False,
                'purchase_price': 0.5,
                'merge_items': False,
            },
            expected_code=201,
        ).json()
        self.assertEqual(float(li4['purchase_price']), 0.5)

        # test that pricing is correctly recalculated if auto_pricing is True for update
        li5 = self.patch(
            reverse('api-po-line-detail', kwargs={'pk': li4['pk']}),
            {**li4, 'quantity': 5, 'auto_pricing': False},
            expected_code=200,
        ).json()
        self.assertEqual(float(li5['purchase_price']), 0.5)

        li5 = self.patch(
            reverse('api-po-line-detail', kwargs={'pk': li4['pk']}),
            {**li4, 'quantity': 5, 'auto_pricing': True},
            expected_code=200,
        ).json()
        self.assertEqual(float(li5['purchase_price']), 1)

    def test_output_options(self):
        """Test PurchaseOrderLineItem output option endpoint."""
        self.run_output_test(
            reverse('api-po-line-detail', kwargs={'pk': 1}),
            ['part_detail', 'order_detail'],
        )


class PurchaseOrderDownloadTest(OrderTest):
    """Unit tests for downloading PurchaseOrder data via the API endpoint."""

    required_cols = [
        'ID',
        'Line Items',
        'Description',
        'Issue Date',
        'Order Currency',
        'Reference',
        'Order Status',
        'Supplier Reference',
    ]

    excluded_cols = ['metadata']

    def test_download_wrong_format(self):
        """Incorrect format should default raise an error."""
        url = reverse('api-po-list')

        response = self.export_data(url, export_format='xyz', expected_code=400)
        self.assertIn('is not a valid choice', str(response['export_format']))

    def test_download_csv(self):
        """Download PurchaseOrder data as .csv."""
        with self.export_data(
            reverse('api-po-list'),
            expected_code=200,
            expected_fn=r'InvenTree_PurchaseOrder_.+\.csv',
        ) as file:
            data = self.process_csv(
                file,
                required_cols=self.required_cols,
                excluded_cols=self.excluded_cols,
                required_rows=models.PurchaseOrder.objects.count(),
            )

            for row in data:
                order = models.PurchaseOrder.objects.get(pk=row['ID'])

                self.assertEqual(order.description, row['Description'])
                self.assertEqual(order.reference, row['Reference'])

    def test_download_line_items(self):
        """Test that the PurchaseOrderLineItems can be downloaded to a file."""
        with self.export_data(
            reverse('api-po-line-list'),
            export_format='xlsx',
            expected_code=200,
            expected_fn=r'InvenTree_PurchaseOrderLineItem.+\.xlsx',
            decode=False,
        ) as file:
            self.assertIsInstance(file, io.BytesIO)


class PurchaseOrderReceiveTest(OrderTest):
    """Unit tests for receiving items against a PurchaseOrder."""

    def setUp(self):
        """Init routines for this unit test class."""
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

        # No new stock items have been created
        self.assertEqual(self.n, StockItem.objects.count())

    def test_no_items(self):
        """Test with an empty list of items."""
        data = self.post(
            self.url, {'items': [], 'location': None}, expected_code=400
        ).data

        self.assertIn('Line items must be provided', str(data))

        # No new stock items have been created
        self.assertEqual(self.n, StockItem.objects.count())

    def test_invalid_items(self):
        """Test than errors are returned as expected for invalid data."""
        data = self.post(
            self.url,
            {'items': [{'line_item': 12345, 'location': 12345}]},
            expected_code=400,
        ).data

        items = data['items'][0]

        self.assertIn('Invalid pk "12345"', str(items['line_item']))
        self.assertIn('object does not exist', str(items['location']))

        # No new stock items have been created
        self.assertEqual(self.n, StockItem.objects.count())

    def test_invalid_status(self):
        """Test with an invalid StockStatus value."""
        data = self.post(
            self.url,
            {
                'items': [
                    {'line_item': 22, 'location': 1, 'status': 99999, 'quantity': 5}
                ]
            },
            expected_code=400,
        ).data

        self.assertIn('"99999" is not a valid choice.', str(data))

        # No new stock items have been created
        self.assertEqual(self.n, StockItem.objects.count())

    def test_mismatched_items(self):
        """Test for supplier parts which *do* exist but do not match the order supplier."""
        data = self.post(
            self.url,
            {
                'items': [{'line_item': 22, 'quantity': 123, 'location': 1}],
                'location': None,
            },
            expected_code=400,
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
                'items': [{'line_item': 1, 'quantity': 50, 'barcode': None}],
                'location': 1,
            },
            expected_code=201,
        )

    def test_invalid_barcodes(self):
        """Tests for checking in items with invalid barcodes.

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
                    {'line_item': 1, 'quantity': 50, 'barcode': 'MY-BARCODE-HASH'}
                ],
                'location': 1,
            },
            expected_code=400,
        )

        self.assertIn('Barcode is already in use', str(response.data))

        response = self.post(
            self.url,
            {
                'items': [
                    {'line_item': 1, 'quantity': 5, 'barcode': 'MY-BARCODE-HASH-1'},
                    {'line_item': 1, 'quantity': 5, 'barcode': 'MY-BARCODE-HASH-1'},
                ],
                'location': 1,
            },
            expected_code=400,
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

        one_week_from_today = date.today() + timedelta(days=7)

        valid_data = {
            'items': [
                {
                    'line_item': 1,
                    'quantity': 50,
                    'expiry_date': one_week_from_today.strftime(r'%Y-%m-%d'),
                    'barcode': 'MY-UNIQUE-BARCODE-123',
                },
                {
                    'line_item': 2,
                    'quantity': 200,
                    'expiry_date': one_week_from_today.strftime(r'%Y-%m-%d'),
                    'location': 2,  # Explicit location
                    'barcode': 'MY-UNIQUE-BARCODE-456',
                },
            ],
            'location': 1,  # Default location
        }

        # Before posting "valid" data, we will mark the purchase order as "pending"
        # In this case we do expect an error!
        order = models.PurchaseOrder.objects.get(pk=1)
        order.status = PurchaseOrderStatus.PENDING.value
        order.save()

        response = self.post(self.url, valid_data, expected_code=400)

        self.assertIn('can only be received against', str(response.data))

        # Now, set the PurchaseOrder back to "PLACED" so the items can be received
        order.status = PurchaseOrderStatus.PLACED.value
        order.save()

        # Receive two separate line items against this order
        self.post(self.url, valid_data, expected_code=201)

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

        # Check received locations
        self.assertEqual(stock_1.last().location.pk, 1)
        self.assertEqual(stock_2.last().location.pk, 2)

        # Expiry dates should be set
        self.assertEqual(stock_1.last().expiry_date, one_week_from_today)
        self.assertEqual(stock_2.last().expiry_date, one_week_from_today)

        # creation_date must be populated on both received items
        self.assertIsNotNone(stock_1.last().creation_date)
        self.assertIsNotNone(stock_2.last().creation_date)

        # Barcodes should have been assigned to the stock items
        self.assertTrue(
            StockItem.objects.filter(barcode_data='MY-UNIQUE-BARCODE-123').exists()
        )
        self.assertTrue(
            StockItem.objects.filter(barcode_data='MY-UNIQUE-BARCODE-456').exists()
        )

    def test_batch_code(self):
        """Test that we can supply a 'batch code' when receiving items."""
        line_1 = models.PurchaseOrderLineItem.objects.get(pk=1)
        line_2 = models.PurchaseOrderLineItem.objects.get(pk=2)

        self.assertEqual(StockItem.objects.filter(supplier_part=line_1.part).count(), 0)
        self.assertEqual(StockItem.objects.filter(supplier_part=line_2.part).count(), 0)

        data = {
            'items': [
                {'line_item': 1, 'quantity': 10, 'batch_code': 'B-abc-123'},
                {'line_item': 2, 'quantity': 10, 'batch_code': 'B-xyz-789'},
            ],
            'location': 1,
        }

        n = StockItem.objects.count()

        self.post(self.url, data, expected_code=201)

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
                {'line_item': 2, 'quantity': 10, 'batch_code': 'B-xyz-789'},
            ],
            'location': 1,
        }

        n = StockItem.objects.count()

        self.post(self.url, data, expected_code=201, max_query_count=275)

        # Check that the expected number of stock items has been created
        self.assertEqual(n + 11, StockItem.objects.count())

        # 10 serialized stock items created for the first line item
        self.assertEqual(
            StockItem.objects.filter(supplier_part=line_1.part).count(), 10
        )

        # Check that the correct serial numbers have been allocated
        for i in range(100, 110):
            item = StockItem.objects.get(serial_int=i)
            self.assertEqual(item.serial, str(i))
            self.assertEqual(item.quantity, 1)
            self.assertEqual(item.batch, 'B-abc-123')
            self.assertIsNotNone(item.creation_date)

        # A single stock item (quantity 10) created for the second line item
        items = StockItem.objects.filter(supplier_part=line_2.part)
        self.assertEqual(items.count(), 1)

        item = items.first()

        self.assertEqual(item.quantity, 10)
        self.assertEqual(item.batch, 'B-xyz-789')

    def test_duplicate_serial_numbers_across_items(self):
        """Duplicate serial numbers across line items in a single request are rejected.

        Regression test: each line's serials used to be validated against the
        database only, so two lines could claim the same serial number and create
        duplicate serialized stock items.
        """
        data = {
            'items': [
                {'line_item': 1, 'quantity': 3, 'serial_numbers': '100-102'},
                {'line_item': 1, 'quantity': 3, 'serial_numbers': '102-104'},
            ],
            'location': 1,
        }

        # Serial 102 is claimed by both entries - request must be rejected
        response = self.post(self.url, data, expected_code=400)

        self.assertIn('Supplied serial numbers must be unique', str(response.data))

        # No new stock items have been created
        self.assertEqual(self.n, StockItem.objects.count())

        # Non-overlapping serial numbers are accepted
        data['items'][1]['serial_numbers'] = '103-105'

        self.post(self.url, data, expected_code=201, max_query_count=250)

        self.assertEqual(self.n + 6, StockItem.objects.count())

        for serial in range(100, 106):
            self.assertEqual(
                StockItem.objects.filter(serial=str(serial)).count(),
                1,
                f'Expected exactly one stock item with serial {serial}',
            )

    def test_receive_large_quantity(self):
        """Test receipt of a large number of items."""
        from stock.status_codes import StockStatus

        sp = SupplierPart.objects.first()

        # Create a new order
        po = models.PurchaseOrder.objects.create(
            reference='PO-9999', supplier=sp.supplier
        )

        N_LINES = 250

        # Create some line items
        models.PurchaseOrderLineItem.objects.bulk_create([
            models.PurchaseOrderLineItem(order=po, part=sp, quantity=1000 + i)
            for i in range(N_LINES)
        ])

        # Place the order
        po.place_order()

        url = reverse('api-po-receive', kwargs={'pk': po.pk})

        lines = po.lines.all()
        location = StockLocation.objects.filter(structural=False).first()

        N_ITEMS = StockItem.objects.count()

        # Receive all items in a single request
        response = self.post(
            url,
            {
                'items': [
                    {
                        'line_item': line.pk,
                        'quantity': line.quantity,
                        'status': StockStatus.QUARANTINED.value,
                    }
                    for line in lines
                ],
                'location': location.pk,
            },
            max_query_count=104 + 3 * N_LINES,
        ).data

        # Check for expected response
        self.assertEqual(len(response), N_LINES)

        # Check that the expected number of stock items has been created
        self.assertEqual(N_ITEMS + N_LINES, StockItem.objects.count())

        for item in response:
            self.assertEqual(item['purchase_order'], po.pk)
            self.assertEqual(item['status'], StockStatus.QUARANTINED)

            stock_item = StockItem.objects.get(pk=item['pk'])
            # Check that the item has tracking entries
            self.assertEqual(stock_item.tracking_info.count(), 1)
            entry = stock_item.tracking_info.first()
            self.assertEqual(entry.deltas['quantity'], stock_item.quantity)
            self.assertEqual(entry.user, self.user)
            self.assertEqual(
                entry.tracking_type, StockHistoryCode.RECEIVED_AGAINST_PURCHASE_ORDER
            )

        # Check that the order has been completed
        po.refresh_from_db()
        self.assertEqual(po.status, PurchaseOrderStatus.COMPLETE)

        for line in lines:
            line.refresh_from_db()
            self.assertEqual(line.received, line.quantity)

    def test_bulk_receive_query_benchmark(self):
        """Benchmark: measure the number of DB queries required to receive 100 line items at once."""
        InvenTreeSetting.set_setting('ENABLE_PLUGINS_EVENTS', True, change_user=None)

        sp = SupplierPart.objects.first()

        po = models.PurchaseOrder.objects.create(
            reference='PO-BENCHMARK-100', supplier=sp.supplier
        )

        N_LINES = 100

        models.PurchaseOrderLineItem.objects.bulk_create([
            models.PurchaseOrderLineItem(order=po, part=sp, quantity=10)
            for _ in range(N_LINES)
        ])

        po.place_order()

        url = reverse('api-po-receive', kwargs={'pk': po.pk})

        lines = po.lines.all()
        location = StockLocation.objects.filter(structural=False).first()

        data = {
            'items': [
                {'line_item': line.pk, 'quantity': line.quantity} for line in lines
            ],
            'location': location.pk,
        }

        with self.settings(
            PLUGIN_TESTING_EVENTS=True, PLUGIN_TESTING_EVENTS_ASYNC=True
        ):
            response = self.post(
                url, data, max_query_count=400, benchmark=True, format='json'
            )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(response.data), N_LINES)

    def test_packaging(self):
        """Test that we can supply a 'packaging' value when receiving items."""
        line_1 = models.PurchaseOrderLineItem.objects.get(pk=1)
        line_2 = models.PurchaseOrderLineItem.objects.get(pk=2)

        line_1.part.packaging = 'Reel'
        line_1.part.save()

        line_2.part.packaging = 'Tube'
        line_2.part.save()

        # Receive items without packaging data
        data = {
            'items': [
                {'line_item': line_1.pk, 'quantity': 1},
                {'line_item': line_2.pk, 'quantity': 1},
            ],
            'location': 1,
        }

        n = StockItem.objects.count()

        self.post(self.url, data, expected_code=201)

        item_1 = StockItem.objects.filter(supplier_part=line_1.part).first()
        self.assertEqual(item_1.packaging, 'Reel')

        item_2 = StockItem.objects.filter(supplier_part=line_2.part).first()
        self.assertEqual(item_2.packaging, 'Tube')

        # Receive items and override packaging data
        data = {
            'items': [
                {'line_item': line_1.pk, 'quantity': 1, 'packaging': 'Bag'},
                {'line_item': line_2.pk, 'quantity': 1, 'packaging': 'Box'},
            ],
            'location': 1,
        }

        self.post(self.url, data, expected_code=201)

        item_1 = StockItem.objects.filter(supplier_part=line_1.part).last()
        self.assertEqual(item_1.packaging, 'Bag')

        item_2 = StockItem.objects.filter(supplier_part=line_2.part).last()
        self.assertEqual(item_2.packaging, 'Box')

        # Check that the expected number of stock items has been created
        self.assertEqual(n + 4, StockItem.objects.count())

    def test_virtual(self):
        """Test receipt of "virtual" items (i.e. items which do not create a StockItem)."""
        line = models.PurchaseOrderLineItem.objects.get(pk=1)
        base_part = line.part.part
        base_part.virtual = True
        base_part.save()

        self.assertEqual(line.received, 0)

        N_ITEMS = base_part.stock_entries().count()
        N_STOCK = base_part.get_stock_count()

        # Try with serial numbers (expect to fail)
        data = {
            'items': [{'line_item': line.pk, 'quantity': 1, 'serial_numbers': '999'}],
            'location': 1,
        }

        response = self.post(self.url, data, expected_code=400)

        self.assertIn(
            'Serial numbers cannot be assigned to virtual parts',
            str(response.data['non_field_errors']),
        )

        # Try without serial numbers (expect to succeed)
        data = {
            'items': [{'line_item': line.pk, 'quantity': line.quantity}],
            'location': 1,
        }

        self.post(self.url, data, expected_code=201)

        # No new stock items should have been created
        self.assertEqual(base_part.stock_entries().count(), N_ITEMS)
        self.assertEqual(base_part.get_stock_count(), N_STOCK)

        # Check that the line item has been fully received
        line.refresh_from_db()
        self.assertEqual(line.received, line.quantity)


class SalesOrderTest(OrderTest):
    """Tests for the SalesOrder API."""

    LIST_URL = reverse('api-so-list')

    def test_so_list(self):
        """Test the SalesOrder list API endpoint."""
        # All orders
        self.filter({}, 6)

        # Filter by customer
        self.filter({'customer': 4}, 3)
        self.filter({'customer': 5}, 3)

        # Filter by outstanding
        self.filter({'outstanding': True}, 4)
        self.filter({'outstanding': False}, 2)

        # Filter by status
        self.filter({'status': SalesOrderStatus.PENDING.value}, 3)
        self.filter({'status': SalesOrderStatus.SHIPPED.value}, 1)
        self.filter({'status': SalesOrderStatus.COMPLETE.value}, 1)
        self.filter({'status': SalesOrderStatus.CANCELLED.value}, 0)
        self.filter({'status': 99}, 0)  # Invalid

        # Filter by "reference"
        self.filter({'reference': 'ABC123'}, 1)
        self.filter({'reference': 'XXX999'}, 0)

        # Filter by "assigned_to_me"
        self.filter({'assigned_to_me': 1}, 0)
        self.filter({'assigned_to_me': 0}, 6)

    def test_total_price(self):
        """Unit tests for the 'total_price' field."""
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
                    models.SalesOrder(customer=customer, reference=f'SO-{idx + 100}')
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
                        sale_price=Money((idx + 1) / 5, currencies[idx % n]),
                    )
                )

                idx += 1

            # Create some extra lines against this order
            for _ in range(3):
                extra_lines.append(
                    models.SalesOrderExtraLine(
                        order=so, quantity=(idx + 2) % 10, price=Money(10, 'CAD')
                    )
                )

        models.SalesOrderLineItem.objects.bulk_create(lines)
        models.SalesOrderExtraLine.objects.bulk_create(extra_lines)

        # List all SalesOrder objects and count queries
        for limit in [1, 5, 10, 100]:
            with CaptureQueriesContext(connection) as ctx:
                response = self.get(
                    self.LIST_URL, data={'limit': limit}, expected_code=200
                )

                # Total database queries must be less than 25
                self.assertLess(len(ctx), 25)

                n = len(response.data['results'])

                for result in response.data['results']:
                    self.assertIn('total_price', result)
                    self.assertIn('order_currency', result)

    def test_overdue(self):
        """Test "overdue" status."""
        self.filter({'overdue': True}, 0)
        self.filter({'overdue': False}, 6)

        for pk in [1, 2]:
            order = models.SalesOrder.objects.get(pk=pk)
            order.target_date = datetime.now().date() - timedelta(days=10)
            order.save()

        self.filter({'overdue': True}, 2)
        self.filter({'overdue': False}, 4)

    def test_so_detail(self):
        """Test the SalesOrder detail endpoint."""
        url = '/api/order/so/1/'

        response = self.get(url)

        data = response.data

        self.assertEqual(data['pk'], 1)

    def test_so_attachments(self):
        """Test the list endpoint for the SalesOrderAttachment model."""
        url = reverse('api-attachment-list')

        # Filter by 'salesorder'
        self.get(
            url, data={'model_type': 'salesorder', 'model_id': 1}, expected_code=200
        )

    def test_so_operations(self):
        """Test that we can create / edit and delete a SalesOrder via the API."""
        n = models.SalesOrder.objects.count()

        url = reverse('api-so-list')

        # Initially we do not have "add" permission for the SalesOrder model,
        # so this POST request should return 403 (denied)
        response = self.post(
            url,
            {'customer': 4, 'reference': '12345', 'description': 'Sales order'},
            expected_code=403,
        )

        self.assignRole('sales_order.add')

        # Now we should be able to create a SalesOrder via the API
        response = self.post(
            url,
            {'customer': 4, 'reference': 'SO-12345', 'description': 'Sales order'},
            expected_code=201,
        )

        # Check that the new order has been created
        self.assertEqual(models.SalesOrder.objects.count(), n + 1)

        # Grab the PK for the newly created SalesOrder
        pk = response.data['pk']

        # Basic checks against the newly created SalesOrder
        so = models.SalesOrder.objects.get(pk=pk)
        self.assertEqual(so.reference, 'SO-12345')
        self.assertEqual(so.created_by.username, 'testuser')

        # Try to create a SO with identical reference (should fail)
        response = self.post(
            url,
            {
                'customer': 4,
                'reference': 'SO-12345',
                'description': 'Another sales order',
            },
            expected_code=400,
        )

        url = reverse('api-so-detail', kwargs={'pk': pk})

        # Extract detail info for the SalesOrder
        response = self.get(url)
        self.assertEqual(response.data['reference'], 'SO-12345')

        # Try to alter (edit) the SalesOrder
        # Initially try with an invalid reference field value
        response = self.patch(url, {'reference': 'SO-12345-a'}, expected_code=400)

        response = self.patch(url, {'reference': 'SO-12346'}, expected_code=200)

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

        self.assertIn(
            'Reference must match required pattern', str(response.data['reference'])
        )

        self.post(
            url,
            {
                'reference': 'SO-12345',
                'customer': 4,
                'description': 'A better test sales order',
            },
            expected_code=201,
        )

    def test_so_duplicate(self):
        """Test SalesOrder duplication via the API."""
        from common.models import Parameter, ParameterTemplate

        url = reverse('api-so-list')

        self.assignRole('sales_order.add')

        so = models.SalesOrder.objects.get(pk=1)
        self.assertEqual(so.status, SalesOrderStatus.PENDING)

        # Add some parameters to the sales order
        for idx in range(5):
            template = ParameterTemplate.objects.create(name=f'Template {idx}')

            Parameter.objects.create(
                template=template,
                model_type=so.get_content_type(),
                model_id=so.pk,
                data=f'Value {idx}',
            )

        self.assertEqual(so.parameters.count(), 5)

        # Create a duplicate of this sales order
        # We explicitly specify "copy_parameters" as False, so the duplicated sales order should not have any parameters
        response = self.post(
            url,
            {
                'reference': 'SO-12345',
                'customer': so.customer.pk,
                'duplicate': {'original': so.pk, 'copy_parameters': False},
            },
        )

        duplicate_id = response.data['pk']
        duplicate_so = models.SalesOrder.objects.get(pk=duplicate_id)

        self.assertEqual(duplicate_so.reference, 'SO-12345')
        self.assertEqual(duplicate_so.customer, so.customer)
        self.assertEqual(duplicate_so.parameters.count(), 0)

        # Duplicate again, with default values for the "duplicate" options (which should result in parameters being copied)
        response = self.post(
            url,
            {
                'reference': 'SO-12346',
                'customer': so.customer.pk,
                'duplicate': {'original': so.pk},
            },
        )

        duplicate_id = response.data['pk']
        duplicate_so = models.SalesOrder.objects.get(pk=duplicate_id)

        self.assertEqual(duplicate_so.reference, 'SO-12346')
        self.assertEqual(duplicate_so.customer, so.customer)
        self.assertEqual(duplicate_so.parameters.count(), 5)

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
        """Test the calendar export endpoint."""
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
                expected_code=201,
            )

        # Cancel a few orders - these will not show in incomplete view below
        for so in models.SalesOrder.objects.filter(target_date__isnull=False):
            if so.reference in [
                'SO-11000006',
                'SO-11000007',
                'SO-11000008',
                'SO-11000009',
            ]:
                self.post(
                    reverse('api-so-cancel', kwargs={'pk': so.pk}), expected_code=201
                )

        url = reverse('api-po-so-calendar', kwargs={'ordertype': 'sales-order'})

        # Test without completed orders
        response = self.get(url, expected_code=200, format=None)

        number_orders = len(
            models.SalesOrder.objects.filter(target_date__isnull=False).filter(
                status__lt=SalesOrderStatus.SHIPPED.value
            )
        )

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
        response = self.get(
            url, data={'include_completed': 'True'}, expected_code=200, format=None
        )

        number_orders_incl_complete = len(
            models.SalesOrder.objects.filter(target_date__isnull=False)
        )
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
        """Test we can export the SalesOrder list."""
        set_global_setting(models.SalesOrder.UNLOCK_SETTING, True)

        n = models.SalesOrder.objects.count()

        # Check there are some sales orders
        self.assertGreater(n, 0)

        for order in models.SalesOrder.objects.all():
            # Reconstruct the total price
            order.save()

        # Download file, check we get a 200 response
        for fmt in ['csv', 'xlsx', 'tsv']:
            self.export_data(
                reverse('api-so-list'),
                export_format=fmt,
                decode=fmt == 'csv',
                expected_code=200,
                expected_fn=r'InvenTree_SalesOrder_.+',
            )

    def test_sales_order_complete(self):
        """Tests for marking a SalesOrder as complete."""
        self.assignRole('sales_order.add')

        # Let's create a SalesOrder
        customer = Company.objects.filter(is_customer=True).first()
        so = models.SalesOrder.objects.create(
            customer=customer, reference='SO-12345', description='Test SO'
        )

        self.assertEqual(so.status, SalesOrderStatus.PENDING.value)

        # Create a line item
        part = Part.objects.filter(salable=True).first()

        line = models.SalesOrderLineItem.objects.create(
            order=so, part=part, quantity=10, sale_price=Money(10, 'USD')
        )

        shipment = so.shipments.first()

        if shipment is None:
            shipment = models.SalesOrderShipment.objects.create(
                order=so, reference='SHIP-12345'
            )
        assert shipment

        # Allocate some stock
        item = StockItem.objects.create(part=part, quantity=100, location=None)
        models.SalesOrderAllocation.objects.create(
            quantity=10, line=line, item=item, shipment=shipment
        )

        # Ship the shipment
        shipment.complete_shipment(self.user)

        # Ok, now we should be able to "complete" the shipment via the API
        # The 'SALESORDER_SHIP_COMPLETE' setting determines if the outcome is "SHIPPED" or "COMPLETE"
        InvenTreeSetting.set_setting('SALESORDER_SHIP_COMPLETE', False)

        url = reverse('api-so-complete', kwargs={'pk': so.pk})
        self.post(url, {}, expected_code=201)

        so.refresh_from_db()
        self.assertEqual(so.status, SalesOrderStatus.SHIPPED.value)
        self.assertIsNotNone(so.shipment_date)
        self.assertIsNotNone(so.shipped_by)

        # Now, let's try to "complete" the shipment again
        # This time it should get marked as "COMPLETE"
        self.post(url, {}, expected_code=201)

        so.refresh_from_db()
        self.assertEqual(so.status, SalesOrderStatus.COMPLETE.value)

        # Now, let's try *again* (it should fail as the order is already complete)
        response = self.post(url, {}, expected_code=400)

        self.assertIn('Order is already complete', str(response.data))

        # Next, we'll change the setting so that the order status jumps straight to "complete"
        so.status = SalesOrderStatus.PENDING.value
        so.shipment_date = None
        so.shipped_by = None
        so.save()
        so.refresh_from_db()

        self.assertEqual(so.status, SalesOrderStatus.PENDING.value)
        self.assertIsNone(so.shipped_by)
        self.assertIsNone(so.shipment_date)

        InvenTreeSetting.set_setting('SALESORDER_SHIP_COMPLETE', True)

        self.post(url, {}, expected_code=201)

        # The orders status should now be "complete" (not "shipped")
        so.refresh_from_db()
        self.assertEqual(so.status, SalesOrderStatus.COMPLETE.value)

        self.assertIsNotNone(so.shipment_date)
        self.assertIsNotNone(so.shipped_by)

    def test_output_options(self):
        """Test the output options for the SalesOrder detail endpoint."""
        self.run_output_test(
            reverse('api-so-detail', kwargs={'pk': 1}), ['customer_detail']
        )

    def test_so_custom_status_query_count(self):
        """Test that listing SalesOrders with custom statuses does not cause N+1 queries.

        Ensures that resolving the 'status_text' field for custom status values
        is O(1) in database queries, not O(N) relative to the number of results.
        """
        so_content_type = ContentType.objects.get_for_model(models.SalesOrder)

        logical_keys = [
            SalesOrderStatus.PENDING.value,
            SalesOrderStatus.IN_PROGRESS.value,
            SalesOrderStatus.SHIPPED.value,
            SalesOrderStatus.ON_HOLD.value,
            SalesOrderStatus.COMPLETE.value,
            SalesOrderStatus.CANCELLED.value,
            SalesOrderStatus.PENDING.value,
            SalesOrderStatus.IN_PROGRESS.value,
            SalesOrderStatus.SHIPPED.value,
            SalesOrderStatus.ON_HOLD.value,
        ]

        custom_statuses = [
            InvenTreeCustomUserStateModel.objects.create(
                key=2000 + i,
                name=f'SoCustomStatus{i}',
                label=f'SO Custom Status Label {i}',
                color='secondary',
                logical_key=logical_keys[i],
                model=so_content_type,
                reference_status='SalesOrderStatus',
            )
            for i in range(10)
        ]

        customer = Company.objects.filter(is_customer=True).first()
        models.SalesOrder.objects.bulk_create([
            models.SalesOrder(
                customer=customer,
                reference=f'SO-QTEST-{i}',
                status=custom_statuses[i % 10].logical_key,
                status_custom_key=custom_statuses[i % 10].key,
            )
            for i in range(100)
        ])

        for limit in [1, 5, 10, 25, 50, 100]:
            response = self.get(
                self.LIST_URL,
                data={'limit': limit},
                expected_code=200,
                max_query_count=50,
            )

            for result in response.data['results']:
                self.assertIn('status_text', result)
                self.assertIsNotNone(result['status_text'])


class SalesOrderLineItemTest(OrderTest):
    """Tests for the SalesOrderLineItem API."""

    LIST_URL = reverse('api-so-line-list')

    @classmethod
    def setUpTestData(cls):
        """Init routine for this unit test class."""
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
                        reference=f'Order {so.reference} - line {idx}',
                    )
                )

        # Bulk create
        models.SalesOrderLineItem.objects.bulk_create(lines)

        cls.url = reverse('api-so-line-list')

    def test_so_line_list(self):
        """Test list endpoint."""
        response = self.get(self.url, {}, expected_code=200)

        n = models.SalesOrderLineItem.objects.count()

        # We should have received *all* lines
        self.assertEqual(len(response.data), n)

        # List *all* lines, but paginate
        response = self.get(self.url, {'limit': 5}, expected_code=200)

        self.assertEqual(response.data['count'], n)
        self.assertEqual(len(response.data['results']), 5)

        n_orders = models.SalesOrder.objects.count()
        n_parts = Part.objects.filter(salable=True).count()

        # List by part
        for part in Part.objects.filter(salable=True)[:3]:
            response = self.get(self.url, {'part': part.pk, 'limit': 10})

            self.assertEqual(response.data['count'], n_orders)

        # List by order
        for order in models.SalesOrder.objects.all()[:3]:
            response = self.get(self.url, {'order': order.pk, 'limit': 10})

            self.assertEqual(response.data['count'], n_parts)

        # Filter by has_pricing status
        self.filter({'has_pricing': 1}, 0)
        self.filter({'has_pricing': 0}, n)

        # Filter by 'completed' status
        self.filter({'completed': 1}, 0)
        self.filter({'completed': 0}, n)

        # Filter by 'allocated' status
        self.filter({'allocated': 'true'}, 1)
        self.filter({'allocated': 'false'}, n - 1)

    def test_so_line_bulk_delete(self):
        """Test that we can bulk delete multiple SalesOrderLineItems via the API."""
        n = models.SalesOrderLineItem.objects.count()

        items = list(models.SalesOrderLineItem.objects.values_list('pk', flat=True)[:2])

        # Deletion should fail without the correct role
        self.delete(self.url, {'items': items}, expected_code=403)

        self.assignRole('sales_order.delete')

        self.delete(self.url, {'items': items}, expected_code=200)

        # We should have 2 less SalesOrderLineItems after deleting them
        self.assertEqual(models.SalesOrderLineItem.objects.count(), n - 2)

    def test_so_extra_line_bulk_delete(self):
        """Test that we can bulk delete multiple SalesOrderExtraLine items via the API."""
        so = models.SalesOrder.objects.first()

        models.SalesOrderExtraLine.objects.bulk_create([
            models.SalesOrderExtraLine(
                order=so, quantity=idx + 1, reference=f'Extra line {idx}'
            )
            for idx in range(3)
        ])

        n = models.SalesOrderExtraLine.objects.count()
        items = list(
            models.SalesOrderExtraLine.objects.values_list('pk', flat=True)[:2]
        )

        url = reverse('api-so-extra-line-list')

        # Deletion should fail without the correct role
        self.delete(url, {'items': items}, expected_code=403)

        self.assignRole('sales_order.delete')

        self.delete(url, {'items': items}, expected_code=200)

        self.assertEqual(models.SalesOrderExtraLine.objects.count(), n - 2)

    def test_so_line_allocated_filters(self):
        """Test filtering by allocation status for a SalesOrderLineItem."""
        self.assignRole('sales_order.add')

        # Crete a new SalesOrder via the API
        company = Company.objects.filter(is_customer=True).first()
        assert company

        response = self.post(
            reverse('api-so-list'),
            {
                'customer': company.pk,
                'reference': 'SO-12345',
                'description': 'Test Sales Order',
            },
        )

        order_id = response.data['pk']
        order = models.SalesOrder.objects.get(pk=order_id)

        so_line_url = reverse('api-so-line-list')

        # Initially, there should be no line items against this order
        response = self.get(so_line_url, {'order': order_id})

        self.assertEqual(len(response.data), 0)

        parts = [25, 50, 100]

        # Let's create some new line items
        for part_id in parts:
            self.post(so_line_url, {'order': order_id, 'part': part_id, 'quantity': 10})

        # Should be three items now
        response = self.get(so_line_url, {'order': order_id})

        self.assertEqual(len(response.data), 3)

        for item in response.data:
            # Check that the line item has been created
            self.assertEqual(item['order'], order_id)

            # Check that the line quantities are correct
            self.assertEqual(item['quantity'], 10)
            self.assertEqual(item['allocated'], 0)
            self.assertEqual(item['shipped'], 0)

        # Initial API filters should return no results
        self.filter({'order': order_id, 'allocated': 1}, 0)
        self.filter({'order': order_id, 'completed': 1}, 0)

        # Create a new shipment against this SalesOrder
        shipment = models.SalesOrderShipment.objects.create(
            order=order, reference='SHIP-12345'
        )

        # Next, allocate stock against 2 line items
        for item in parts[:2]:
            p = Part.objects.get(pk=item)
            s = StockItem.objects.create(part=p, quantity=100)
            l = models.SalesOrderLineItem.objects.filter(order=order, part=p).first()
            assert l

            # Allocate against the API
            self.post(
                reverse('api-so-allocate', kwargs={'pk': order.pk}),
                {
                    'items': [{'line_item': l.pk, 'stock_item': s.pk, 'quantity': 10}],
                    'shipment': shipment.pk,
                },
            )

        # Filter by 'fully allocated' status
        self.filter({'order': order_id, 'allocated': 1}, 2)
        self.filter({'order': order_id, 'allocated': 0}, 1)

        self.filter({'order': order_id, 'completed': 1}, 0)
        self.filter({'order': order_id, 'completed': 0}, 3)

        # Finally, mark this shipment as 'shipped'
        self.post(
            reverse('api-so-shipment-ship', kwargs={'pk': shipment.pk}),
            {},
            expected_code=200,
        )

        # Filter by 'completed' status
        self.filter({'order': order_id, 'completed': 1}, 2)
        self.filter({'order': order_id, 'completed': 0}, 1)

    def test_output_options(self):
        """Test the various output options for the SalesOrderLineItem detail endpoint."""
        self.run_output_test(
            reverse('api-so-line-detail', kwargs={'pk': 1}),
            ['part_detail', 'order_detail', 'customer_detail'],
        )


class SalesOrderDownloadTest(OrderTest):
    """Unit tests for downloading SalesOrder data via the API endpoint."""

    def test_download_fail(self):
        """Test that downloading without the 'export' option fails."""
        url = reverse('api-so-list')

        response = self.export_data(url, export_plugin='no-plugin', expected_code=400)
        self.assertIn('is not a valid choice', str(response['export_plugin']))

    def test_download_xlsx(self):
        """Test xlsx file download."""
        url = reverse('api-so-list')

        # Download .xls file
        with self.export_data(
            url, export_format='xlsx', expected_code=200, decode=False
        ) as file:
            self.assertIsInstance(file, io.BytesIO)

    def test_download_csv(self):
        """Test that the list of sales orders can be downloaded as a .csv file."""
        url = reverse('api-so-list')

        required_cols = [
            'Line Items',
            'ID',
            'Reference',
            'Customer',
            'Order Status',
            'Shipment Date',
            'Description',
            'Project Code',
            'Responsible',
        ]

        excluded_cols = ['metadata']

        # Download .xls file
        with self.export_data(url, export_format='csv') as file:
            data = self.process_csv(
                file,
                required_cols=required_cols,
                excluded_cols=excluded_cols,
                required_rows=models.SalesOrder.objects.count(),
            )

            for line in data:
                order = models.SalesOrder.objects.get(pk=line['ID'])

                self.assertEqual(line['Description'], order.description)
                self.assertEqual(line['Order Status'], str(order.status))

        # Download only outstanding sales orders
        with self.export_data(url, {'outstanding': True}, export_format='tsv') as file:
            self.process_csv(
                file,
                required_cols=required_cols,
                excluded_cols=excluded_cols,
                required_rows=models.SalesOrder.objects.filter(
                    status__in=SalesOrderStatusGroups.OPEN
                ).count(),
                delimiter='\t',
            )


class SalesOrderAllocateTest(OrderTest):
    """Unit tests for allocating stock items against a SalesOrder."""

    @classmethod
    def setUpTestData(cls):
        """Init routine for this unit test class."""
        super().setUpTestData()

    def setUp(self):
        """Init routines for this unit testing class."""
        super().setUp()

        self.assignRole('sales_order.add')

        self.url = reverse('api-so-allocate', kwargs={'pk': 1})

        self.order = models.SalesOrder.objects.get(pk=1)

        # Create some line items for this purchase order
        parts = Part.objects.filter(salable=True)

        for part in parts:
            # Create a new line item
            models.SalesOrderLineItem.objects.create(
                order=self.order, part=part, quantity=5
            )

            # Ensure we have stock!
            StockItem.objects.create(part=part, quantity=100)

        # Create a new shipment against this SalesOrder
        self.shipment = models.SalesOrderShipment.objects.create(order=self.order)

    def test_invalid(self):
        """Test POST with invalid data."""
        # No data
        response = self.post(self.url, {}, expected_code=400)

        self.assertIn('This field is required', str(response.data['items']))

        # Test with a single line items
        line = self.order.lines.first()
        part = line.part

        # Valid stock_item, but quantity is invalid
        data = {
            'items': [
                {
                    'line_item': line.pk,
                    'stock_item': part.stock_items.last().pk,
                    'quantity': 0,
                }
            ]
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
            order=models.SalesOrder.objects.get(pk=2)
        )

        data['shipment'] = shipment.pk

        response = self.post(self.url, data, expected_code=400)

        self.assertIn(
            'Shipment is not associated with this order', str(response.data['shipment'])
        )

    def test_allocate(self):
        """Test that the allocation endpoint acts as expected, when provided with valid data!"""
        # First, check that there are no line items allocated against this SalesOrder
        self.assertEqual(self.order.stock_allocations.count(), 0)

        data = {'items': [], 'shipment': self.shipment.pk}

        for line in self.order.lines.all():
            for stock_item in line.part.stock_items.all():
                # Find a non-serialized stock item to allocate
                if not stock_item.serialized:
                    break

            # Fully-allocate each line
            data['items'].append({
                'line_item': line.pk,
                'stock_item': stock_item.pk,
                'quantity': 5,
            })

        self.post(self.url, data, expected_code=201)

        # There should have been 1 stock item allocated against each line item
        n_lines = self.order.lines.count()

        self.assertEqual(self.order.stock_allocations.count(), n_lines)

        for line in self.order.lines.all():
            self.assertEqual(line.allocations.count(), 1)

    def test_allocate_variant(self):
        """Test that the allocation endpoint acts as expected, when provided with variant."""
        # First, check that there are no line items allocated against this SalesOrder
        self.assertEqual(self.order.stock_allocations.count(), 0)

        data = {'items': [], 'shipment': self.shipment.pk}

        def check_template(line_item):
            return line_item.part.is_template

        for line in filter(check_template, self.order.lines.all()):
            stock_item: Optional[StockItem] = None

            stock_item = None

            # Allocate a matching variant
            parts: list[Part] = Part.objects.filter(salable=True).filter(
                variant_of=line.part.pk
            )
            for part in parts:
                stock_item = part.stock_items.last()

                for item in part.stock_items.all():
                    if item.serialized:
                        continue

                    stock_item = item
                    break

                if stock_item is not None:
                    break

            if stock_item is None:
                raise self.fail('No stock item found for part')  # pragma: no cover

            # Fully-allocate each line
            data['items'].append({
                'line_item': line.pk,
                'stock_item': stock_item.pk,
                'quantity': 5,
            })

        self.post(self.url, data, expected_code=201)

        # At least one item should be allocated, and all should be variants
        self.assertGreater(self.order.stock_allocations.count(), 0)
        for allocation in self.order.stock_allocations.all():
            self.assertNotEqual(allocation.item.part.pk, allocation.line.part.pk)

    def test_shipment_complete(self):
        """Test that we can complete a shipment via the API."""
        url = reverse('api-so-shipment-ship', kwargs={'pk': self.shipment.pk})

        self.assertFalse(self.shipment.is_complete())
        self.assertFalse(self.shipment.check_can_complete(raise_error=False))

        with self.assertRaises(ValidationError):
            self.shipment.check_can_complete()

        # Attempting to complete this shipment via the API should fail
        response = self.post(url, {}, expected_code=400)

        self.assertIn('Shipment has no allocated stock items', str(response.data))

        # Allocate stock against this shipment
        line = self.order.lines.first()
        part = line.part

        models.SalesOrderAllocation.objects.create(
            shipment=self.shipment, line=line, item=part.stock_items.last(), quantity=5
        )

        # Shipment should now be able to be completed
        self.assertTrue(self.shipment.check_can_complete())

        # Attempt with an invalid date
        response = self.post(url, {'shipment_date': 'asfasd'}, expected_code=400)

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
            expected_code=200,
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
        response = self.patch(url, {'delivery_date': None}, expected_code=200)

        # Shipment should not be marked as delivered
        self.assertFalse(self.shipment.is_delivered())

        # Attempt to set delivery date
        response = self.patch(url, {'delivery_date': 'asfasd'}, expected_code=400)

        self.assertIn('Date has wrong format', str(response.data))

        response = self.patch(url, {'delivery_date': '2023-05-15'}, expected_code=200)
        self.shipment.refresh_from_db()

        # Shipment should now be marked as delivered
        self.assertTrue(self.shipment.is_delivered())
        self.assertEqual(self.shipment.delivery_date, datetime(2023, 5, 15).date())

    def test_sales_order_shipment_list(self):
        """Test the SalesOrderShipment list API endpoint."""
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
                        'reference': f'SH{idx + 1}',
                        'tracking_number': f'TRK_{order.pk}_{idx}',
                    },
                    expected_code=201,
                )

            # Filter API by order
            response = self.get(url, {'order': order.pk}, expected_code=200)

            # 3 shipments returned for each SalesOrder instance
            self.assertGreaterEqual(len(response.data), 3)

        # List *all* shipments
        response = self.get(url, expected_code=200)

        self.assertEqual(
            len(response.data), count_before + 3 * models.SalesOrder.objects.count()
        )

    def test_output_options(self):
        """Test the various output options for the SalesOrderAllocation detail endpoint."""
        self.run_output_test(
            reverse('api-so-allocation-list'),
            [
                'part_detail',
                'item_detail',
                'order_detail',
                'location_detail',
                'customer_detail',
            ],
            assert_subset=True,
        )

    def test_block_on_required_tests(self):
        """Test the SALESORDER_BLOCK_INCOMPLETE_ITEM_TESTS setting."""
        from part.models import PartTestTemplate

        line = self.order.lines.first()
        part = line.part

        # Make this a testable part
        part.testable = True
        part.save()

        # Create a required test
        PartTestTemplate.objects.create(
            part=part, test_name='A required test', required=True
        )

        data = {
            'items': [
                {
                    'line_item': line.pk,
                    'stock_item': part.stock_items.last().pk,
                    'quantity': line.quantity,
                }
            ]
        }

        set_global_setting('SALESORDER_BLOCK_INCOMPLETE_ITEM_TESTS', True)

        response = self.post(self.url, data, expected_code=400)
        self.assertIn(
            'Stock item has not passed all required tests', str(response.data)
        )

        set_global_setting('SALESORDER_BLOCK_INCOMPLETE_ITEM_TESTS', False)

        response = self.post(self.url, data, expected_code=201)


class SalesOrderAllocationDownloadTest(OrderTest):
    """Unit tests for downloading SalesOrderAllocation data via the API endpoint."""

    def test_download_csv(self):
        """Test that SalesOrderAllocation data can be downloaded as a .csv file.

        Regression test for a bug where the SalesOrderAllocation list endpoint
        did not support data export.
        """
        url = reverse('api-so-allocation-list')

        required_cols = ['ID', 'Item', 'Quantity', 'Shipment', 'Line', 'Part', 'Order']

        with self.export_data(url, export_format='csv', expected_code=200) as file:
            data = self.process_csv(
                file,
                required_cols=required_cols,
                required_rows=SalesOrderAllocation.objects.count(),
            )

            for row in data:
                allocation = SalesOrderAllocation.objects.get(pk=row['ID'])

                self.assertEqual(row['Item'], str(allocation.item.pk))
                self.assertEqual(row['Quantity'], str(allocation.quantity))
                self.assertEqual(row['Line'], str(allocation.line.pk))
                self.assertEqual(row['Part'], str(allocation.item.part.pk))
                self.assertEqual(row['Order'], str(allocation.line.order.pk))


class SalesOrderAllocateSerialsTest(OrderTest):
    """Unit tests for allocating stock items against a SalesOrder, by serial number."""

    @classmethod
    def setUpTestData(cls):
        """Init routine for this unit test class."""
        super().setUpTestData()

    def setUp(self):
        """Init routines for this unit testing class."""
        super().setUp()

        self.assignRole('sales_order.add')

        self.url = reverse('api-so-allocate-serials', kwargs={'pk': 1})

        self.order = models.SalesOrder.objects.get(pk=1)

        self.part = Part.objects.create(
            name='Serial Allocation Part',
            salable=True,
            trackable=True,
            description='A trackable part for serial allocation tests',
        )

        self.line = models.SalesOrderLineItem.objects.create(
            order=self.order, part=self.part, quantity=5
        )

        # Create some serialized stock items for this part
        self.stock_items = [
            StockItem.objects.create(part=self.part, quantity=1, serial=str(n))
            for n in range(1, 6)
        ]

        self.shipment = models.SalesOrderShipment.objects.create(order=self.order)

    def test_allocate(self):
        """Test that we can allocate stock items to a SalesOrder line, by serial number."""
        self.assertEqual(self.order.stock_allocations.count(), 0)

        data = {'line_item': self.line.pk, 'quantity': 3, 'serial_numbers': '1,2,3'}

        self.post(self.url, data, expected_code=201)

        self.assertEqual(self.order.stock_allocations.count(), 3)

        allocated_serials = {
            allocation.item.serial for allocation in self.order.stock_allocations.all()
        }
        self.assertEqual(allocated_serials, {'1', '2', '3'})

        for allocation in self.order.stock_allocations.all():
            self.assertEqual(allocation.quantity, 1)
            self.assertIsNone(allocation.shipment)

    def test_allocate_with_shipment(self):
        """Test that allocations are correctly assigned to a provided shipment."""
        data = {
            'line_item': self.line.pk,
            'quantity': 2,
            'serial_numbers': '4,5',
            'shipment': self.shipment.pk,
        }

        self.post(self.url, data, expected_code=201)

        for allocation in self.order.stock_allocations.all():
            self.assertEqual(allocation.shipment, self.shipment)

    def test_invalid_line_item(self):
        """Test that a line item belonging to a different order is rejected."""
        other_order = models.SalesOrder.objects.exclude(pk=self.order.pk).first()
        other_line = models.SalesOrderLineItem.objects.create(
            order=other_order, part=self.part, quantity=5
        )

        data = {'line_item': other_line.pk, 'quantity': 1, 'serial_numbers': '1'}

        response = self.post(self.url, data, expected_code=400)

        self.assertIn('Line item is not associated with this order', str(response.data))

        self.assertEqual(self.order.stock_allocations.count(), 0)

    def test_shipment_already_shipped(self):
        """Test that a shipment which has already been shipped is rejected."""
        self.shipment.shipment_date = date.today()
        self.shipment.save()

        data = {
            'line_item': self.line.pk,
            'quantity': 1,
            'serial_numbers': '1',
            'shipment': self.shipment.pk,
        }

        response = self.post(self.url, data, expected_code=400)

        self.assertIn('Shipment has already been shipped', str(response.data))

        self.assertEqual(self.order.stock_allocations.count(), 0)

    def test_shipment_wrong_order(self):
        """Test that a shipment belonging to a different order is rejected."""
        other_order = models.SalesOrder.objects.exclude(pk=self.order.pk).first()
        other_shipment = models.SalesOrderShipment.objects.create(order=other_order)

        data = {
            'line_item': self.line.pk,
            'quantity': 1,
            'serial_numbers': '1',
            'shipment': other_shipment.pk,
        }

        response = self.post(self.url, data, expected_code=400)

        self.assertIn('Shipment is not associated with this order', str(response.data))

        self.assertEqual(self.order.stock_allocations.count(), 0)

    def test_serial_not_exist(self):
        """Test that non-existent serial numbers are rejected."""
        data = {'line_item': self.line.pk, 'quantity': 1, 'serial_numbers': '999'}

        response = self.post(self.url, data, expected_code=400)

        self.assertIn(
            'No match found for the following serial numbers', str(response.data)
        )
        self.assertIn('999', str(response.data))

        self.assertEqual(self.order.stock_allocations.count(), 0)

    def test_serial_unavailable(self):
        """Test that an already-allocated serial number is rejected as unavailable."""
        # Fully allocate stock item with serial '1' against some other line
        models.SalesOrderAllocation.objects.create(
            line=self.line, item=self.stock_items[0], quantity=1
        )

        data = {'line_item': self.line.pk, 'quantity': 1, 'serial_numbers': '1'}

        response = self.post(self.url, data, expected_code=400)

        self.assertIn(
            'The following serial numbers are unavailable', str(response.data)
        )
        self.assertIn('1', str(response.data))

        # No *additional* allocation should have been created
        self.assertEqual(self.order.stock_allocations.count(), 1)

    def test_block_on_required_tests(self):
        """Test the SALESORDER_BLOCK_INCOMPLETE_ITEM_TESTS setting."""
        from part.models import PartTestTemplate

        self.part.testable = True
        self.part.save()

        PartTestTemplate.objects.create(
            part=self.part, test_name='A required test', required=True
        )

        data = {'line_item': self.line.pk, 'quantity': 1, 'serial_numbers': '1'}

        set_global_setting('SALESORDER_BLOCK_INCOMPLETE_ITEM_TESTS', True)

        response = self.post(self.url, data, expected_code=400)
        self.assertIn(
            'The following serial numbers are unavailable', str(response.data)
        )

        set_global_setting('SALESORDER_BLOCK_INCOMPLETE_ITEM_TESTS', False)

        self.post(self.url, data, expected_code=201)


class ReturnOrderTests(InvenTreeAPITestCase):
    """Unit tests for ReturnOrder API endpoints."""

    fixtures = [
        'category',
        'company',
        'return_order',
        'part',
        'location',
        'supplier_part',
        'stock',
    ]
    roles = ['return_order.view']

    def test_options(self):
        """Test the OPTIONS endpoint."""
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

    def test_project_code(self):
        """Test the 'project_code' serializer field."""
        self.assignRole('return_order.add')
        response = self.options(reverse('api-return-order-list'), expected_code=200)
        project_code = response.data['actions']['POST']['project_code']

        self.assertFalse(project_code['required'])
        self.assertFalse(project_code['read_only'])
        self.assertEqual(project_code['type'], 'related field')
        self.assertEqual(project_code['label'], 'Project Code')
        self.assertEqual(project_code['model'], 'projectcode')

    def test_list(self):
        """Tests for the list endpoint."""
        url = reverse('api-return-order-list')

        response = self.get(url, expected_code=200)

        self.assertEqual(len(response.data), 6)

        # Paginated query
        data = self.get(
            url,
            {'limit': 1, 'ordering': 'reference', 'customer_detail': True},
            expected_code=200,
        ).data

        self.assertEqual(data['count'], 6)
        self.assertEqual(len(data['results']), 1)
        result = data['results'][0]
        self.assertEqual(result['reference'], 'RMA-001')
        self.assertEqual(result['customer_detail']['name'], 'A customer')

        # Reverse ordering
        data = self.get(url, {'ordering': '-reference'}, expected_code=200).data

        self.assertEqual(data[0]['reference'], 'RMA-006')

        # Filter by customer
        for cmp_id in [4, 5]:
            data = self.get(url, {'customer': cmp_id}, expected_code=200).data

            self.assertEqual(len(data), 3)

            for result in data:
                self.assertEqual(result['customer'], cmp_id)

        # Filter by status
        data = self.get(
            url, {'status': ReturnOrderStatus.IN_PROGRESS.value}, expected_code=200
        ).data

        self.assertEqual(len(data), 2)

        for result in data:
            self.assertEqual(result['status'], 20)

    def test_create(self):
        """Test creation of ReturnOrder via the API."""
        url = reverse('api-return-order-list')

        # Do not have required permissions yet
        self.post(
            url, {'customer': 1, 'description': 'a return order'}, expected_code=403
        )

        self.assignRole('return_order.add')

        data = self.post(
            url,
            {
                'customer': 4,
                'customer_reference': 'cr',
                'description': 'a return order',
            },
            expected_code=201,
        ).data

        # Reference automatically generated
        self.assertEqual(data['reference'], 'RMA-0007')
        self.assertEqual(data['customer_reference'], 'cr')

    def test_update(self):
        """Test that we can update a ReturnOrder via the API."""
        url = reverse('api-return-order-detail', kwargs={'pk': 1})

        # Test detail endpoint
        data = self.get(url, expected_code=200).data

        self.assertEqual(data['reference'], 'RMA-001')

        # Attempt to update, incorrect permissions
        self.patch(
            url, {'customer_reference': 'My customer reference'}, expected_code=403
        )

        self.assignRole('return_order.change')

        self.patch(url, {'customer_reference': 'customer ref'}, expected_code=200)

        rma = models.ReturnOrder.objects.get(pk=1)
        self.assertEqual(rma.customer_reference, 'customer ref')

    def test_ro_issue(self):
        """Test the 'issue' order for a ReturnOrder."""
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
        """Test that we can receive items against a ReturnOrder."""
        customer = Company.objects.get(pk=4)

        # Create an order
        rma = models.ReturnOrder.objects.create(
            customer=customer, description='A return order'
        )

        self.assertEqual(rma.reference, 'RMA-0007')

        # Create some line items
        part = Part.objects.get(pk=25)
        for idx in range(3):
            stock_item = StockItem.objects.create(
                part=part, customer=customer, quantity=1, serial=idx
            )

            line_item = models.ReturnOrderLineItem.objects.create(
                order=rma, item=stock_item
            )

            self.assertEqual(line_item.outcome, ReturnOrderLineStatus.PENDING)
            self.assertIsNone(line_item.received_date)
            self.assertFalse(line_item.received)

        self.assertEqual(rma.lines.count(), 3)

        def receive(items, location=None, expected_code=400):
            """Helper function to receive items against this ReturnOrder."""
            url = reverse('api-return-order-receive', kwargs={'pk': rma.pk})

            response = self.post(
                url, {'items': items, 'location': location}, expected_code=expected_code
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
        self.assertIn(
            'Items can only be received against orders which are in progress', str(data)
        )

        # Issue the order (via the API)
        self.assertIsNone(rma.issue_date)
        self.post(
            reverse('api-return-order-issue', kwargs={'pk': rma.pk}), expected_code=201
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
            [{'item': line.pk} for line in rma.lines.all()], 1, expected_code=201
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

    def test_receive_untracked(self):
        """Test that we can receive untracked items against a ReturnOrder.

        Ref: https://github.com/inventree/InvenTree/pull/8590
        """
        self.assignRole('return_order.add')
        company = Company.objects.get(pk=4)

        # Create a new ReturnOrder
        rma = models.ReturnOrder.objects.create(
            customer=company, description='A return order'
        )

        rma.issue_order()

        # Create some new line items
        part = Part.objects.get(pk=25)

        n_items = part.stock_entries().count()

        for idx in range(2):
            stock_item = StockItem.objects.create(
                part=part, customer=company, quantity=10
            )

            models.ReturnOrderLineItem.objects.create(
                order=rma, item=stock_item, quantity=(idx + 1) * 5
            )

        self.assertEqual(part.stock_entries().count(), n_items + 2)

        line_items = rma.lines.all()

        # Receive items against the order
        url = reverse('api-return-order-receive', kwargs={'pk': rma.pk})

        LOCATION_ID = 1

        self.post(
            url,
            {
                'items': [
                    {'item': line.pk, 'status': StockStatus.DAMAGED.value}
                    for line in line_items
                ],
                'location': LOCATION_ID,
            },
            expected_code=201,
        )

        # Due to the quantities received, we should have created 1 new stock item
        self.assertEqual(part.stock_entries().count(), n_items + 3)

        rma.refresh_from_db()

        for line in rma.lines.all():
            self.assertTrue(line.received)
            self.assertIsNotNone(line.received_date)

            # Check that the associated StockItem has been updated correctly
            self.assertEqual(line.item.status, StockStatus.DAMAGED)
            self.assertIsNone(line.item.customer)
            self.assertIsNone(line.item.sales_order)
            self.assertEqual(line.item.location.pk, LOCATION_ID)

    def test_receive_stale_line_instance(self):
        """A second receipt attempt with a stale line instance must be a no-op.

        Regression test: receive_line_item() checked received_date on the
        caller's (potentially stale) instance, so two concurrent receipt
        requests could both process the same line - splitting the source stock
        item twice and orphaning one of the splits. The line is now re-read
        (under lock) from the database before the check.
        """
        company = Company.objects.get(pk=4)

        rma = models.ReturnOrder.objects.create(
            customer=company, description='A return order'
        )
        rma.issue_order()

        part = Part.objects.get(pk=25)

        # An untracked item, where only part of the quantity is returned
        # (forces the stock item to be split on receipt)
        stock_item = StockItem.objects.create(part=part, customer=company, quantity=10)
        line = models.ReturnOrderLineItem.objects.create(
            order=rma, item=stock_item, quantity=4
        )

        location = StockLocation.objects.get(pk=1)

        # Two "concurrent" requests each hold their own instance of the line
        line_a = models.ReturnOrderLineItem.objects.get(pk=line.pk)
        line_b = models.ReturnOrderLineItem.objects.get(pk=line.pk)

        n_items = StockItem.objects.count()

        rma.receive_line_item(line_a, location, None)

        # The stock item has been split: 4 returned, 6 remain with the customer
        self.assertEqual(StockItem.objects.count(), n_items + 1)

        stock_item.refresh_from_db()
        self.assertEqual(stock_item.quantity, 6)

        line.refresh_from_db()
        self.assertIsNotNone(line.received_date)
        self.assertEqual(line.item.quantity, 4)
        self.assertEqual(line.item.location, location)

        # The second (stale) instance still believes the line is unreceived -
        # the receipt must be skipped based on the database state
        self.assertIsNone(line_b.received_date)

        rma.receive_line_item(line_b, location, None)

        # No further stock item has been created, and the source is unchanged
        self.assertEqual(StockItem.objects.count(), n_items + 1)

        stock_item.refresh_from_db()
        self.assertEqual(stock_item.quantity, 6)

    def test_complete_stale_instance_is_noop(self):
        """A second completion attempt with a stale instance must be a no-op.

        Regression test: _action_complete() checked 'status' on the caller's
        (potentially stale) instance, so two concurrent completion requests
        could both run the completion side effects (duplicate COMPLETED events).
        The status is now re-read (under lock) from the database before the check.
        """
        company = Company.objects.get(pk=4)

        rma = models.ReturnOrder.objects.create(
            customer=company, description='A return order'
        )
        rma.issue_order()

        # Two "concurrent" requests each hold their own instance of the order
        order_a = models.ReturnOrder.objects.get(pk=rma.pk)
        order_b = models.ReturnOrder.objects.get(pk=rma.pk)

        order_a.complete_order()

        rma.refresh_from_db()
        self.assertEqual(rma.status, ReturnOrderStatus.COMPLETE.value)

        # The second (stale) instance still believes the order is IN_PROGRESS -
        # completion must be skipped based on the database state
        self.assertEqual(order_b.status, ReturnOrderStatus.IN_PROGRESS.value)

        with mock.patch('order.models.trigger_event') as trigger:
            order_b.complete_order()
            trigger.assert_not_called()

        rma.refresh_from_db()
        self.assertEqual(rma.status, ReturnOrderStatus.COMPLETE.value)

    def test_ro_calendar(self):
        """Test the calendar export endpoint."""
        # Full test is in test_po_calendar. Since these use the same backend, test only
        # that the endpoint is available
        url = reverse('api-po-so-calendar', kwargs={'ordertype': 'return-order'})

        # Test without completed orders
        response = self.get(url, expected_code=200, format=None)
        calendar = Calendar.from_ical(response.content)
        self.assertIsInstance(calendar, Calendar)

    def test_export(self):
        """Test data export for the ReturnOrder API endpoints."""
        # Export return orders
        data = self.export_data(
            reverse('api-return-order-list'),
            export_format='csv',
            decode=True,
            expected_code=200,
        )

        self.process_csv(
            data,
            required_cols=['Reference', 'Customer'],
            required_rows=models.ReturnOrder.objects.count(),
        )

        N = models.ReturnOrderLineItem.objects.count()
        self.assertGreater(N, 0, 'No ReturnOrderLineItems found!')

        # Export return order lines
        data = self.export_data(
            reverse('api-return-order-line-list'),
            export_format='csv',
            decode=True,
            expected_code=200,
        )

        self.process_csv(
            data, required_rows=N, required_cols=['Order', 'Reference', 'Target Date']
        )

        # Export again, with a search term
        data = self.export_data(
            reverse('api-return-order-line-list'),
            params={'search': 'xyz'},
            export_format='csv',
            decode=True,
            expected_code=200,
        )

        self.process_csv(
            data, required_rows=0, required_cols=['Order', 'Reference', 'Target Date']
        )

    def test_output_options(self):
        """Test the various output options for the ReturnOrder detail endpoint."""
        self.run_output_test(
            reverse('api-return-order-detail', kwargs={'pk': 1}), ['customer_detail']
        )


class ReturnOrderLineItemTests(InvenTreeAPITestCase):
    """Unit tests for ReturnOrderLineItem API endpoints."""

    fixtures = [
        'category',
        'company',
        'return_order',
        'part',
        'location',
        'supplier_part',
        'stock',
    ]
    roles = ['return_order.view']

    def test_options(self):
        """Test the OPTIONS endpoint."""
        self.assignRole('return_order.add')
        data = self.options(
            reverse('api-return-order-line-list'), expected_code=200
        ).data

        self.assertEqual(data['name'], 'Return Order Line Item List')

        # Check POST fields
        post = data['actions']['POST']
        self.assertIn('order', post)
        self.assertIn('item', post)
        self.assertIn('quantity', post)
        self.assertIn('outcome', post)

    def test_list(self):
        """Test list endpoint."""
        url = reverse('api-return-order-line-list')

        response = self.get(url, expected_code=200)
        self.assertGreater(len(response.data), 0)

        # Test with pagination
        data = self.get(
            url, {'limit': 1, 'ordering': 'reference'}, expected_code=200
        ).data

        self.assertIn('count', data)
        self.assertIn('results', data)
        self.assertEqual(len(data['results']), 1)

    def test_detail(self):
        """Test detail endpoint."""
        url = reverse('api-return-order-line-detail', kwargs={'pk': 1})

        response = self.get(url, expected_code=200)
        data = response.data

        self.assertIn('order', data)
        self.assertIn('item', data)
        self.assertIn('quantity', data)
        self.assertIn('outcome', data)

    def test_output_options(self):
        """Test output options for detail endpoint."""
        self.run_output_test(
            reverse('api-return-order-line-detail', kwargs={'pk': 1}),
            ['part_detail', 'item_detail', 'order_detail'],
        )

    def test_update(self):
        """Test updating ReturnOrderLineItem."""
        url = reverse('api-return-order-line-detail', kwargs={'pk': 1})

        # Without permissions
        self.patch(url, {'price': '10.50'}, expected_code=403)

        self.assignRole('return_order.change')

        self.patch(url, {'price': '15.75'}, expected_code=200)

        line = models.ReturnOrderLineItem.objects.get(pk=1)
        self.assertEqual(float(line.price.amount), 15.75)

    def test_bulk_delete(self):
        """Test that we can bulk delete multiple ReturnOrderLineItems via the API."""
        n = models.ReturnOrderLineItem.objects.count()
        self.assertGreater(n, 0)

        items = list(
            models.ReturnOrderLineItem.objects.values_list('pk', flat=True)[:1]
        )

        url = reverse('api-return-order-line-list')

        # Deletion should fail without the correct role
        self.delete(url, {'items': items}, expected_code=403)

        self.assignRole('return_order.delete')

        self.delete(url, {'items': items}, expected_code=200)

        self.assertEqual(models.ReturnOrderLineItem.objects.count(), n - 1)

    def test_extra_line_bulk_delete(self):
        """Test that we can bulk delete multiple ReturnOrderExtraLine items via the API."""
        ro = models.ReturnOrder.objects.first()

        models.ReturnOrderExtraLine.objects.bulk_create([
            models.ReturnOrderExtraLine(
                order=ro, quantity=idx + 1, reference=f'Extra line {idx}'
            )
            for idx in range(3)
        ])

        n = models.ReturnOrderExtraLine.objects.count()
        items = list(
            models.ReturnOrderExtraLine.objects.values_list('pk', flat=True)[:2]
        )

        url = reverse('api-return-order-extra-line-list')

        # Deletion should fail without the correct role
        self.delete(url, {'items': items}, expected_code=403)

        self.assignRole('return_order.delete')

        self.delete(url, {'items': items}, expected_code=200)

        self.assertEqual(models.ReturnOrderExtraLine.objects.count(), n - 2)


class ExtraLineTotalPriceTest(InvenTreeAPITestCase):
    """Unit tests for the 'total_price' field on ExtraLine API endpoints.

    Covers PurchaseOrderExtraLine, SalesOrderExtraLine and ReturnOrderExtraLine,
    which all share the same 'total_price' field via AbstractExtraLineSerializer.
    """

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

    roles = ['purchase_order.change', 'sales_order.change', 'return_order.change']

    def check_total_price(
        self, order, extra_line_model, list_url_name, detail_url_name
    ):
        """Create an ExtraLine with a known price/quantity/discount, and check total_price."""
        line = extra_line_model.objects.create(
            order=order, quantity=5, price=Money(10, 'USD'), discount=20
        )

        # 5 * 10 = 50, less 20% discount = 40
        expected = 40

        # List endpoint
        response = self.get(
            reverse(list_url_name), {'order': order.pk}, expected_code=200
        )
        result = next(r for r in response.data if r['pk'] == line.pk)
        self.assertEqual(float(result['total_price']), expected)

        # Detail endpoint
        response = self.get(
            reverse(detail_url_name, kwargs={'pk': line.pk}), expected_code=200
        )
        self.assertEqual(float(response.data['total_price']), expected)

    def test_po_extra_line_total_price(self):
        """Check 'total_price' for a PurchaseOrderExtraLine."""
        self.check_total_price(
            models.PurchaseOrder.objects.get(pk=1),
            models.PurchaseOrderExtraLine,
            'api-po-extra-line-list',
            'api-po-extra-line-detail',
        )

    def test_so_extra_line_total_price(self):
        """Check 'total_price' for a SalesOrderExtraLine."""
        self.check_total_price(
            models.SalesOrder.objects.get(pk=1),
            models.SalesOrderExtraLine,
            'api-so-extra-line-list',
            'api-so-extra-line-detail',
        )

    def test_return_order_extra_line_total_price(self):
        """Check 'total_price' for a ReturnOrderExtraLine."""
        self.check_total_price(
            models.ReturnOrder.objects.get(pk=1),
            models.ReturnOrderExtraLine,
            'api-return-order-extra-line-list',
            'api-return-order-extra-line-detail',
        )


class TransferOrderTest(OrderTest):
    """Tests for the TransferOrder API."""

    LIST_URL = reverse('api-transfer-order-list')

    def test_transfer_order_list(self):
        """Test the TransferOrder list API endpoint."""
        # all orders
        self.filter({}, 5)

        # filter by outstanding
        self.filter({'outstanding': True}, 3)
        self.filter({'outstanding': False}, 2)

        # Filter by status
        self.filter({'status': TransferOrderStatus.PENDING.value}, 1)
        self.filter({'status': SalesOrderStatus.COMPLETE.value}, 1)
        self.filter({'status': 99}, 0)  # Invalid

        # Filter by "reference"
        self.filter({'reference': 'TO-123'}, 1)
        self.filter({'reference': 'TO-999'}, 0)

        # Filter by "assigned_to_me"
        self.filter({'assigned_to_me': 1}, 0)
        self.filter({'assigned_to_me': 0}, 5)

    def test_overdue(self):
        """Test "overdue" status."""
        self.filter({'overdue': True}, 0)
        self.filter({'overdue': False}, 5)

        # pick two orders that are still open (not cancelled or complete)
        for pk in [1, 4]:
            order = models.TransferOrder.objects.get(pk=pk)
            order.target_date = datetime.now().date() - timedelta(days=10)
            order.save()

        self.filter({'overdue': True}, 2)
        self.filter({'overdue': False}, 3)

    def test_transfer_order_detail(self):
        """Test the TransferOrder detail endpoint."""
        url = '/api/order/transfer-order/1/'

        response = self.get(url)

        data = response.data

        self.assertEqual(data['pk'], 1)

    def test_transfer_order_attachments(self):
        """Test the list endpoint for the Transfer Order Attachments."""
        url = reverse('api-attachment-list')

        # Filter by 'transferorder'
        self.get(
            url, data={'model_type': 'transferorder', 'model_id': 1}, expected_code=200
        )

    def test_transfer_order_operations(self):
        """Test that we can create / edit and delete a TransferOrder via the API."""
        n = models.TransferOrder.objects.count()

        url = reverse('api-transfer-order-list')

        # Initially we do not have "add" permission for the TransferOrder model,
        # so this POST request should return 403 (denied)
        response = self.post(
            url,
            {'reference': 'TO-43245', 'description': 'Transfer order'},
            expected_code=403,
        )

        self.assignRole('transfer_order.add')

        # Now we should be able to create a TransferOrder via the API
        response = self.post(
            url,
            {'reference': 'TO-12345', 'description': 'Transfer order'},
            expected_code=201,
        )

        # Check that the new order has been created
        self.assertEqual(models.TransferOrder.objects.count(), n + 1)

        # Grab the PK for the newly created TransferOrder
        pk = response.data['pk']

        # Basic checks against the newly created TransferOrder
        so = models.TransferOrder.objects.get(pk=pk)
        self.assertEqual(so.reference, 'TO-12345')
        self.assertEqual(so.created_by.username, 'testuser')

        # Try to create a TO with identical reference (should fail)
        response = self.post(
            url,
            {
                'customer': 4,
                'reference': 'TO-12345',
                'description': 'Another transfer order',
            },
            expected_code=400,
        )

        url = reverse('api-transfer-order-detail', kwargs={'pk': pk})

        # Extract detail info for the TransferOrder
        response = self.get(url)
        self.assertEqual(response.data['reference'], 'TO-12345')

        # Try to alter (edit) the TransferOrder
        # Initially try with an invalid reference field value
        response = self.patch(url, {'reference': 'TO-12345-a'}, expected_code=400)

        response = self.patch(url, {'reference': 'TO-12346'}, expected_code=200)

        # Reference should have changed
        self.assertEqual(response.data['reference'], 'TO-12346')

        # Now, let's try to delete this TransferOrder
        # Initially, we do not have the required permission
        response = self.delete(url, expected_code=403)

        self.assignRole('transfer_order.delete')

        response = self.delete(url, expected_code=204)

        # Check that the number of transfer orders has decreased
        self.assertEqual(models.TransferOrder.objects.count(), n)

        # And the resource should no longer be available
        response = self.get(url, expected_code=404)

    def test_transfer_order_create(self):
        """Test that we can create a new TransferOrder via the API."""
        self.assignRole('transfer_order.add')

        url = reverse('api-transfer-order-list')

        # Will fail due to invalid reference field
        response = self.post(
            url,
            {'reference': '1234566778', 'description': 'A test transfer order'},
            expected_code=400,
        )

        self.assertIn(
            'Reference must match required pattern', str(response.data['reference'])
        )

        self.post(
            url,
            {'reference': 'TO-12345', 'description': 'A better test transfer order'},
            expected_code=201,
        )

    def test_transfer_order_cancel(self):
        """Test API endpoint for cancelling a TransferOrder."""
        to = models.TransferOrder.objects.get(pk=1)

        self.assertEqual(to.status, TransferOrderStatus.PENDING)

        url = reverse('api-transfer-order-cancel', kwargs={'pk': to.pk})

        # Try to cancel, without permission
        self.post(url, {}, expected_code=403)

        self.assignRole('transfer_order.add')

        self.post(url, {}, expected_code=201)

        to.refresh_from_db()

        self.assertEqual(to.status, TransferOrderStatus.CANCELLED)

    def test_transfer_order_cancel_stale_instance_is_noop(self):
        """A second cancellation attempt with a stale order instance must be a no-op.

        Regression test: _action_cancel() checked 'can_cancel' (derived from
        'status') on the caller's (potentially stale) instance, so two concurrent
        cancellation requests could both run the cancellation side effects
        (duplicate CANCELLED events). The status is now re-read (under lock)
        from the database before the check.
        """
        to = models.TransferOrder.objects.get(pk=1)
        self.assertEqual(to.status, TransferOrderStatus.PENDING)

        # Two "concurrent" requests each hold their own instance of the order
        instance_a = models.TransferOrder.objects.get(pk=to.pk)
        instance_b = models.TransferOrder.objects.get(pk=to.pk)

        instance_a.cancel_order()

        to.refresh_from_db()
        self.assertEqual(to.status, TransferOrderStatus.CANCELLED)

        # The second (stale) instance still believes the order is PENDING -
        # cancellation must be skipped based on the database state
        self.assertEqual(instance_b.status, TransferOrderStatus.PENDING)

        with mock.patch('order.models.trigger_event') as trigger:
            instance_b.cancel_order()
            trigger.assert_not_called()

        to.refresh_from_db()
        self.assertEqual(to.status, TransferOrderStatus.CANCELLED)

    def test_transfer_order_hold(self):
        """Test API endpoint for holdling a TransferOrder."""
        to = models.TransferOrder.objects.get(pk=1)

        self.assertEqual(to.status, TransferOrderStatus.PENDING)

        url = reverse('api-transfer-order-hold', kwargs={'pk': to.pk})

        # Try to hold, without permission
        self.post(url, {}, expected_code=403)

        self.assignRole('transfer_order.add')

        self.post(url, {}, expected_code=201)

        to.refresh_from_db()

        self.assertEqual(to.status, TransferOrderStatus.ON_HOLD)

    def test_transfer_order_calendar(self):
        """Test the calendar export endpoint."""
        # Create required transfer orders
        self.assignRole('transfer_order.add')

        for i in range(1, 9):
            self.post(
                reverse('api-transfer-order-list'),
                {
                    'reference': f'TO-1100000{i}',
                    'description': f'Calendar SO {i}',
                    'target_date': f'2024-12-{i:02d}',
                },
                expected_code=201,
            )

        # Cancel a few orders - these will not show in incomplete view below
        for to in models.TransferOrder.objects.filter(target_date__isnull=False):
            if to.reference in [
                'TO-11000006',
                'TO-11000007',
                'TO-11000008',
                'TO-11000009',
            ]:
                self.post(
                    reverse('api-transfer-order-cancel', kwargs={'pk': to.pk}),
                    expected_code=201,
                )

        url = reverse('api-po-so-calendar', kwargs={'ordertype': 'transfer-order'})

        # Test without completed orders
        response = self.get(url, expected_code=200, format=None)

        number_orders = len(
            models.TransferOrder.objects.filter(target_date__isnull=False).filter(
                status__lt=TransferOrderStatus.COMPLETE.value
            )
        )

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
        response = self.get(
            url, data={'include_completed': 'True'}, expected_code=200, format=None
        )

        number_orders_incl_complete = len(
            models.TransferOrder.objects.filter(target_date__isnull=False)
        )
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
        """Test we can export the TransferOrder list."""
        n = models.TransferOrder.objects.count()

        # Check there are some sales orders
        self.assertGreater(n, 0)

        # Download file, check we get a 200 response
        for fmt in ['csv', 'xlsx', 'tsv']:
            self.export_data(
                reverse('api-transfer-order-list'),
                export_format=fmt,
                decode=fmt == 'csv',
                expected_code=200,
                expected_fn=r'InvenTree_TransferOrder_.+',
            )

    def test_transfer_order_complete(self):
        """Tests for marking a TransferOrder as complete."""
        self.assignRole('transfer_order.add')
        destination = StockLocation.objects.first()
        # Let's create a TransferOrder
        to = models.TransferOrder.objects.create(
            reference='TO-12345', description='Test TO'
        )

        self.assertEqual(to.status, TransferOrderStatus.PENDING.value)

        # Create a line item
        part = Part.objects.exclude(virtual=True).first()

        line = models.TransferOrderLineItem.objects.create(
            order=to, part=part, quantity=10
        )

        # issue the order
        url = reverse('api-transfer-order-issue', kwargs={'pk': to.pk})
        self.post(url, {}, expected_code=201)
        to.refresh_from_db()
        self.assertEqual(to.status, TransferOrderStatus.ISSUED.value)

        # Allocate some stock
        item = StockItem.objects.create(
            part=part, quantity=100, location=None, batch='transfer-order-test'
        )
        short_allocation = models.TransferOrderAllocation.objects.create(
            quantity=5, line=line, item=item
        )

        # attempt to complete the order, but fail because there are incomplete allocations
        url = reverse('api-transfer-order-complete', kwargs={'pk': to.pk})
        response = self.post(url, {}, expected_code=400)
        self.assertIn('has incomplete allocations', str(response.data))
        # allocate more stock
        short_allocation.delete()
        models.TransferOrderAllocation.objects.create(quantity=10, line=line, item=item)

        # attempt to complete the order, but fail because there is no destination yet
        url = reverse('api-transfer-order-complete', kwargs={'pk': to.pk})
        response = self.post(url, {}, expected_code=400)
        self.assertIn('until a destination location is set', str(response.data))
        # add destination
        to.destination = destination
        to.save()

        # Ok, now we should be able to "complete" the transfer via the API
        url = reverse('api-transfer-order-complete', kwargs={'pk': to.pk})
        self.post(url, {}, expected_code=201)

        to.refresh_from_db()
        self.assertEqual(to.status, TransferOrderStatus.COMPLETE.value)
        self.assertIsNotNone(to.complete_date)

        # Now, let's try *again* (it should fail as the order is already complete)
        response = self.post(url, {}, expected_code=400)
        self.assertIn('Order is already complete', str(response.data))

        # Now, we make sure the affected stock was transferred to the correct location
        StockItem.objects.get(
            part=part, quantity=10, batch='transfer-order-test', location=destination
        )

    def test_transfer_order_consume(self):
        """Tests for marking a TransferOrder consume the stock it 'transfers'."""
        self.assignRole('transfer_order.add')
        destination = StockLocation.objects.first()
        # Let's create a TransferOrder
        to = models.TransferOrder.objects.create(
            reference='TO-12345',
            description='Test TO',
            consume=True,
            destination=destination,
        )

        self.assertEqual(to.status, TransferOrderStatus.PENDING.value)

        # Create a line item
        part = Part.objects.exclude(virtual=True).first()

        line = models.TransferOrderLineItem.objects.create(
            order=to, part=part, quantity=10
        )

        # issue the order
        url = reverse('api-transfer-order-issue', kwargs={'pk': to.pk})
        self.post(url, {}, expected_code=201)
        to.refresh_from_db()
        self.assertEqual(to.status, TransferOrderStatus.ISSUED.value)

        # Allocate some stock
        item = StockItem.objects.create(
            part=part, quantity=100, location=None, batch='transfer-order-test'
        )
        models.TransferOrderAllocation.objects.create(quantity=10, line=line, item=item)

        # Ok, now we should be able to "complete" the transfer via the API
        url = reverse('api-transfer-order-complete', kwargs={'pk': to.pk})
        self.post(url, {}, expected_code=201)

        to.refresh_from_db()
        self.assertEqual(to.status, TransferOrderStatus.COMPLETE.value)
        self.assertIsNotNone(to.complete_date)

        # Now, we make sure the affected stock was 'consumed', reducing available quantity
        item.refresh_from_db()
        self.assertEqual(item.quantity, 90)

        # and that it wasn't transferred to the destination
        with self.assertRaises(StockItem.DoesNotExist):
            StockItem.objects.get(
                part=part,
                quantity=10,
                batch='transfer-order-test',
                location=destination,
            )

    def test_transfer_order_depleted_allocation(self):
        """Completion handles allocations whose stock was reduced after allocation.

        Regression test: the 'transferred' quantity used to be incremented by the
        *allocated* quantity even when less (or no) stock was actually moved.
        """
        self.assignRole('transfer_order.add')
        destination = StockLocation.objects.first()

        to = models.TransferOrder.objects.create(
            reference='TO-54321', description='Test TO', destination=destination
        )

        part = Part.objects.exclude(virtual=True).first()

        line_a = models.TransferOrderLineItem.objects.create(
            order=to, part=part, quantity=10
        )
        line_b = models.TransferOrderLineItem.objects.create(
            order=to, part=part, quantity=10
        )

        url = reverse('api-transfer-order-issue', kwargs={'pk': to.pk})
        self.post(url, {}, expected_code=201)

        item_a = StockItem.objects.create(part=part, quantity=10, batch='to-reduced')
        item_b = StockItem.objects.create(part=part, quantity=10, batch='to-depleted')

        models.TransferOrderAllocation.objects.create(
            quantity=10, line=line_a, item=item_a
        )
        models.TransferOrderAllocation.objects.create(
            quantity=10, line=line_b, item=item_b
        )

        # Reduce the available stock *after* the allocations have been made
        item_a.quantity = 6
        item_a.save()

        item_b.quantity = 0
        item_b.save()

        url = reverse('api-transfer-order-complete', kwargs={'pk': to.pk})
        self.post(url, {}, expected_code=201)

        to.refresh_from_db()
        self.assertEqual(to.status, TransferOrderStatus.COMPLETE.value)

        # Only the quantity which was actually available has been transferred
        line_a.refresh_from_db()
        item_a.refresh_from_db()
        self.assertEqual(line_a.transferred, 6)
        self.assertEqual(item_a.location, destination)
        self.assertEqual(item_a.quantity, 6)

        # The depleted allocation was skipped, without error
        line_b.refresh_from_db()
        item_b.refresh_from_db()
        self.assertEqual(line_b.transferred, 0)
        self.assertIsNone(item_b.location)

    def test_transfer_order_consume_depleted_allocation(self):
        """Consume-type completion only records the quantity actually consumed."""
        self.assignRole('transfer_order.add')

        to = models.TransferOrder.objects.create(
            reference='TO-54322', description='Test TO', consume=True
        )

        part = Part.objects.exclude(virtual=True).first()

        line = models.TransferOrderLineItem.objects.create(
            order=to, part=part, quantity=10
        )

        url = reverse('api-transfer-order-issue', kwargs={'pk': to.pk})
        self.post(url, {}, expected_code=201)

        item = StockItem.objects.create(
            part=part, quantity=100, batch='to-consume', delete_on_deplete=False
        )

        models.TransferOrderAllocation.objects.create(quantity=10, line=line, item=item)

        # Reduce the available stock *after* the allocation has been made
        item.quantity = 4
        item.save()

        url = reverse('api-transfer-order-complete', kwargs={'pk': to.pk})
        self.post(url, {}, expected_code=201)

        to.refresh_from_db()
        self.assertEqual(to.status, TransferOrderStatus.COMPLETE.value)

        # Only the quantity which was actually available has been consumed
        line.refresh_from_db()
        item.refresh_from_db()
        self.assertEqual(line.transferred, 4)
        self.assertEqual(item.quantity, 0)

    def test_transfer_order_partial_allocation_stale_item_instance(self):
        """A partial allocation must not fail completion if stock is reduced concurrently.

        Regression test: transfer_quantity (and the choice between the "move" and
        "split" branches) was computed from self.item.quantity as cached in memory
        on the allocation instance. If the stock item's quantity was reduced by a
        concurrent operation after the allocation was loaded, the stale value could
        select the "split" branch when only a "move" of the entire (now-reduced)
        item is actually possible - causing splitStock() to reject the now-oversized
        split, and the whole order completion to fail. The stock item's row is now
        locked and its quantity refreshed before the branch is chosen.
        """
        self.assignRole('transfer_order.add')
        destination = StockLocation.objects.first()

        to = models.TransferOrder.objects.create(
            reference='TO-STALE-ITEM', description='Test TO', destination=destination
        )

        part = Part.objects.exclude(virtual=True).first()

        line = models.TransferOrderLineItem.objects.create(
            order=to, part=part, quantity=6
        )

        to.issue_order()

        item = StockItem.objects.create(part=part, quantity=10, batch='to-stale-item')

        # A partial allocation - less than the full stock item quantity
        allocation = models.TransferOrderAllocation.objects.create(
            quantity=6, line=line, item=item
        )

        # Load a second copy of the allocation, caching the item's original quantity
        stale_allocation = models.TransferOrderAllocation.objects.get(pk=allocation.pk)
        self.assertEqual(stale_allocation.item.quantity, 10)

        # Reduce the available stock *after* the stale copy was loaded
        # (simulating a concurrent stock adjustment)
        item.quantity = 4
        item.save()

        # Completing the (stale) allocation must not raise, and must transfer
        # only the quantity which is actually available
        stale_allocation.complete_allocation(None)

        item.refresh_from_db()
        line.refresh_from_db()

        self.assertEqual(item.location, destination)
        self.assertEqual(item.quantity, 4)
        self.assertEqual(line.transferred, 4)

    def test_transfer_order_complete_stale_instance(self):
        """A second completion attempt with a stale instance must be rejected.

        Regression test: _action_complete() only checked the *in-memory* status,
        so two concurrent completion requests (each holding its own instance of
        the order) could both observe status=ISSUED and each process every
        allocation - duplicating all stock movements and double-counting the
        'transferred' quantity. The status is now re-read (under lock) from the
        database before the allocations are processed.
        """
        self.assignRole('transfer_order.add')
        destination = StockLocation.objects.first()

        to = models.TransferOrder.objects.create(
            reference='TO-54323', description='Test TO', destination=destination
        )

        part = Part.objects.exclude(virtual=True).first()

        line = models.TransferOrderLineItem.objects.create(
            order=to, part=part, quantity=10
        )

        to.issue_order()
        to.refresh_from_db()
        self.assertEqual(to.status, TransferOrderStatus.ISSUED.value)

        item = StockItem.objects.create(part=part, quantity=10, batch='to-stale')
        models.TransferOrderAllocation.objects.create(quantity=10, line=line, item=item)

        # Two "concurrent" requests each hold their own instance of the order
        instance_a = models.TransferOrder.objects.get(pk=to.pk)
        instance_b = models.TransferOrder.objects.get(pk=to.pk)

        self.assertTrue(instance_a.complete_order(None))

        line.refresh_from_db()
        self.assertEqual(line.transferred, 10)

        # The second (stale) instance still believes the order is ISSUED,
        # but completion must be rejected based on the database state
        self.assertEqual(instance_b.status, TransferOrderStatus.ISSUED.value)

        with self.assertRaises(ValidationError) as err:
            instance_b.complete_order(None)

        self.assertIn('Order is already complete', str(err.exception))

        # The transferred quantity has not been double-counted
        line.refresh_from_db()
        self.assertEqual(line.transferred, 10)

    def test_output_options(self):
        """Test the output options for the TransferOrder detail endpoint."""
        self.run_output_test(
            reverse('api-transfer-order-detail', kwargs={'pk': 1}),
            ['take_from_detail', 'destination_detail'],
        )


class TransferOrderLineItemTest(OrderTest):
    """Tests for the TransferOrderLineItem API."""

    LIST_URL = reverse('api-transfer-order-line-list')

    # adjust counts in asserts based on those created in setUpTestData
    # plus those in fixtures
    NUM_LINE_ITEMS_IN_FIXTURES = 2

    @classmethod
    def setUpTestData(cls):
        """Init routine for this unit test class."""
        super().setUpTestData()

        # List of 'transferrable' parts
        parts = Part.objects.exclude(virtual=True)

        lines = []

        # Create a bunch of TransferOrderLineItems for each order
        for idx, to in enumerate(models.TransferOrder.objects.all()):
            for part in parts:
                lines.append(
                    models.TransferOrderLineItem(
                        order=to,
                        part=part,
                        quantity=(idx + 1) * 5,
                        reference=f'Order {to.reference} - line {idx}',
                    )
                )

        # Bulk create
        models.TransferOrderLineItem.objects.bulk_create(lines)

        cls.url = reverse('api-transfer-order-line-list')

    def test_transfer_order_line_list(self):
        """Test list endpoint."""
        response = self.get(self.url, {}, expected_code=200)

        n = models.TransferOrderLineItem.objects.count()

        # We should have received *all* lines
        self.assertEqual(len(response.data), n)

        # List *all* lines, but paginate
        response = self.get(self.url, {'limit': 5}, expected_code=200)

        self.assertEqual(response.data['count'], n)
        self.assertEqual(len(response.data['results']), 5)

        n_orders = models.TransferOrder.objects.count()
        n_parts = Part.objects.exclude(virtual=True).count()

        # List by part
        # fixures add line items, avoid those here with [:3] for predictable counts
        for part in Part.objects.exclude(virtual=True)[:3]:
            response = self.get(self.url, {'part': part.pk, 'limit': 10})
            self.assertEqual(response.data['count'], n_orders)

        # List by order
        # fixures add line items, avoid those here with [:3] for predictable counts
        for order in models.TransferOrder.objects.all()[:3]:
            response = self.get(self.url, {'order': order.pk, 'limit': 10})
            # count of line items equal to number of parts because
            # we created a line item per part on each order in setUpTestData
            self.assertEqual(response.data['count'], n_parts)

        # Filter by 'completed' status
        self.filter({'completed': 1}, 1)
        self.filter({'completed': 0}, n - 1)

        # Filter by 'allocated' status
        self.filter({'allocated': 'true'}, 2)
        self.filter({'allocated': 'false'}, n - 2)

    def test_transfer_order_line_bulk_delete(self):
        """Test that we can bulk delete multiple TransferOrderLineItems via the API."""
        n = models.TransferOrderLineItem.objects.count()

        # Select lines from orders which are not completed (and thus not locked)
        items = list(
            models.TransferOrderLineItem.objects.exclude(
                order__status__in=TransferOrderStatusGroups.COMPLETE
            ).values_list('pk', flat=True)[:2]
        )

        # Deletion should fail without the correct role
        self.delete(self.url, {'items': items}, expected_code=403)

        self.assignRole('transfer_order.delete')

        self.delete(self.url, {'items': items}, expected_code=200)

        # We should have 2 less TransferOrderLineItems after deleting them
        self.assertEqual(models.TransferOrderLineItem.objects.count(), n - 2)

    def test_completed_order_locked(self):
        """Test that line items cannot be deleted from a completed TransferOrder."""
        self.assignRole('transfer_order.delete')

        set_global_setting(models.TransferOrder.UNLOCK_SETTING, False)

        order = models.TransferOrder.objects.filter(
            status=TransferOrderStatus.PENDING.value, lines__isnull=False
        ).first()
        assert order

        # Mark the order as complete
        order.status = TransferOrderStatus.COMPLETE.value
        order.save()

        n = order.lines.count()
        self.assertGreater(n, 1)

        line = order.lines.first()
        detail_url = reverse('api-transfer-order-line-detail', kwargs={'pk': line.pk})

        # Single deletion of a line item should fail
        self.delete(detail_url, expected_code=400)

        # Bulk deletion should also fail (and roll back atomically)
        items = list(order.lines.values_list('pk', flat=True))
        self.delete(self.url, {'items': items}, expected_code=400)

        self.assertEqual(order.lines.count(), n)

        # Unlocking completed orders should allow deletion again
        set_global_setting(models.TransferOrder.UNLOCK_SETTING, True)

        self.delete(detail_url, expected_code=204)
        self.assertEqual(order.lines.count(), n - 1)

    def test_transfer_order_line_allocated_filters(self):
        """Test filtering by allocation status for a TransferOrderLineItem."""
        self.assignRole('transfer_order.add')

        destination = StockLocation.objects.first()
        assert destination

        response = self.post(
            reverse('api-transfer-order-list'),
            {
                'reference': 'TO-12345',
                'description': 'Test Transfer Order',
                'destination': destination.pk,
            },
        )

        order_id = response.data['pk']
        order = models.TransferOrder.objects.get(pk=order_id)

        transfer_order_line_url = reverse('api-transfer-order-line-list')

        # Initially, there should be no line items against this order
        response = self.get(transfer_order_line_url, {'order': order_id})

        self.assertEqual(len(response.data), 0)

        parts = [25, 50, 100]

        # Let's create some new line items
        for part_id in parts:
            self.post(
                transfer_order_line_url,
                {'order': order_id, 'part': part_id, 'quantity': 10},
            )

        # Should be three items now
        response = self.get(transfer_order_line_url, {'order': order_id})

        self.assertEqual(len(response.data), 3)

        for item in response.data:
            # Check that the line item has been created
            self.assertEqual(item['order'], order_id)

            # Check that the line quantities are correct
            self.assertEqual(item['quantity'], 10)
            self.assertEqual(item['allocated'], 0)
            self.assertEqual(item['transferred'], 0)

        # Initial API filters should return no results
        self.filter({'order': order_id, 'allocated': 1}, 0)
        self.filter({'order': order_id, 'completed': 1}, 0)

        # issue the order
        order_issue_url = reverse('api-transfer-order-issue', kwargs={'pk': order.pk})
        self.post(order_issue_url, {}, expected_code=201)

        # Next, allocate stock against 2 line items
        for item in parts[:2]:
            p = Part.objects.get(pk=item)
            s = StockItem.objects.create(part=p, quantity=100)
            l = models.TransferOrderLineItem.objects.filter(order=order, part=p).first()
            assert l

            # Allocate against the API
            self.post(
                reverse('api-transfer-order-allocate', kwargs={'pk': order.pk}),
                {'items': [{'line_item': l.pk, 'stock_item': s.pk, 'quantity': 10}]},
            )

        # Filter by 'fully allocated' status
        self.filter({'order': order_id, 'allocated': 1}, 2)
        self.filter({'order': order_id, 'allocated': 0}, 1)

        self.filter({'order': order_id, 'completed': 1}, 0)
        self.filter({'order': order_id, 'completed': 0}, 3)

        # Finally, attempt to transfer this line item
        # we have incomplete allocations, so must specify arg
        self.post(
            reverse('api-transfer-order-complete', kwargs={'pk': order.pk}),
            {'accept_incomplete_allocation': 'true'},
        )

        # Filter by 'completed' status
        self.filter({'order': order_id, 'completed': 1}, 2)
        self.filter({'order': order_id, 'completed': 0}, 1)

    def test_output_options(self):
        """Test the various output options for the TransferOrderLineItem detail endpoint."""
        self.run_output_test(
            reverse('api-transfer-order-line-detail', kwargs={'pk': 1}),
            ['part_detail', 'order_detail'],
        )


class TransferOrderDownloadTest(OrderTest):
    """Unit tests for downloading TransferOrder data via the API endpoint."""

    def test_download_fail(self):
        """Test that downloading without the 'export' option fails."""
        url = reverse('api-transfer-order-list')

        response = self.export_data(url, export_plugin='no-plugin', expected_code=400)
        self.assertIn('is not a valid choice', str(response['export_plugin']))

    def test_download_xlsx(self):
        """Test xlsx file download."""
        url = reverse('api-transfer-order-list')

        # Download .xls file
        with self.export_data(
            url, export_format='xlsx', expected_code=200, decode=False
        ) as file:
            self.assertIsInstance(file, io.BytesIO)

    def test_download_csv(self):
        """Test that the list of transfer orders can be downloaded as a .csv file."""
        url = reverse('api-transfer-order-list')

        required_cols = [
            'Line Items',
            'Completed Lines',
            'ID',
            'Reference',
            'Order Status',
            'Description',
            'Project Code',
            'Responsible',
            'Consume Stock',
        ]

        excluded_cols = ['metadata']

        # Download .xls file
        with self.export_data(url, export_format='csv') as file:
            data = self.process_csv(
                file,
                required_cols=required_cols,
                excluded_cols=excluded_cols,
                required_rows=models.TransferOrder.objects.count(),
            )

            for line in data:
                order = models.TransferOrder.objects.get(pk=line['ID'])

                self.assertEqual(line['Description'], order.description)
                self.assertEqual(line['Order Status'], str(order.status))

        # Download only outstanding transfer orders
        with self.export_data(url, {'outstanding': True}, export_format='tsv') as file:
            self.process_csv(
                file,
                required_cols=required_cols,
                excluded_cols=excluded_cols,
                required_rows=models.TransferOrder.objects.filter(
                    status__in=TransferOrderStatusGroups.OPEN
                ).count(),
                delimiter='\t',
            )


class TransferOrderAllocateTest(OrderTest):
    """Unit tests for allocating stock items against a TransferOrder."""

    @classmethod
    def setUpTestData(cls):
        """Init routine for this unit test class."""
        super().setUpTestData()

    def setUp(self):
        """Init routines for this unit testing class."""
        super().setUp()

        self.assignRole('transfer_order.add')

        self.url = reverse('api-transfer-order-allocate', kwargs={'pk': 1})
        self.url_serialized = reverse(
            'api-transfer-order-allocate-serials', kwargs={'pk': 1}
        )

        self.order = models.TransferOrder.objects.get(pk=1)

        # Create some line items for this transfer order
        parts = Part.objects.exclude(virtual=True)

        for part in parts:
            # Create a new line item
            models.TransferOrderLineItem.objects.create(
                order=self.order, part=part, quantity=5
            )

            # Ensure we have stock!
            StockItem.objects.create(part=part, quantity=100)

        # Create a new shipment against this TransferOrder
        # self.shipment = models.TransferOrderShipment.objects.create(order=self.order)

    def test_invalid(self):
        """Test POST with invalid data."""
        # No data
        response = self.post(self.url, {}, expected_code=400)

        self.assertIn('This field is required', str(response.data['items']))

        # Test with a single line items
        line = self.order.lines.first()
        part = line.part

        # Valid stock_item, but quantity is invalid
        data = {
            'items': [
                {
                    'line_item': line.pk,
                    'stock_item': part.stock_items.last().pk,
                    'quantity': 0,
                }
            ]
        }

        response = self.post(self.url, data, expected_code=400)

        self.assertIn('Quantity must be positive', str(response.data['items']))

        # Valid stock item, too much quantity
        data['items'][0]['quantity'] = 250

        response = self.post(self.url, data, expected_code=400)

        self.assertIn('Available quantity (100) exceeded', str(response.data['items']))

    def test_allocate(self):
        """Test that the allocation endpoint acts as expected, when provided with valid data!"""
        # First, check that there are no line items allocated against this TransferOrder
        self.assertEqual(self.order.stock_allocations.count(), 0)

        data = {'items': []}

        for line in self.order.lines.all():
            for stock_item in line.part.stock_items.filter(quantity__gt=5):
                # Find a non-serialized stock item to allocate
                if not stock_item.serialized:
                    break

            # Fully-allocate each line
            data['items'].append({
                'line_item': line.pk,
                'stock_item': stock_item.pk,
                'quantity': 5,
            })

        self.post(self.url, data, expected_code=201)

        # There should have been 1 stock item allocated against each line item
        n_lines = self.order.lines.count()

        self.assertEqual(self.order.stock_allocations.count(), n_lines)

        for line in self.order.lines.all():
            self.assertEqual(line.allocations.count(), 1)

    def test_allocate_serials(self):
        """Test that the allocation endpoint acts as expected, when provided with serials."""
        self.assertEqual(self.order.stock_allocations.count(), 0)

        trackable_lines = self.order.lines.filter(part__trackable=True)
        for line in trackable_lines:
            stock_item = (
                line.part.stock_items
                .exclude(serial=None)
                .filter(StockItem.IN_STOCK_FILTER)
                .first()
            )

            # Allocate this serialized item to the transfer order
            data = {
                'line_item': line.pk,
                'quantity': 1,
                'serial_numbers': stock_item.serial,
            }

            self.post(self.url_serialized, data, expected_code=201)

        # There should have been 1 stock item allocated against each line item
        n_lines = trackable_lines.count()
        self.assertEqual(self.order.stock_allocations.count(), n_lines)

        for line in trackable_lines.all():
            self.assertEqual(line.allocations.count(), 1)

    def test_allocate_variant(self):
        """Test that the allocation endpoint acts as expected, when provided with variant."""
        # First, check that there are no line items allocated against this TransferOrder
        self.assertEqual(self.order.stock_allocations.count(), 0)

        data = {'items': []}

        def check_template(line_item):
            return line_item.part.is_template

        for line in filter(check_template, self.order.lines.all()):
            stock_item: Optional[StockItem] = None

            stock_item = None

            # Allocate a matching variant
            parts: list[Part] = (
                Part.objects
                .exclude(virtual=True)
                .exclude(is_template=True)
                .filter(variant_of=line.part.pk)
            )
            # if we don't have a matching variant, continue
            if not parts.exists():
                continue
            for part in parts:
                # ensure we have the quantity necessary to allocate
                if not part.stock_items.filter(quantity__gt=5).exists():
                    continue

                stock_item = part.stock_items.last()

                for item in part.stock_items.filter(quantity__gt=5):
                    if item.serialized:
                        continue

                    stock_item = item
                    break

                if stock_item is not None:
                    break

            if stock_item is None:
                raise self.fail('No stock item found for part')  # pragma: no cover

            # Fully-allocate each line
            data['items'].append({
                'line_item': line.pk,
                'stock_item': stock_item.pk,
                'quantity': 5,
            })

        self.post(self.url, data, expected_code=201)

        # At least one item should be allocated, and all should be variants
        self.assertGreater(self.order.stock_allocations.count(), 0)
        for allocation in self.order.stock_allocations.all():
            self.assertNotEqual(allocation.item.part.pk, allocation.line.part.pk)

    def test_output_options(self):
        """Test the various output options for the SalesOrderAllocation detail endpoint."""
        self.run_output_test(
            reverse('api-transfer-order-allocation-list'),
            ['part_detail', 'item_detail', 'order_detail', 'location_detail'],
            assert_subset=True,
        )


class SalesOrderAutoAllocateAPITest(InvenTreeAPITestCase):
    """API integration tests for the SalesOrder auto-allocate endpoint."""

    fixtures = ['company', 'users']

    roles = ['sales_order.add', 'sales_order.change', 'sales_order.delete']

    @classmethod
    def setUpTestData(cls):
        """Create shared order, parts, locations and stock for all tests."""
        super().setUpTestData()

        cls.customer = Company.objects.create(
            name='Test Customer', is_customer=True, description=''
        )
        cls.part = Part.objects.create(
            name='AutoAlloc Part', salable=True, description=''
        )

        cls.loc_a = StockLocation.objects.create(name='Shelf A')
        cls.loc_b = StockLocation.objects.create(name='Shelf B')

    def _make_order(self, qty=50):
        """Create a fresh SalesOrder with one line item and one shipment."""
        order = models.SalesOrder.objects.create(
            customer=self.customer,
            reference=f'SO-TEST-{models.SalesOrder.objects.count()}',
        )
        line = SalesOrderLineItem.objects.create(
            order=order, part=self.part, quantity=qty
        )
        shipment = SalesOrderShipment.objects.create(order=order)
        return order, line, shipment

    def _url(self, pk):
        return reverse('api-so-auto-allocate', kwargs={'pk': pk})

    # ------------------------------------------------------------------
    # Permission and basic response tests
    # ------------------------------------------------------------------

    def test_requires_authentication(self):
        """POST without authentication returns 401."""
        self.client.logout()
        order, _, _ = self._make_order()
        self.post(self._url(order.pk), {}, expected_code=401)

    def test_basic_post_returns_200(self):
        """POST with defaults runs synchronously in tests and returns 200."""
        order, line, _ = self._make_order()
        StockItem.objects.create(part=self.part, quantity=100)

        response = self.post(self._url(order.pk), {}, expected_code=200)

        self.assertIn('task_id', response.data)
        self.assertTrue(response.data['complete'])
        self.assertTrue(response.data['success'])

        # Task ran synchronously — allocations are already committed
        self.assertTrue(line.is_fully_allocated())

    def test_invalid_order_pk_returns_404(self):
        """POST to a non-existent order pk returns 404."""
        self.post(self._url(999999), {}, expected_code=404)

    # ------------------------------------------------------------------
    # Field validation
    # ------------------------------------------------------------------

    def test_invalid_stock_sort_by_rejected(self):
        """An unrecognised stock_sort_by value is rejected with 400."""
        order, _, _ = self._make_order()
        self.post(
            self._url(order.pk),
            {'stock_sort_by': 'not_a_valid_sort'},
            expected_code=400,
        )

    def test_invalid_serialized_stock_rejected(self):
        """An unrecognised serialized_stock value is rejected with 400."""
        order, _, _ = self._make_order()
        self.post(self._url(order.pk), {'serialized_stock': 'maybe'}, expected_code=400)

    def test_shipment_from_another_order_rejected(self):
        """A shipment that belongs to a different order is rejected with 400."""
        order, _, _ = self._make_order()
        _other_order, _, other_shipment = self._make_order()

        self.post(
            self._url(order.pk), {'shipment': other_shipment.pk}, expected_code=400
        )

    def test_shipped_shipment_rejected(self):
        """A shipment that has already been marked as shipped is rejected with 400."""
        from datetime import date

        order, _, shipment = self._make_order()
        shipment.shipment_date = date.today()
        shipment.save()

        self.post(self._url(order.pk), {'shipment': shipment.pk}, expected_code=400)

    def test_line_items_from_another_order_rejected(self):
        """line_items belonging to a different order are rejected with 400."""
        order, _, _ = self._make_order()
        _, other_line, _ = self._make_order()

        self.post(
            self._url(order.pk), {'line_items': [other_line.pk]}, expected_code=400
        )

    # ------------------------------------------------------------------
    # Allocation behaviour
    # ------------------------------------------------------------------

    def test_allocates_available_stock(self):
        """Stock is allocated to the line item after a successful POST."""
        order, line, _ = self._make_order(qty=30)
        item = StockItem.objects.create(part=self.part, quantity=100)

        self.post(self._url(order.pk), {}, expected_code=200)

        allocs = SalesOrderAllocation.objects.filter(line=line)
        self.assertEqual(allocs.count(), 1)
        self.assertEqual(allocs.first().item, item)
        self.assertEqual(allocs.first().quantity, 30)

    def test_line_items_subset_only_allocates_selected_lines(self):
        """When line_items is specified only those lines are allocated."""
        order = models.SalesOrder.objects.create(
            customer=self.customer,
            reference=f'SO-SUBSET-{models.SalesOrder.objects.count()}',
        )
        line_a = SalesOrderLineItem.objects.create(
            order=order, part=self.part, quantity=10
        )
        part_b = Part.objects.create(name='Part B', salable=True, description='')
        line_b = SalesOrderLineItem.objects.create(
            order=order, part=part_b, quantity=10
        )

        StockItem.objects.create(part=self.part, quantity=50)
        StockItem.objects.create(part=part_b, quantity=50)

        self.post(self._url(order.pk), {'line_items': [line_a.pk]}, expected_code=200)

        self.assertTrue(line_a.is_fully_allocated())
        self.assertFalse(line_b.is_fully_allocated())

    def test_serialized_stock_only(self):
        """serialized_stock='serialized' allocates only serialized items."""
        order, line, _ = self._make_order(qty=1)
        # Unserialized item
        StockItem.objects.create(part=self.part, quantity=50)
        # Serialized item
        serial_item = StockItem.objects.create(
            part=self.part, quantity=1, serial='SN-001'
        )

        self.post(
            self._url(order.pk), {'serialized_stock': 'serialized'}, expected_code=200
        )

        allocs = SalesOrderAllocation.objects.filter(line=line)
        self.assertEqual(allocs.count(), 1)
        self.assertEqual(allocs.first().item, serial_item)

    def test_unserialized_stock_only(self):
        """serialized_stock='unserialized' skips serialized items."""
        order, line, _ = self._make_order(qty=10)
        # Serialized items only
        for sn in range(10):
            StockItem.objects.create(part=self.part, quantity=1, serial=f'SN-{sn}')

        self.post(
            self._url(order.pk), {'serialized_stock': 'unserialized'}, expected_code=200
        )

        self.assertFalse(line.is_fully_allocated())
        self.assertEqual(SalesOrderAllocation.objects.filter(line=line).count(), 0)

    def test_stock_sort_by_quantity_asc(self):
        """stock_sort_by=QUANTITY_ASC consumes the smallest lot first."""
        order, line, _ = self._make_order(qty=15)
        small = StockItem.objects.create(part=self.part, quantity=5)
        StockItem.objects.create(part=self.part, quantity=100)

        self.post(
            self._url(order.pk),
            {
                'stock_sort_by': str(StockSortOrder.QUANTITY_ASC),
                'interchangeable': True,
            },
            expected_code=200,
        )

        allocs = SalesOrderAllocation.objects.filter(line=line)
        self.assertTrue(any(a.item == small and a.quantity == 5 for a in allocs))

    def test_stock_sort_by_quantity_desc(self):
        """stock_sort_by=QUANTITY_DESC consumes the largest lot first, covering the requirement in one allocation."""
        order, line, _ = self._make_order(qty=15)
        StockItem.objects.create(part=self.part, quantity=5)
        StockItem.objects.create(part=self.part, quantity=100)

        self.post(
            self._url(order.pk),
            {
                'stock_sort_by': str(StockSortOrder.QUANTITY_DESC),
                'interchangeable': True,
            },
            expected_code=200,
        )

        allocs = SalesOrderAllocation.objects.filter(line=line)
        self.assertEqual(allocs.count(), 1)
        self.assertEqual(allocs.first().quantity, 15)

    def test_location_filter(self):
        """Only stock within the specified location is used."""
        order, line, _ = self._make_order(qty=10)
        StockItem.objects.create(part=self.part, quantity=50, location=self.loc_a)
        StockItem.objects.create(part=self.part, quantity=50, location=self.loc_b)

        self.post(self._url(order.pk), {'location': self.loc_a.pk}, expected_code=200)

        allocs = SalesOrderAllocation.objects.filter(line=line)
        self.assertEqual(allocs.count(), 1)
        self.assertEqual(allocs.first().item.location, self.loc_a)

    def test_exclude_location_filter(self):
        """Stock in the excluded location is not used."""
        order, line, _ = self._make_order(qty=10)
        StockItem.objects.create(part=self.part, quantity=50, location=self.loc_a)
        StockItem.objects.create(part=self.part, quantity=50, location=self.loc_b)

        self.post(
            self._url(order.pk), {'exclude_location': self.loc_a.pk}, expected_code=200
        )

        allocs = SalesOrderAllocation.objects.filter(line=line)
        self.assertEqual(allocs.count(), 1)
        self.assertEqual(allocs.first().item.location, self.loc_b)

    def test_shipment_assigned_to_allocations(self):
        """When a shipment is specified, all allocations are assigned to it."""
        order, line, shipment = self._make_order(qty=20)
        StockItem.objects.create(part=self.part, quantity=100)

        self.post(self._url(order.pk), {'shipment': shipment.pk}, expected_code=200)

        allocs = SalesOrderAllocation.objects.filter(line=line)
        self.assertTrue(allocs.exists())
        for alloc in allocs:
            self.assertEqual(alloc.shipment, shipment)

    def test_interchangeable_false_skips_split_stock(self):
        """With interchangeable=False, allocation is skipped when no single item covers the full quantity."""
        order, line, _ = self._make_order(qty=50)
        StockItem.objects.create(part=self.part, quantity=20)
        StockItem.objects.create(part=self.part, quantity=20)

        self.post(self._url(order.pk), {'interchangeable': False}, expected_code=200)

        self.assertFalse(line.is_fully_allocated())
        self.assertEqual(SalesOrderAllocation.objects.filter(line=line).count(), 0)


class SalesOrderAllocationBulkDeleteAPITest(InvenTreeAPITestCase):
    """API integration tests for bulk-delete of SalesOrderAllocation, verifying shipped allocations are protected."""

    fixtures = ['company', 'users']

    roles = ['sales_order.add', 'sales_order.change', 'sales_order.delete']

    @classmethod
    def setUpTestData(cls):
        """Create shared order, part and stock for all tests."""
        super().setUpTestData()

        cls.customer = models.Company.objects.create(
            name='BulkDelete Customer', is_customer=True, description=''
        )
        cls.part = Part.objects.create(
            name='BulkDelete Part', salable=True, description=''
        )

    def _make_order_with_allocations(self, n_unshipped=2, n_shipped=1):
        """Return (order, unshipped_allocations, shipped_allocations)."""
        order = models.SalesOrder.objects.create(
            customer=self.customer,
            reference=f'SO-BD-{models.SalesOrder.objects.count()}',
        )
        line = SalesOrderLineItem.objects.create(
            order=order, part=self.part, quantity=100
        )
        unshipped_shipment = models.SalesOrderShipment.objects.create(
            order=order, reference='1'
        )

        shipped_shipment = models.SalesOrderShipment.objects.create(
            order=order, reference='2'
        )
        shipped_shipment.shipment_date = date.today()
        shipped_shipment.save()

        unshipped = []
        for _ in range(n_unshipped):
            item = StockItem.objects.create(part=self.part, quantity=10)
            alloc = SalesOrderAllocation.objects.create(
                line=line, item=item, quantity=10, shipment=unshipped_shipment
            )
            unshipped.append(alloc)

        shipped = []
        for _ in range(n_shipped):
            item = StockItem.objects.create(part=self.part, quantity=10)
            alloc = SalesOrderAllocation.objects.create(
                line=line, item=item, quantity=10, shipment=shipped_shipment
            )
            shipped.append(alloc)

        return order, unshipped, shipped

    def _url(self):
        return reverse('api-so-allocation-list')

    # ------------------------------------------------------------------
    # Basic bulk-delete
    # ------------------------------------------------------------------

    def test_bulk_delete_unshipped_allocations(self):
        """Unshipped allocations can be bulk-deleted."""
        _, unshipped, _ = self._make_order_with_allocations(n_unshipped=2, n_shipped=0)
        ids = [a.pk for a in unshipped]

        self.delete(self._url(), {'items': ids}, expected_code=200)

        self.assertFalse(SalesOrderAllocation.objects.filter(pk__in=ids).exists())

    # ------------------------------------------------------------------
    # Shipped allocation protection
    # ------------------------------------------------------------------

    def test_shipped_allocations_are_not_deleted(self):
        """Shipped allocations are silently skipped when included in a bulk-delete request."""
        _, _, shipped = self._make_order_with_allocations(n_unshipped=0, n_shipped=2)
        ids = [a.pk for a in shipped]

        self.delete(self._url(), {'items': ids}, expected_code=200)

        # All shipped allocations should still exist
        self.assertEqual(SalesOrderAllocation.objects.filter(pk__in=ids).count(), 2)

    def test_mixed_delete_removes_only_unshipped(self):
        """A bulk-delete of mixed shipped/unshipped allocations removes only the unshipped ones."""
        _, unshipped, shipped = self._make_order_with_allocations(
            n_unshipped=2, n_shipped=2
        )
        all_ids = [a.pk for a in unshipped] + [a.pk for a in shipped]

        self.delete(self._url(), {'items': all_ids}, expected_code=200)

        # Unshipped should be gone
        for alloc in unshipped:
            self.assertFalse(SalesOrderAllocation.objects.filter(pk=alloc.pk).exists())

        # Shipped should remain
        shipped_ids = [a.pk for a in shipped]
        self.assertEqual(
            SalesOrderAllocation.objects.filter(pk__in=shipped_ids).count(), 2
        )
