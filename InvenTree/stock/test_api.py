"""Unit testing for the Stock API."""

import io
import os
from datetime import datetime, timedelta
from enum import IntEnum

import django.http
from django.core.exceptions import ValidationError
from django.urls import reverse

import tablib
from djmoney.money import Money
from rest_framework import status

import build.models
import company.models
import part.models
from common.models import InvenTreeSetting
from InvenTree.status_codes import StockHistoryCode, StockStatus
from InvenTree.unit_test import InvenTreeAPITestCase
from part.models import Part
from stock.models import (StockItem, StockItemTestResult, StockLocation,
                          StockLocationType)


class StockAPITestCase(InvenTreeAPITestCase):
    """Mixin for stock api tests."""

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
        'stock_location.delete',
        'stock.delete',
    ]


class StockLocationTest(StockAPITestCase):
    """Series of API tests for the StockLocation API."""

    list_url = reverse('api-location-list')

    @classmethod
    def setUpTestData(cls):
        """Setup for all tests."""
        super().setUpTestData()

        # Add some stock locations
        StockLocation.objects.create(name='top', description='top category')

    def test_list(self):
        """Test the StockLocationList API endpoint"""
        test_cases = [
            ({}, 8, 'no parameters'),
            ({'parent': 1, 'cascade': False}, 2, 'Filter by parent, no cascading'),
            ({'parent': 1, 'cascade': True}, 2, 'Filter by parent, cascading'),
            ({'cascade': True, 'depth': 0}, 8, 'Cascade with no parent, depth=0'),
            ({'cascade': False, 'depth': 10}, 8, 'Cascade with no parent, depth=0'),
            ({'parent': 'null', 'cascade': True, 'depth': 0}, 7, 'Cascade with null parent, depth=0'),
            ({'parent': 'null', 'cascade': True, 'depth': 10}, 8, 'Cascade with null parent and bigger depth'),
            ({'parent': 'null', 'cascade': False, 'depth': 10}, 3, 'No cascade even with depth specified with null parent'),
            ({'parent': 1, 'cascade': False, 'depth': 0}, 2, 'Dont cascade with depth=0 and parent'),
            ({'parent': 1, 'cascade': True, 'depth': 0}, 2, 'Cascade with depth=0 and parent'),
            ({'parent': 1, 'cascade': False, 'depth': 1}, 2, 'Dont cascade even with depth=1 specified with parent'),
            ({'parent': 1, 'cascade': True, 'depth': 1}, 2, 'Cascade with depth=1 with parent'),
            ({'parent': 1, 'cascade': True, 'depth': 'abcdefg'}, 2, 'Cascade with invalid depth and parent'),
            ({'parent': 42}, 8, 'Should return everything if parent_pk is not valid'),
            ({'parent': 'null', 'exclude_tree': 1, 'cascade': True}, 5, 'Should return everything except tree with pk=1'),
            ({'parent': 'null', 'exclude_tree': 42, 'cascade': True}, 8, 'Should return everything because exclude_tree=42 is no valid pk'),
        ]

        for params, res_len, description in test_cases:
            response = self.get(self.list_url, params, expected_code=200)
            self.assertEqual(len(response.data), res_len, description)

        # Check that the required fields are present
        fields = [
            'pk',
            'name',
            'description',
            'level',
            'parent',
            'items',
            'pathstring',
            'owner',
            'url',
            'icon',
            'location_type',
            'location_type_detail',
        ]

        response = self.get(self.list_url, expected_code=200)
        for result in response.data:
            for f in fields:
                self.assertIn(f, result, f'"{f}" is missing in result of StockLocation list')

    def test_add(self):
        """Test adding StockLocation."""
        # Check that we can add a new StockLocation
        data = {
            'parent': 1,
            'name': 'Location',
            'description': 'Another location for stock'
        }

        self.post(self.list_url, data, expected_code=201)

    def test_stock_location_delete(self):
        """Test stock location deletion with different parameters"""

        class Target(IntEnum):
            move_sub_locations_to_parent_move_stockitems_to_parent = 0,
            move_sub_locations_to_parent_delete_stockitems = 1,
            delete_sub_locations_move_stockitems_to_parent = 2,
            delete_sub_locations_delete_stockitems = 3,

        # First, construct a set of template / variant parts
        part = Part.objects.create(
            name='Part for stock item creation', description='Part for stock item creation',
            category=None,
            is_template=False,
        )

        for i in range(4):
            delete_sub_locations: bool = False
            delete_stock_items: bool = False

            if i in (Target.move_sub_locations_to_parent_delete_stockitems, Target.delete_sub_locations_delete_stockitems):
                delete_stock_items = True
            if i in (Target.delete_sub_locations_move_stockitems_to_parent, Target.delete_sub_locations_delete_stockitems):
                delete_sub_locations = True

            # Create a parent stock location
            parent_stock_location = StockLocation.objects.create(
                name='Parent stock location',
                description='This is the parent stock location where the sub categories and stock items are moved to',
                parent=None
            )

            stocklocation_count_before = StockLocation.objects.count()
            stock_location_count_before = StockItem.objects.count()

            # Create a stock location to be deleted
            stock_location_to_delete = StockLocation.objects.create(
                name='Stock location to delete',
                description='This is the stock location to be deleted',
                parent=parent_stock_location
            )

            url = reverse('api-location-detail', kwargs={'pk': stock_location_to_delete.id})

            stock_items = []
            # Create stock items in the location to be deleted
            for jj in range(3):
                stock_items.append(StockItem.objects.create(
                    batch=f"Batch xyz {jj}",
                    location=stock_location_to_delete,
                    part=part
                ))

            child_stock_locations = []
            child_stock_locations_items = []
            # Create sub location under the stock location to be deleted
            for ii in range(3):
                child = StockLocation.objects.create(
                    name=f"Sub-location {ii}",
                    description="A sub-location of the deleted stock location",
                    parent=stock_location_to_delete
                )
                child_stock_locations.append(child)

                # Create stock items in the sub locations
                for jj in range(3):
                    child_stock_locations_items.append(StockItem.objects.create(
                        batch=f"B xyz {jj}",
                        part=part,
                        location=child
                    ))

            # Delete the created stock location
            params = {}
            if delete_stock_items:
                params['delete_stock_items'] = '1'
            if delete_sub_locations:
                params['delete_sub_locations'] = '1'
            response = self.delete(
                url,
                params,
                expected_code=204,
            )

            self.assertEqual(response.status_code, 204)

            if delete_stock_items:
                if i == Target.delete_sub_locations_delete_stockitems:
                    # Check if all sub-categories deleted
                    self.assertEqual(StockItem.objects.count(), stock_location_count_before)
                elif i == Target.move_sub_locations_to_parent_delete_stockitems:
                    # Check if all stock locations deleted
                    self.assertEqual(StockItem.objects.count(), stock_location_count_before + len(child_stock_locations_items))
            else:
                # Stock locations moved to the parent location
                for stock_item in stock_items:
                    stock_item.refresh_from_db()
                    self.assertEqual(stock_item.location, parent_stock_location)

                if delete_sub_locations:
                    for child_stock_location_item in child_stock_locations_items:
                        child_stock_location_item.refresh_from_db()
                        self.assertEqual(child_stock_location_item.location, parent_stock_location)

            if delete_sub_locations:
                # Check if all sub-locations are deleted
                self.assertEqual(StockLocation.objects.count(), stocklocation_count_before)
            else:
                #  Check if all sub-locations moved to the parent
                for child in child_stock_locations:
                    child.refresh_from_db()
                    self.assertEqual(child.parent, parent_stock_location)

    def test_stock_location_structural(self):
        """Test the effectiveness of structural stock locations

        Make sure:
        - Stock items cannot be created in structural locations
        - Stock items cannot be located to structural locations
        - Check that stock location change to structural fails if items located into it
        """
        # Create our structural stock location
        structural_location = StockLocation.objects.create(
            name='Structural stock location',
            description='This is the structural stock location',
            parent=None,
            structural=True
        )

        stock_item_count_before = StockItem.objects.count()

        # Make sure that we get an error if we try to create a stock item in the structural location
        with self.assertRaises(ValidationError):
            item = StockItem.objects.create(
                batch="Stock item which shall not be created",
                location=structural_location
            )

        # Ensure that the stock item really did not get created in the structural location
        self.assertEqual(stock_item_count_before, StockItem.objects.count())

        # Create a non-structural location for test stock location change
        non_structural_location = StockLocation.objects.create(
            name='Non-structural category',
            description='This is a non-structural category',
            parent=None,
            structural=False
        )

        # Construct a part for stock item creation
        part = Part.objects.create(
            name='Part for stock item creation', description='Part for stock item creation',
            category=None,
            is_template=False,
        )

        # Create the test stock item located to a non-structural category
        item = StockItem.objects.create(
            batch="BBB",
            location=non_structural_location,
            part=part
        )

        # Try to relocate it to a structural location
        item.location = structural_location
        with self.assertRaises(ValidationError):
            item.save()

        # Ensure that the item did not get saved to the DB
        item.refresh_from_db()
        self.assertEqual(item.location.pk, non_structural_location.pk)

        # Try to change the non-structural location to structural while items located into it
        non_structural_location.structural = True
        with self.assertRaises(ValidationError):
            non_structural_location.full_clean()

    def test_stock_location_icon(self):
        """Test stock location icon inheritance from StockLocationType."""
        parent_location = StockLocation.objects.create(name="Parent location")

        location_type = StockLocationType.objects.create(name="Box", description="This is a very cool type of box", icon="fas fa-box")
        location = StockLocation.objects.create(name="Test location", custom_icon="fas fa-microscope", location_type=location_type, parent=parent_location)

        res = self.get(self.list_url, {"parent": str(parent_location.pk)}, expected_code=200).json()
        self.assertEqual(res[0]["icon"], "fas fa-microscope", "Custom icon from location should be returned")

        location.custom_icon = ""
        location.save()
        res = self.get(self.list_url, {"parent": str(parent_location.pk)}, expected_code=200).json()
        self.assertEqual(res[0]["icon"], "fas fa-box", "Custom icon is None, therefore it should inherit the location type icon")

        location_type.icon = ""
        location_type.save()
        res = self.get(self.list_url, {"parent": str(parent_location.pk)}, expected_code=200).json()
        self.assertEqual(res[0]["icon"], "", "Custom icon and location type icon is None, None should be returned")

    def test_stock_location_list_filter(self):
        """Test stock location list filters."""
        parent_location = StockLocation.objects.create(name="Parent location")

        location_type = StockLocationType.objects.create(name="Box", description="This is a very cool type of box", icon="fas fa-box")
        location_type2 = StockLocationType.objects.create(name="Shelf", description="This is a very cool type of shelf", icon="fas fa-shapes")
        StockLocation.objects.create(name="Test location w. type", location_type=location_type, parent=parent_location)
        StockLocation.objects.create(name="Test location w. type 2", parent=parent_location, location_type=location_type2)
        StockLocation.objects.create(name="Test location wo type", parent=parent_location)

        res = self.get(self.list_url, {"parent": str(parent_location.pk), "has_location_type": "1"}, expected_code=200).json()
        self.assertEqual(len(res), 2)
        self.assertEqual(res[0]["name"], "Test location w. type")
        self.assertEqual(res[1]["name"], "Test location w. type 2")

        res = self.get(self.list_url, {"parent": str(parent_location.pk), "location_type": str(location_type.pk)}, expected_code=200).json()
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["name"], "Test location w. type")

        res = self.get(self.list_url, {"parent": str(parent_location.pk), "has_location_type": "0"}, expected_code=200).json()
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["name"], "Test location wo type")


