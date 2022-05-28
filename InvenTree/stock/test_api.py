"""Unit testing for the Stock API"""

import io
import os
from datetime import datetime, timedelta

import django.http
from django.urls import reverse

import tablib
from rest_framework import status

import company.models
import part.models
from common.models import InvenTreeSetting
from InvenTree.api_tester import InvenTreeAPITestCase
from InvenTree.status_codes import StockStatus
from stock.models import StockItem, StockLocation


class StockAPITestCase(InvenTreeAPITestCase):

    fixtures = [
        'category',
        'part',
        'bom',
        'company',
        'location',
        'supplier_part',
        'stock',
        'stock_tests',
    ]

    roles = [
        'stock.change',
        'stock.add',
        'stock_location.change',
        'stock_location.add',
        'stock.delete',
    ]

    def setUp(self):

        super().setUp()


class StockLocationTest(StockAPITestCase):
    """Series of API tests for the StockLocation API"""
    list_url = reverse('api-location-list')

    def setUp(self):
        super().setUp()

        # Add some stock locations
        StockLocation.objects.create(name='top', description='top category')

    def test_list(self):
        # Check that we can request the StockLocation list
        response = self.client.get(self.list_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_add(self):
        # Check that we can add a new StockLocation
        data = {
            'parent': 1,
            'name': 'Location',
            'description': 'Another location for stock'
        }
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class StockItemListTest(StockAPITestCase):
    """Tests for the StockItem API LIST endpoint"""

    list_url = reverse('api-stock-list')

    def get_stock(self, **kwargs):
        """Filter stock and return JSON object"""
        response = self.client.get(self.list_url, format='json', data=kwargs)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Return JSON-ified data
        return response.data

    def test_get_stock_list(self):
        """List *all* StockItem objects."""
        response = self.get_stock()

        self.assertEqual(len(response), 29)

    def test_filter_by_part(self):
        """Filter StockItem by Part reference"""
        response = self.get_stock(part=25)

        self.assertEqual(len(response), 17)

        response = self.get_stock(part=10004)

        self.assertEqual(len(response), 12)

    def test_filter_by_IPN(self):
        """Filter StockItem by IPN reference"""
        response = self.get_stock(IPN="R.CH")
        self.assertEqual(len(response), 3)

    def test_filter_by_location(self):
        """Filter StockItem by StockLocation reference"""
        response = self.get_stock(location=5)
        self.assertEqual(len(response), 1)

        response = self.get_stock(location=1, cascade=0)
        self.assertEqual(len(response), 7)

        response = self.get_stock(location=1, cascade=1)
        self.assertEqual(len(response), 9)

        response = self.get_stock(location=7)
        self.assertEqual(len(response), 18)

    def test_filter_by_depleted(self):
        """Filter StockItem by depleted status"""
        response = self.get_stock(depleted=1)
        self.assertEqual(len(response), 1)

        response = self.get_stock(depleted=0)
        self.assertEqual(len(response), 28)

    def test_filter_by_in_stock(self):
        """Filter StockItem by 'in stock' status"""
        response = self.get_stock(in_stock=1)
        self.assertEqual(len(response), 26)

        response = self.get_stock(in_stock=0)
        self.assertEqual(len(response), 3)

    def test_filter_by_status(self):
        """Filter StockItem by 'status' field"""
        codes = {
            StockStatus.OK: 27,
            StockStatus.DESTROYED: 1,
            StockStatus.LOST: 1,
            StockStatus.DAMAGED: 0,
            StockStatus.REJECTED: 0,
        }

        for code in codes.keys():
            num = codes[code]

            response = self.get_stock(status=code)
            self.assertEqual(len(response), num)

    def test_filter_by_batch(self):
        """Filter StockItem by batch code"""
        response = self.get_stock(batch='B123')
        self.assertEqual(len(response), 1)

    def test_filter_by_serialized(self):
        """Filter StockItem by serialized status"""
        response = self.get_stock(serialized=1)
        self.assertEqual(len(response), 12)

        for item in response:
            self.assertIsNotNone(item['serial'])

        response = self.get_stock(serialized=0)
        self.assertEqual(len(response), 17)

        for item in response:
            self.assertIsNone(item['serial'])

    def test_filter_by_has_batch(self):
        """Test the 'has_batch' filter, which tests if the stock item has been assigned a batch code"""
        with_batch = self.get_stock(has_batch=1)
        without_batch = self.get_stock(has_batch=0)

        n_stock_items = StockItem.objects.all().count()

        # Total sum should equal the total count of stock items
        self.assertEqual(n_stock_items, len(with_batch) + len(without_batch))

        for item in with_batch:
            self.assertFalse(item['batch'] in [None, ''])

        for item in without_batch:
            self.assertTrue(item['batch'] in [None, ''])

    def test_filter_by_tracked(self):
        """Test the 'tracked' filter.

        This checks if the stock item has either a batch code *or* a serial number
        """
        tracked = self.get_stock(tracked=True)
        untracked = self.get_stock(tracked=False)

        n_stock_items = StockItem.objects.all().count()

        self.assertEqual(n_stock_items, len(tracked) + len(untracked))

        blank = [None, '']

        for item in tracked:
            self.assertTrue(item['batch'] not in blank or item['serial'] not in blank)

        for item in untracked:
            self.assertTrue(item['batch'] in blank and item['serial'] in blank)

    def test_filter_by_expired(self):
        """Filter StockItem by expiry status"""
        # First, we can assume that the 'stock expiry' feature is disabled
        response = self.get_stock(expired=1)
        self.assertEqual(len(response), 29)

        self.user.is_staff = True
        self.user.save()

        # Now, ensure that the expiry date feature is enabled!
        InvenTreeSetting.set_setting('STOCK_ENABLE_EXPIRY', True, self.user)

        response = self.get_stock(expired=1)
        self.assertEqual(len(response), 1)

        for item in response:
            self.assertTrue(item['expired'])

        response = self.get_stock(expired=0)
        self.assertEqual(len(response), 28)

        for item in response:
            self.assertFalse(item['expired'])

        # Mark some other stock items as expired
        today = datetime.now().date()

        for pk in [510, 511, 512]:
            item = StockItem.objects.get(pk=pk)
            item.expiry_date = today - timedelta(days=pk)
            item.save()

        response = self.get_stock(expired=1)
        self.assertEqual(len(response), 4)

        response = self.get_stock(expired=0)
        self.assertEqual(len(response), 25)

    def test_paginate(self):
        """Test that we can paginate results correctly"""
        for n in [1, 5, 10]:
            response = self.get_stock(limit=n)

            self.assertIn('count', response)
            self.assertIn('results', response)

            self.assertEqual(len(response['results']), n)

    def export_data(self, filters=None):

        if not filters:
            filters = {}

        filters['export'] = 'csv'

        response = self.client.get(self.list_url, data=filters)

        self.assertEqual(response.status_code, 200)

        self.assertTrue(isinstance(response, django.http.response.StreamingHttpResponse))

        file_object = io.StringIO(response.getvalue().decode('utf-8'))

        dataset = tablib.Dataset().load(file_object, 'csv', headers=True)

        return dataset

    def test_export(self):
        """Test exporting of Stock data via the API"""
        dataset = self.export_data({})

        # Check that *all* stock item objects have been exported
        self.assertEqual(len(dataset), StockItem.objects.count())

        # Expected headers
        headers = [
            'part',
            'customer',
            'location',
            'parent',
            'quantity',
            'status',
        ]

        for h in headers:
            self.assertIn(h, dataset.headers)

        excluded_headers = [
            'metadata',
        ]

        for h in excluded_headers:
            self.assertNotIn(h, dataset.headers)

        # Now, add a filter to the results
        dataset = self.export_data({'location': 1})

        self.assertEqual(len(dataset), 9)

        dataset = self.export_data({'part': 25})

        self.assertEqual(len(dataset), 17)


class StockItemTest(StockAPITestCase):
    """Series of API tests for the StockItem API"""

    list_url = reverse('api-stock-list')

    def setUp(self):
        super().setUp()
        # Create some stock locations
        top = StockLocation.objects.create(name='A', description='top')

        StockLocation.objects.create(name='B', description='location b', parent=top)
        StockLocation.objects.create(name='C', description='location c', parent=top)

    def test_create_default_location(self):
        """Test the default location functionality, if a 'location' is not specified in the creation request."""
        # The part 'R_4K7_0603' (pk=4) has a default location specified

        response = self.client.post(
            self.list_url,
            data={
                'part': 4,
                'quantity': 10
            }
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['location'], 2)

        # What if we explicitly set the location to a different value?

        response = self.client.post(
            self.list_url,
            data={
                'part': 4,
                'quantity': 20,
                'location': 1,
            }
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['location'], 1)

        # And finally, what if we set the location explicitly to None?

        response = self.client.post(
            self.list_url,
            data={
                'part': 4,
                'quantity': 20,
                'location': '',
            }
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['location'], None)

    def test_stock_item_create(self):
        """Test creation of a StockItem via the API"""
        # POST with an empty part reference

        response = self.client.post(
            self.list_url,
            data={
                'quantity': 10,
                'location': 1
            }
        )

        self.assertContains(response, 'Valid part must be supplied', status_code=status.HTTP_400_BAD_REQUEST)

        # POST with an invalid part reference

        response = self.client.post(
            self.list_url,
            data={
                'quantity': 10,
                'location': 1,
                'part': 10000000,
            }
        )

        self.assertContains(response, 'Valid part must be supplied', status_code=status.HTTP_400_BAD_REQUEST)

        # POST without quantity
        response = self.post(
            self.list_url,
            {
                'part': 1,
                'location': 1,
            },
            expected_code=400
        )

        self.assertIn('Quantity is required', str(response.data))

        # POST with quantity and part and location
        response = self.post(
            self.list_url,
            data={
                'part': 1,
                'location': 1,
                'quantity': 10,
            },
            expected_code=201
        )

    def test_creation_with_serials(self):
        """Test that serialized stock items can be created via the API."""
        trackable_part = part.models.Part.objects.create(
            name='My part',
            description='A trackable part',
            trackable=True,
            default_location=StockLocation.objects.get(pk=1),
        )

        self.assertEqual(trackable_part.stock_entries().count(), 0)
        self.assertEqual(trackable_part.get_stock_count(), 0)

        # This should fail, incorrect serial number count
        self.post(
            self.list_url,
            data={
                'part': trackable_part.pk,
                'quantity': 10,
                'serial_numbers': '1-20',
            },
            expected_code=400,
        )

        response = self.post(
            self.list_url,
            data={
                'part': trackable_part.pk,
                'quantity': 10,
                'serial_numbers': '1-10',
            },
            expected_code=201,
        )

        data = response.data

        self.assertEqual(data['quantity'], 10)
        sn = data['serial_numbers']

        # Check that each serial number was created
        for i in range(1, 11):
            self.assertTrue(i in sn)

            # Check the unique stock item has been created

            item = StockItem.objects.get(
                part=trackable_part,
                serial=str(i),
            )

            # Item location should have been set automatically
            self.assertIsNotNone(item.location)

            self.assertEqual(str(i), item.serial)

        # There now should be 10 unique stock entries for this part
        self.assertEqual(trackable_part.stock_entries().count(), 10)
        self.assertEqual(trackable_part.get_stock_count(), 10)

    def test_default_expiry(self):
        """Test that the "default_expiry" functionality works via the API.

        - If an expiry_date is specified, use that
        - Otherwise, check if the referenced part has a default_expiry defined
            - If so, use that!
            - Otherwise, no expiry

        Notes:
            - Part <25> has a default_expiry of 10 days

        """
        # First test - create a new StockItem without an expiry date
        data = {
            'part': 4,
            'quantity': 10,
        }

        response = self.client.post(self.list_url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertIsNone(response.data['expiry_date'])

        # Second test - create a new StockItem with an explicit expiry date
        data['expiry_date'] = '2022-12-12'

        response = self.client.post(self.list_url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertIsNotNone(response.data['expiry_date'])
        self.assertEqual(response.data['expiry_date'], '2022-12-12')

        # Third test - create a new StockItem for a Part which has a default expiry time
        data = {
            'part': 25,
            'quantity': 10
        }

        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Expected expiry date is 10 days in the future
        expiry = datetime.now().date() + timedelta(10)

        self.assertEqual(response.data['expiry_date'], expiry.isoformat())

    def test_purchase_price(self):
        """Test that we can correctly read and adjust purchase price information via the API"""
        url = reverse('api-stock-detail', kwargs={'pk': 1})

        data = self.get(url, expected_code=200).data

        # Check fixture values
        self.assertEqual(data['purchase_price'], '123.0000')
        self.assertEqual(data['purchase_price_currency'], 'AUD')
        self.assertEqual(data['purchase_price_string'], 'A$123.0000')

        # Update just the amount
        data = self.patch(
            url,
            {
                'purchase_price': 456
            },
            expected_code=200
        ).data

        self.assertEqual(data['purchase_price'], '456.0000')
        self.assertEqual(data['purchase_price_currency'], 'AUD')

        # Update the currency
        data = self.patch(
            url,
            {
                'purchase_price_currency': 'NZD',
            },
            expected_code=200
        ).data

        self.assertEqual(data['purchase_price_currency'], 'NZD')

        # Clear the price field
        data = self.patch(
            url,
            {
                'purchase_price': None,
            },
            expected_code=200
        ).data

        self.assertEqual(data['purchase_price'], None)
        self.assertEqual(data['purchase_price_string'], '-')

        # Invalid currency code
        data = self.patch(
            url,
            {
                'purchase_price_currency': 'xyz',
            },
            expected_code=400
        )

        data = self.get(url).data
        self.assertEqual(data['purchase_price_currency'], 'NZD')

    def test_install(self):
        """Test that stock item can be installed into antoher item, via the API"""
        # Select the "parent" stock item
        parent_part = part.models.Part.objects.get(pk=100)

        item = StockItem.objects.create(
            part=parent_part,
            serial='12345688-1230',
            quantity=1,
        )

        sub_part = part.models.Part.objects.get(pk=50)
        sub_item = StockItem.objects.create(
            part=sub_part,
            serial='xyz-123',
            quantity=1,
        )

        n_entries = sub_item.tracking_info.count()

        self.assertIsNone(sub_item.belongs_to)

        url = reverse('api-stock-item-install', kwargs={'pk': item.pk})

        # Try to install an item that is *not* in the BOM for this part!
        response = self.post(
            url,
            {
                'stock_item': 520,
                'note': 'This should fail, as Item #522 is not in the BOM',
            },
            expected_code=400
        )

        self.assertIn('Selected part is not in the Bill of Materials', str(response.data))

        # Now, try to install an item which *is* in the BOM for the parent part
        response = self.post(
            url,
            {
                'stock_item': sub_item.pk,
                'note': "This time, it should be good!",
            },
            expected_code=201,
        )

        sub_item.refresh_from_db()

        self.assertEqual(sub_item.belongs_to, item)

        self.assertEqual(n_entries + 1, sub_item.tracking_info.count())

        # Try to install again - this time, should fail because the StockItem is not available!
        response = self.post(
            url,
            {
                'stock_item': sub_item.pk,
                'note': 'Expectation: failure!',
            },
            expected_code=400,
        )

        self.assertIn('Stock item is unavailable', str(response.data))

        # Now, try to uninstall via the API

        url = reverse('api-stock-item-uninstall', kwargs={'pk': sub_item.pk})

        self.post(
            url,
            {
                'location': 1,
            },
            expected_code=201,
        )

        sub_item.refresh_from_db()

        self.assertIsNone(sub_item.belongs_to)
        self.assertEqual(sub_item.location.pk, 1)


class StocktakeTest(StockAPITestCase):
    """Series of tests for the Stocktake API"""

    def test_action(self):
        """Test each stocktake action endpoint, for validation"""
        for endpoint in ['api-stock-count', 'api-stock-add', 'api-stock-remove']:

            url = reverse(endpoint)

            data = {}

            # POST with a valid action
            response = self.post(url, data)

            self.assertIn("This field is required", str(response.data["items"]))

            data['items'] = [{
                'no': 'aa'
            }]

            # POST without a PK
            response = self.post(url, data, expected_code=400)

            self.assertIn('This field is required', str(response.data))

            # POST with an invalid PK
            data['items'] = [{
                'pk': 10
            }]

            response = self.post(url, data, expected_code=400)

            self.assertContains(response, 'object does not exist', status_code=status.HTTP_400_BAD_REQUEST)

            # POST with missing quantity value
            data['items'] = [{
                'pk': 1234
            }]

            response = self.post(url, data, expected_code=400)
            self.assertContains(response, 'This field is required', status_code=status.HTTP_400_BAD_REQUEST)

            # POST with an invalid quantity value
            data['items'] = [{
                'pk': 1234,
                'quantity': '10x0d'
            }]

            response = self.post(url, data)
            self.assertContains(response, 'A valid number is required', status_code=status.HTTP_400_BAD_REQUEST)

            data['items'] = [{
                'pk': 1234,
                'quantity': "-1.234"
            }]

            response = self.post(url, data)
            self.assertContains(response, 'Ensure this value is greater than or equal to 0', status_code=status.HTTP_400_BAD_REQUEST)

    def test_transfer(self):
        """Test stock transfers"""
        data = {
            'items': [
                {
                    'pk': 1234,
                    'quantity': 10,
                }
            ],
            'location': 1,
            'notes': "Moving to a new location"
        }

        url = reverse('api-stock-transfer')

        # This should succeed
        response = self.post(url, data, expected_code=201)

        # Now try one which will fail due to a bad location
        data['location'] = 'not a location'

        response = self.post(url, data, expected_code=400)

        self.assertContains(response, 'Incorrect type. Expected pk value', status_code=status.HTTP_400_BAD_REQUEST)


class StockItemDeletionTest(StockAPITestCase):
    """Tests for stock item deletion via the API"""

    def test_delete(self):

        n = StockItem.objects.count()

        # Create and then delete a bunch of stock items
        for idx in range(10):

            # Create new StockItem via the API
            response = self.post(
                reverse('api-stock-list'),
                {
                    'part': 1,
                    'location': 1,
                    'quantity': idx,
                },
                expected_code=201
            )

            pk = response.data['pk']

            self.assertEqual(StockItem.objects.count(), n + 1)

            # Request deletion via the API
            self.delete(
                reverse('api-stock-detail', kwargs={'pk': pk}),
                expected_code=204
            )

        self.assertEqual(StockItem.objects.count(), n)


class StockTestResultTest(StockAPITestCase):

    def get_url(self):
        return reverse('api-stock-test-result-list')

    def test_list(self):

        url = self.get_url()
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 4)

        response = self.client.get(url, data={'stock_item': 105})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 4)

    def test_post_fail(self):
        # Attempt to post a new test result without specifying required data

        url = self.get_url()

        response = self.client.post(
            url,
            data={
                'test': 'A test',
                'result': True,
            },
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # This one should pass!
        response = self.client.post(
            url,
            data={
                'test': 'A test',
                'stock_item': 105,
                'result': True,
            },
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_post(self):
        # Test creation of a new test result

        url = self.get_url()

        response = self.client.get(url)
        n = len(response.data)

        data = {
            'stock_item': 105,
            'test': 'Checked Steam Valve',
            'result': False,
            'value': '150kPa',
            'notes': 'I guess there was just too much pressure?',
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.get(url)
        self.assertEqual(len(response.data), n + 1)

        # And read out again
        response = self.client.get(url, data={'test': 'Checked Steam Valve'})

        self.assertEqual(len(response.data), 1)

        test = response.data[0]
        self.assertEqual(test['value'], '150kPa')
        self.assertEqual(test['user'], self.user.pk)

    def test_post_bitmap(self):
        """2021-08-25

        For some (unknown) reason, prior to fix https://github.com/inventree/InvenTree/pull/2018
        uploading a bitmap image would result in a failure.

        This test has been added to ensure that there is no regression.

        As a bonus this also tests the file-upload component
        """
        here = os.path.dirname(__file__)

        image_file = os.path.join(here, 'fixtures', 'test_image.bmp')

        with open(image_file, 'rb') as bitmap:

            data = {
                'stock_item': 105,
                'test': 'Checked Steam Valve',
                'result': False,
                'value': '150kPa',
                'notes': 'I guess there was just too much pressure?',
                "attachment": bitmap,
            }

            response = self.client.post(self.get_url(), data)

            self.assertEqual(response.status_code, 201)

            # Check that an attachment has been uploaded
            self.assertIsNotNone(response.data['attachment'])


class StockAssignTest(StockAPITestCase):
    """Unit tests for the stock assignment API endpoint, where stock items are manually assigned to a customer"""

    URL = reverse('api-stock-assign')

    def test_invalid(self):

        # Test with empty data
        response = self.post(
            self.URL,
            data={},
            expected_code=400,
        )

        self.assertIn('This field is required', str(response.data['items']))
        self.assertIn('This field is required', str(response.data['customer']))

        # Test with an invalid customer
        response = self.post(
            self.URL,
            data={
                'customer': 999,
            },
            expected_code=400,
        )

        self.assertIn('object does not exist', str(response.data['customer']))

        # Test with a company which is *not* a customer
        response = self.post(
            self.URL,
            data={
                'customer': 3,
            },
            expected_code=400,
        )

        self.assertIn('company is not a customer', str(response.data['customer']))

        # Test with an empty items list
        response = self.post(
            self.URL,
            data={
                'items': [],
                'customer': 4,
            },
            expected_code=400,
        )

        self.assertIn('A list of stock items must be provided', str(response.data))

        stock_item = StockItem.objects.create(
            part=part.models.Part.objects.get(pk=1),
            status=StockStatus.DESTROYED,
            quantity=5,
        )

        response = self.post(
            self.URL,
            data={
                'items': [
                    {
                        'item': stock_item.pk,
                    },
                ],
                'customer': 4,
            },
            expected_code=400,
        )

        self.assertIn('Item must be in stock', str(response.data['items'][0]))

    def test_valid(self):

        stock_items = []

        for i in range(5):

            stock_item = StockItem.objects.create(
                part=part.models.Part.objects.get(pk=25),
                quantity=i + 5,
            )

            stock_items.append({
                'item': stock_item.pk
            })

        customer = company.models.Company.objects.get(pk=4)

        self.assertEqual(customer.assigned_stock.count(), 0)

        response = self.post(
            self.URL,
            data={
                'items': stock_items,
                'customer': 4,
            },
            expected_code=201,
        )

        self.assertEqual(response.data['customer'], 4)

        # 5 stock items should now have been assigned to this customer
        self.assertEqual(customer.assigned_stock.count(), 5)


class StockMergeTest(StockAPITestCase):
    """Unit tests for merging stock items via the API"""

    URL = reverse('api-stock-merge')

    def setUp(self):

        super().setUp()

        self.part = part.models.Part.objects.get(pk=25)
        self.loc = StockLocation.objects.get(pk=1)
        self.sp_1 = company.models.SupplierPart.objects.get(pk=100)
        self.sp_2 = company.models.SupplierPart.objects.get(pk=101)

        self.item_1 = StockItem.objects.create(
            part=self.part,
            supplier_part=self.sp_1,
            quantity=100,
        )

        self.item_2 = StockItem.objects.create(
            part=self.part,
            supplier_part=self.sp_2,
            quantity=100,
        )

        self.item_3 = StockItem.objects.create(
            part=self.part,
            supplier_part=self.sp_2,
            quantity=50,
        )

    def test_missing_data(self):
        """Test responses which are missing required data"""
        # Post completely empty

        data = self.post(
            self.URL,
            {},
            expected_code=400
        ).data

        self.assertIn('This field is required', str(data['items']))
        self.assertIn('This field is required', str(data['location']))

        # Post with a location and empty items list
        data = self.post(
            self.URL,
            {
                'items': [],
                'location': 1,
            },
            expected_code=400
        ).data

        self.assertIn('At least two stock items', str(data))

    def test_invalid_data(self):
        """Test responses which have invalid data"""
        # Serialized stock items should be rejected
        data = self.post(
            self.URL,
            {
                'items': [
                    {
                        'item': 501,
                    },
                    {
                        'item': 502,
                    }
                ],
                'location': 1,
            },
            expected_code=400,
        ).data

        self.assertIn('Serialized stock cannot be merged', str(data))

        # Prevent item duplication

        data = self.post(
            self.URL,
            {
                'items': [
                    {
                        'item': 11,
                    },
                    {
                        'item': 11,
                    }
                ],
                'location': 1,
            },
            expected_code=400,
        ).data

        self.assertIn('Duplicate stock items', str(data))

        # Check for mismatching stock items
        data = self.post(
            self.URL,
            {
                'items': [
                    {
                        'item': 1234,
                    },
                    {
                        'item': 11,
                    }
                ],
                'location': 1,
            },
            expected_code=400,
        ).data

        self.assertIn('Stock items must refer to the same part', str(data))

        # Check for mismatching supplier parts
        payload = {
            'items': [
                {
                    'item': self.item_1.pk,
                },
                {
                    'item': self.item_2.pk,
                },
            ],
            'location': 1,
        }

        data = self.post(
            self.URL,
            payload,
            expected_code=400,
        ).data

        self.assertIn('Stock items must refer to the same supplier part', str(data))

    def test_valid_merge(self):
        """Test valid merging of stock items"""
        # Check initial conditions
        n = StockItem.objects.filter(part=self.part).count()
        self.assertEqual(self.item_1.quantity, 100)

        payload = {
            'items': [
                {
                    'item': self.item_1.pk,
                },
                {
                    'item': self.item_2.pk,
                },
                {
                    'item': self.item_3.pk,
                },
            ],
            'location': 1,
            'allow_mismatched_suppliers': True,
        }

        self.post(
            self.URL,
            payload,
            expected_code=201,
        )

        self.item_1.refresh_from_db()

        # Stock quantity should have been increased!
        self.assertEqual(self.item_1.quantity, 250)

        # Total number of stock items has been reduced!
        self.assertEqual(StockItem.objects.filter(part=self.part).count(), n - 2)