class StockLocationTypeTest(StockAPITestCase):
    """Tests for the StockLocationType API endpoints."""

    list_url = reverse('api-location-type-list')

    def test_list(self):
        """Test that the list endpoint works as expected."""
        location_types = [
            StockLocationType.objects.create(name="Type 1", description="Type 1 desc", icon="fas fa-box"),
            StockLocationType.objects.create(name="Type 2", description="Type 2 desc", icon="fas fa-box"),
            StockLocationType.objects.create(name="Type 3", description="Type 3 desc", icon="fas fa-box"),
        ]

        StockLocation.objects.create(name="Loc 1", location_type=location_types[0])
        StockLocation.objects.create(name="Loc 2", location_type=location_types[0])
        StockLocation.objects.create(name="Loc 3", location_type=location_types[1])

        res = self.get(self.list_url, expected_code=200).json()
        self.assertEqual(len(res), 3)
        self.assertCountEqual([r["location_count"] for r in res], [2, 1, 0])

    def test_delete(self):
        """Test that we can delete a location type via API."""
        location_type = StockLocationType.objects.create(name="Type 1", description="Type 1 desc", icon="fas fa-box")
        self.delete(reverse('api-location-type-detail', kwargs={"pk": location_type.pk}), expected_code=204)
        self.assertEqual(StockLocationType.objects.count(), 0)

    def test_create(self):
        """Test that we can create a location type via API."""
        self.post(self.list_url, {"name": "Test Type 1", "description": "Test desc 1", "icon": "fas fa-box"}, expected_code=201)
        self.assertIsNotNone(StockLocationType.objects.filter(name="Test Type 1").first())

    def test_update(self):
        """Test that we can update a location type via API."""
        location_type = StockLocationType.objects.create(name="Type 1", description="Type 1 desc", icon="fas fa-box")
        res = self.patch(reverse('api-location-type-detail', kwargs={"pk": location_type.pk}), {"icon": "fas fa-shapes"}, expected_code=200).json()
        self.assertEqual(res["icon"], "fas fa-shapes")


class StockItemListTest(StockAPITestCase):
    """Tests for the StockItem API LIST endpoint."""

    list_url = reverse('api-stock-list')

    def get_stock(self, **kwargs):
        """Filter stock and return JSON object."""
        response = self.client.get(self.list_url, format='json', data=kwargs)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Return JSON-ified data
        return response.data

    def test_top_level_filtering(self):
        """Test filtering against "top level" stock location"""
        # No filters, should return *all* items
        response = self.get(self.list_url, {}, expected_code=200)
        self.assertEqual(len(response.data), StockItem.objects.count())

        # Filter with "cascade=False" (but no location specified)
        # Should not result in any actual filtering
        response = self.get(self.list_url, {'cascade': False}, expected_code=200)
        self.assertEqual(len(response.data), StockItem.objects.count())

        # Filter with "cascade=False" for the top-level location
        response = self.get(self.list_url, {'location': 'null', 'cascade': False}, expected_code=200)
        self.assertTrue(len(response.data) < StockItem.objects.count())

        for result in response.data:
            self.assertIsNone(result['location'])

        # Filter with "cascade=True"
        response = self.get(self.list_url, {'location': 'null', 'cascade': True}, expected_code=200)
        self.assertEqual(len(response.data), StockItem.objects.count())

    def test_get_stock_list(self):
        """List *all* StockItem objects."""
        response = self.get_stock()

        self.assertEqual(len(response), 29)

    def test_filter_by_part(self):
        """Filter StockItem by Part reference."""
        response = self.get_stock(part=25)

        self.assertEqual(len(response), 17)

        response = self.get_stock(part=10004)

        self.assertEqual(len(response), 12)

    def test_filter_by_ipn(self):
        """Filter StockItem by IPN reference."""
        response = self.get_stock(IPN="R.CH")
        self.assertEqual(len(response), 3)

    def test_filter_by_location(self):
        """Filter StockItem by StockLocation reference."""
        response = self.get_stock(location=5)
        self.assertEqual(len(response), 1)

        response = self.get_stock(location=1, cascade=0)
        self.assertEqual(len(response), 7)

        response = self.get_stock(location=1, cascade=1)
        self.assertEqual(len(response), 9)

        response = self.get_stock(location=7)
        self.assertEqual(len(response), 18)

    def test_filter_by_depleted(self):
        """Filter StockItem by depleted status."""
        response = self.get_stock(depleted=1)
        self.assertEqual(len(response), 1)

        response = self.get_stock(depleted=0)
        self.assertEqual(len(response), 28)

    def test_filter_by_in_stock(self):
        """Filter StockItem by 'in stock' status."""
        response = self.get_stock(in_stock=1)
        self.assertEqual(len(response), 26)

        response = self.get_stock(in_stock=0)
        self.assertEqual(len(response), 3)

    def test_filter_by_status(self):
        """Filter StockItem by 'status' field."""
        codes = {
            StockStatus.OK.value: 27,
            StockStatus.DESTROYED.value: 1,
            StockStatus.LOST.value: 1,
            StockStatus.DAMAGED.value: 0,
            StockStatus.REJECTED.value: 0,
        }

        for code in codes.keys():
            num = codes[code]

            response = self.get_stock(status=code)
            self.assertEqual(len(response), num)

    def test_filter_by_batch(self):
        """Filter StockItem by batch code."""
        response = self.get_stock(batch='B123')
        self.assertEqual(len(response), 1)

    def test_filter_by_company(self):
        """Test that we can filter stock items by company"""
        for cmp in company.models.Company.objects.all():
            self.get_stock(company=cmp.pk)

    def test_filter_by_serialized(self):
        """Filter StockItem by serialized status."""
        response = self.get_stock(serialized=1)
        self.assertEqual(len(response), 12)

        for item in response:
            self.assertIsNotNone(item['serial'])

        response = self.get_stock(serialized=0)
        self.assertEqual(len(response), 17)

        for item in response:
            self.assertIsNone(item['serial'])

    def test_filter_by_has_batch(self):
        """Test the 'has_batch' filter, which tests if the stock item has been assigned a batch code."""
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
        """Filter StockItem by expiry status."""
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
        """Test that we can paginate results correctly."""
        for n in [1, 5, 10]:
            response = self.get_stock(limit=n)

            self.assertIn('count', response)
            self.assertIn('results', response)

            self.assertEqual(len(response['results']), n)

    def export_data(self, filters=None):
        """Helper to test exports."""
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
        """Test exporting of Stock data via the API."""
        dataset = self.export_data({})

        # Check that *all* stock item objects have been exported
        self.assertEqual(len(dataset), StockItem.objects.count())

        # Expected headers
        headers = [
            'Part ID',
            'Customer ID',
            'Location ID',
            'Location Name',
            'Parent ID',
            'Quantity',
            'Status',
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

    def test_filter_by_allocated(self):
        """Test that we can filter by "allocated" status:

        - Only return stock items which are 'allocated'
        - Either to a build order or sales order
        - Test that the results are "distinct" (no duplicated results)
        - Ref: https://github.com/inventree/InvenTree/pull/5916
        """

        # Create a build order to allocate to
        assembly = part.models.Part.objects.create(name='F Assembly', description='Assembly for filter test', assembly=True)
        component = part.models.Part.objects.create(name='F Component', description='Component for filter test', component=True)
        bom_item = part.models.BomItem.objects.create(part=assembly, sub_part=component, quantity=10)

        # Create two build orders
        bo_1 = build.models.Build.objects.create(part=assembly, quantity=10)
        bo_2 = build.models.Build.objects.create(part=assembly, quantity=20)

        # Test that two distinct build line items are created automatically
        self.assertEqual(bo_1.build_lines.count(), 1)
        self.assertEqual(bo_2.build_lines.count(), 1)
        self.assertEqual(build.models.BuildLine.objects.filter(bom_item=bom_item).count(), 2)

        build_line_1 = bo_1.build_lines.first()
        build_line_2 = bo_2.build_lines.first()

        # Allocate stock
        location = StockLocation.objects.first()
        stock_1 = StockItem.objects.create(part=component, quantity=100, location=location)
        stock_2 = StockItem.objects.create(part=component, quantity=100, location=location)
        stock_3 = StockItem.objects.create(part=component, quantity=100, location=location)

        # Allocate stock_1 to two build orders
        build.models.BuildItem.objects.create(
            stock_item=stock_1,
            build_line=build_line_1,
            quantity=5
        )

        build.models.BuildItem.objects.create(
            stock_item=stock_1,
            build_line=build_line_2,
            quantity=5
        )

        # Allocate stock_2 to 1 build orders
        build.models.BuildItem.objects.create(
            stock_item=stock_2,
            build_line=build_line_1,
            quantity=5
        )

        url = reverse('api-stock-list')

        # 3 items when just filtering by part
        response = self.get(
            url,
            {
                "part": component.pk,
                "in_stock": True
            },
            expected_code=200
        )
        self.assertEqual(len(response.data), 3)

        # 1 item when filtering by "not allocated"
        response = self.get(
            url,
            {
                "part": component.pk,
                "in_stock": True,
                "allocated": False,
            },
            expected_code=200
        )

        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["pk"], stock_3.pk)

        # 2 items when filtering by "allocated"
        response = self.get(
            url,
            {
                "part": component.pk,
                "in_stock": True,
                "allocated": True,
            },
            expected_code=200
        )

        self.assertEqual(len(response.data), 2)

        ids = [item["pk"] for item in response.data]

        self.assertIn(stock_1.pk, ids)
        self.assertIn(stock_2.pk, ids)

    def test_query_count(self):
        """Test that the number of queries required to fetch stock items is reasonable."""

        def get_stock(data, expected_status=200):
            """Helper function to fetch stock items."""
            response = self.client.get(self.list_url, data=data)
            self.assertEqual(response.status_code, expected_status)
            return response.data

        # Create a bunch of StockItem objects
        prt = Part.objects.first()

        StockItem.objects.bulk_create([
            StockItem(
                part=prt,
                quantity=1,
                level=0, tree_id=0, lft=0, rght=0,
            ) for _ in range(100)
        ])

        # List *all* stock items
        with self.assertNumQueriesLessThan(25):
            get_stock({})

        # List all stock items, with part detail
        with self.assertNumQueriesLessThan(20):
            get_stock({'part_detail': True})

        # List all stock items, with supplier_part detail
        with self.assertNumQueriesLessThan(20):
            get_stock({'supplier_part_detail': True})

        # List all stock items, with 'location' and 'tests' detail
        with self.assertNumQueriesLessThan(20):
            get_stock({'location_detail': True, 'tests': True})


class StockItemTest(StockAPITestCase):
    """Series of API tests for the StockItem API."""

    list_url = reverse('api-stock-list')

    def setUp(self):
        """Setup for all tests."""
        super().setUp()
        # Create some stock locations
        top = StockLocation.objects.create(name='A', description='top')

        StockLocation.objects.create(name='B', description='location b', parent=top)
        StockLocation.objects.create(name='C', description='location c', parent=top)

    def test_create_default_location(self):
        """Test the default location functionality, if a 'location' is not specified in the creation request."""
        # The part 'R_4K7_0603' (pk=4) has a default location specified

        response = self.post(
            self.list_url,
            data={
                'part': 4,
                'quantity': 10
            },
            expected_code=201
        )

        self.assertEqual(response.data['location'], 2)

        # What if we explicitly set the location to a different value?

        response = self.post(
            self.list_url,
            data={
                'part': 4,
                'quantity': 20,
                'location': 1,
            },
            expected_code=201
        )
        self.assertEqual(response.data['location'], 1)

        # And finally, what if we set the location explicitly to None?

        response = self.post(
            self.list_url,
            data={
                'part': 4,
                'quantity': 20,
                'location': '',
            },
            expected_code=201
        )

        self.assertEqual(response.data['location'], None)

    def test_stock_item_create(self):
        """Test creation of a StockItem via the API."""
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

    def test_stock_item_create_withsupplierpart(self):
        """Test creation of a StockItem via the API, including SupplierPart data."""
        # POST with non-existent supplier part
        response = self.post(
            self.list_url,
            data={
                'part': 1,
                'location': 1,
                'quantity': 4,
                'supplier_part': 1000991
            },
            expected_code=400
        )

        self.assertIn('The given supplier part does not exist', str(response.data))

        # POST with valid supplier part, no pack size defined
        # Get current count of number of parts
        part_4 = part.models.Part.objects.get(pk=4)
        current_count = part_4.available_stock
        response = self.post(
            self.list_url,
            data={
                'part': 4,
                'location': 1,
                'quantity': 3,
                'supplier_part': 5,
                'purchase_price': 123.45,
                'purchase_price_currency': 'USD',
            },
            expected_code=201
        )

        # Reload part, count stock again
        part_4 = part.models.Part.objects.get(pk=4)
        self.assertEqual(part_4.available_stock, current_count + 3)
        stock_4 = StockItem.objects.get(pk=response.data['pk'])
        self.assertEqual(stock_4.purchase_price, Money('123.450000', 'USD'))

        # POST with valid supplier part, no pack size defined
        # Send use_pack_size along, make sure this doesn't break stuff
        # Get current count of number of parts
        part_4 = part.models.Part.objects.get(pk=4)
        current_count = part_4.available_stock
        response = self.post(
            self.list_url,
            data={
                'part': 4,
                'location': 1,
                'quantity': 12,
                'supplier_part': 5,
                'use_pack_size': True,
                'purchase_price': 123.45,
                'purchase_price_currency': 'USD',
            },
            expected_code=201
        )
        # Reload part, count stock again
        part_4 = part.models.Part.objects.get(pk=4)
        self.assertEqual(part_4.available_stock, current_count + 12)
        stock_4 = StockItem.objects.get(pk=response.data['pk'])
        self.assertEqual(stock_4.purchase_price, Money('123.450000', 'USD'))

        # POST with valid supplier part, WITH pack size defined - but ignore
        # Supplier part 6 is a 100-pack, otherwise same as SP 5
        current_count = part_4.available_stock
        response = self.post(
            self.list_url,
            data={
                'part': 4,
                'location': 1,
                'quantity': 3,
                'supplier_part': 6,
                'use_pack_size': False,
                'purchase_price': 123.45,
                'purchase_price_currency': 'USD',
            },
            expected_code=201
        )
        # Reload part, count stock again
        part_4 = part.models.Part.objects.get(pk=4)
        self.assertEqual(part_4.available_stock, current_count + 3)
        stock_4 = StockItem.objects.get(pk=response.data['pk'])
        self.assertEqual(stock_4.purchase_price, Money('123.450000', 'USD'))

        # POST with valid supplier part, WITH pack size defined and used
        # Supplier part 6 is a 100-pack, otherwise same as SP 5
        current_count = part_4.available_stock
        response = self.post(
            self.list_url,
            data={
                'part': 4,
                'location': 1,
                'quantity': 3,
                'supplier_part': 6,
                'use_pack_size': True,
                'purchase_price': 123.45,
                'purchase_price_currency': 'USD',
            },
            expected_code=201
        )
        # Reload part, count stock again
        part_4 = part.models.Part.objects.get(pk=4)
        self.assertEqual(part_4.available_stock, current_count + 3 * 100)
        stock_4 = StockItem.objects.get(pk=response.data['pk'])
        self.assertEqual(stock_4.purchase_price, Money('1.234500', 'USD'))

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
            self.assertTrue(str(i) in sn)

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

        response = self.post(self.list_url, data, expected_code=201)

        self.assertIsNone(response.data['expiry_date'])

        # Second test - create a new StockItem with an explicit expiry date
        data['expiry_date'] = '2022-12-12'

        response = self.post(self.list_url, data, expected_code=201)

        self.assertIsNotNone(response.data['expiry_date'])
        self.assertEqual(response.data['expiry_date'], '2022-12-12')

        # Third test - create a new StockItem for a Part which has a default expiry time
        data = {
            'part': 25,
            'quantity': 10
        }

        response = self.post(self.list_url, data, expected_code=201)

        # Expected expiry date is 10 days in the future
        expiry = datetime.now().date() + timedelta(10)

        self.assertEqual(response.data['expiry_date'], expiry.isoformat())

        # Test result when sending a blank value
        data['expiry_date'] = None

        response = self.post(self.list_url, data, expected_code=201)
        self.assertEqual(response.data['expiry_date'], expiry.isoformat())

    def test_purchase_price(self):
        """Test that we can correctly read and adjust purchase price information via the API."""
        url = reverse('api-stock-detail', kwargs={'pk': 1})

        data = self.get(url, expected_code=200).data

        # Check fixture values
        self.assertEqual(data['purchase_price'], '123.000000')
        self.assertEqual(data['purchase_price_currency'], 'AUD')

        # Update just the amount
        data = self.patch(
            url,
            {
                'purchase_price': 456
            },
            expected_code=200
        ).data

        self.assertEqual(data['purchase_price'], '456.000000')
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
        """Test that stock item can be installed into antoher item, via the API."""
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

    def test_return_from_customer(self):
        """Test that we can return a StockItem from a customer, via the API"""
        # Assign item to customer
        item = StockItem.objects.get(pk=521)
        customer = company.models.Company.objects.get(pk=4)

        item.customer = customer
        item.save()

        n_entries = item.tracking_info_count

        url = reverse('api-stock-item-return', kwargs={'pk': item.pk})

        # Empty POST will fail
        response = self.post(
            url, {},
            expected_code=400
        )

        self.assertIn('This field is required', str(response.data['location']))

        response = self.post(
            url,
            {
                'location': '1',
                'notes': 'Returned from this customer for testing',
            },
            expected_code=201,
        )

        item.refresh_from_db()

        # A new stock tracking entry should have been created
        self.assertEqual(n_entries + 1, item.tracking_info_count)

        # The item is now in stock
        self.assertIsNone(item.customer)

    def test_convert_to_variant(self):
        """Test that we can convert a StockItem to a variant part via the API"""
        category = part.models.PartCategory.objects.get(pk=3)

        # First, construct a set of template / variant parts
        master_part = part.models.Part.objects.create(
            name='Master', description='Master part which has variants',
            category=category,
            is_template=True,
        )

        variants = []

        # Construct a set of variant parts
        for color in ['Red', 'Green', 'Blue', 'Yellow', 'Pink', 'Black']:
            variants.append(part.models.Part.objects.create(
                name=f"{color} Variant", description="Variant part with a specific color",
                variant_of=master_part,
                category=category,
            ))

        stock_item = StockItem.objects.create(
            part=master_part,
            quantity=1000,
        )

        url = reverse('api-stock-item-convert', kwargs={'pk': stock_item.pk})

        # Attempt to convert to a part which does not exist
        response = self.post(
            url,
            {
                'part': 999999,
            },
            expected_code=400,
        )

        self.assertIn('object does not exist', str(response.data['part']))

        # Attempt to convert to a part which is not a valid option
        response = self.post(
            url,
            {
                'part': 1,
            },
            expected_code=400
        )

        self.assertIn('Selected part is not a valid option', str(response.data['part']))

        for variant in variants:
            response = self.post(
                url,
                {
                    'part': variant.pk,
                },
                expected_code=201,
            )

            stock_item.refresh_from_db()
            self.assertEqual(stock_item.part, variant)

    def test_set_status(self):
        """Test API endpoint for setting StockItem status"""
        url = reverse('api-stock-change-status')

        prt = Part.objects.first()

        # Create a bunch of items
        items = [
            StockItem.objects.create(part=prt, quantity=10) for _ in range(10)
        ]

        for item in items:
            item.refresh_from_db()
            self.assertEqual(item.status, StockStatus.OK.value)

        data = {
            'items': [item.pk for item in items],
            'status': StockStatus.DAMAGED.value,
        }

        self.post(url, data, expected_code=201)

        # Check that the item has been updated correctly
        for item in items:
            item.refresh_from_db()
            self.assertEqual(item.status, StockStatus.DAMAGED.value)
            self.assertEqual(item.tracking_info.count(), 1)

        # Same test, but with one item unchanged
        items[0].status = StockStatus.ATTENTION.value
        items[0].save()

        data['status'] = StockStatus.ATTENTION.value

        self.post(url, data, expected_code=201)

        for item in items:
            item.refresh_from_db()
            self.assertEqual(item.status, StockStatus.ATTENTION.value)
            self.assertEqual(item.tracking_info.count(), 2)

            tracking = item.tracking_info.last()
            self.assertEqual(tracking.tracking_type, StockHistoryCode.EDITED.value)


class StocktakeTest(StockAPITestCase):
    """Series of tests for the Stocktake API."""

    def test_action(self):
        """Test each stocktake action endpoint, for validation."""
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
        """Test stock transfers."""
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
    """Tests for stock item deletion via the API."""

    def test_delete(self):
        """Test stock item deletion."""
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
    """Tests for StockTestResult APIs."""

    def get_url(self):
        """Helper function to get test-result api url."""
        return reverse('api-stock-test-result-list')

    def test_list(self):
        """Test list endpoint."""
        url = self.get_url()
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 4)

        response = self.client.get(url, data={'stock_item': 105})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 4)

    def test_post_fail(self):
        """Test failing posts."""
        # Attempt to post a new test result without specifying required data

        url = self.get_url()

        self.post(
            url,
            data={
                'test': 'A test',
                'result': True,
            },
            expected_code=400
        )

        # This one should pass!
        self.post(
            url,
            data={
                'test': 'A test',
                'stock_item': 105,
                'result': True,
            },
            expected_code=201
        )

    def test_post(self):
        """Test creation of a new test result."""
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

        response = self.post(url, data, expected_code=201)

        response = self.client.get(url)
        self.assertEqual(len(response.data), n + 1)

        # And read out again
        response = self.client.get(url, data={'test': 'Checked Steam Valve'})

        self.assertEqual(len(response.data), 1)

        test = response.data[0]
        self.assertEqual(test['value'], '150kPa')
        self.assertEqual(test['user'], self.user.pk)

    def test_post_bitmap(self):
        """2021-08-25.

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

    def test_bulk_delete(self):
        """Test that the BulkDelete endpoint works for this model"""
        n = StockItemTestResult.objects.count()

        tests = []

        url = reverse('api-stock-test-result-list')

        # Create some objects (via the API)
        for _ii in range(50):
            response = self.post(
                url,
                {
                    'stock_item': 1,
                    'test': f"Some test {_ii}",
                    'result': True,
                    'value': 'Test result value'
                },
                expected_code=201
            )

            tests.append(response.data['pk'])

        self.assertEqual(StockItemTestResult.objects.count(), n + 50)

        # Attempt a delete without providing items
        self.delete(
            url,
            {},
            expected_code=400,
        )

        # Now, let's delete all the newly created items with a single API request
        # However, we will provide incorrect filters
        response = self.delete(
            url,
            {
                'items': tests,
                'filters': {
                    'stock_item': 10,
                }
            },
            expected_code=204
        )

        self.assertEqual(StockItemTestResult.objects.count(), n + 50)

        # Try again, but with the correct filters this time
        response = self.delete(
            url,
            {
                'items': tests,
                'filters': {
                    'stock_item': 1,
                }
            },
            expected_code=204
        )

        self.assertEqual(StockItemTestResult.objects.count(), n)


class StockAssignTest(StockAPITestCase):
    """Unit tests for the stock assignment API endpoint, where stock items are manually assigned to a customer."""

    URL = reverse('api-stock-assign')

    def test_invalid(self):
        """Test invalid assign."""
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
            status=StockStatus.DESTROYED.value,
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
        """Test valid assign."""
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
    """Unit tests for merging stock items via the API."""

    URL = reverse('api-stock-merge')

    @classmethod
    def setUpTestData(cls):
        """Setup for all tests."""
        super().setUpTestData()

        cls.part = part.models.Part.objects.get(pk=25)
        cls.loc = StockLocation.objects.get(pk=1)
        cls.sp_1 = company.models.SupplierPart.objects.get(pk=100)
        cls.sp_2 = company.models.SupplierPart.objects.get(pk=101)

        cls.item_1 = StockItem.objects.create(
            part=cls.part,
            supplier_part=cls.sp_1,
            quantity=100,
        )

        cls.item_2 = StockItem.objects.create(
            part=cls.part,
            supplier_part=cls.sp_2,
            quantity=100,
        )

        cls.item_3 = StockItem.objects.create(
            part=cls.part,
            supplier_part=cls.sp_2,
            quantity=50,
        )

    def test_missing_data(self):
        """Test responses which are missing required data."""
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
        """Test responses which have invalid data."""
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
        """Test valid merging of stock items."""
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


class StockMetadataAPITest(InvenTreeAPITestCase):
    """Unit tests for the various metadata endpoints of API."""

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
        'stock_location.change',
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
            'api-location-metadata': StockLocation,
            'api-stock-test-result-metadata': StockItemTestResult,
            'api-stock-item-metadata': StockItem,
        }.items():
            self.metatester(apikey, model)
