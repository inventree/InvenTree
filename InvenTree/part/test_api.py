"""Unit tests for the various part API endpoints"""

from django.urls import reverse

import PIL
from rest_framework import status
from rest_framework.test import APIClient

import build.models
import order.models
from common.models import InvenTreeSetting
from company.models import Company
from InvenTree.api_tester import InvenTreeAPITestCase
from InvenTree.status_codes import (BuildStatus, PurchaseOrderStatus,
                                    StockStatus)
from part.models import (BomItem, BomItemSubstitute, Part, PartCategory,
                         PartRelated)
from stock.models import StockItem, StockLocation


class PartCategoryAPITest(InvenTreeAPITestCase):
    """Unit tests for the PartCategory API."""

    fixtures = [
        'category',
        'part',
        'location',
        'bom',
        'company',
        'test_templates',
        'manufacturer_part',
        'supplier_part',
        'order',
        'stock',
    ]

    roles = [
        'part.change',
        'part.add',
        'part.delete',
        'part_category.change',
        'part_category.add',
    ]

    def test_category_list(self):
        """Test the PartCategoryList API endpoint"""
        url = reverse('api-part-category-list')

        response = self.get(url, expected_code=200)

        self.assertEqual(len(response.data), 8)

        # Filter by parent, depth=1
        response = self.get(
            url,
            {
                'parent': 1,
                'cascade': False,
            },
            expected_code=200
        )

        self.assertEqual(len(response.data), 3)

        # Filter by parent, cascading
        response = self.get(
            url,
            {
                'parent': 1,
                'cascade': True,
            },
            expected_code=200,
        )

        self.assertEqual(len(response.data), 5)

    def test_category_metadata(self):
        """Test metadata endpoint for the PartCategory."""
        cat = PartCategory.objects.get(pk=1)

        cat.metadata = {
            'foo': 'bar',
            'water': 'melon',
            'abc': 'xyz',
        }

        cat.set_metadata('abc', 'ABC')

        response = self.get(reverse('api-part-category-metadata', kwargs={'pk': 1}), expected_code=200)

        metadata = response.data['metadata']

        self.assertEqual(metadata['foo'], 'bar')
        self.assertEqual(metadata['water'], 'melon')
        self.assertEqual(metadata['abc'], 'ABC')


class PartOptionsAPITest(InvenTreeAPITestCase):
    """Tests for the various OPTIONS endpoints in the /part/ API.

    Ensure that the required field details are provided!
    """

    roles = [
        'part.add',
    ]

    def test_part(self):
        """Test the Part API OPTIONS."""
        actions = self.getActions(reverse('api-part-list'))['POST']

        # Check that a bunch o' fields are contained
        for f in ['assembly', 'component', 'description', 'image', 'IPN']:
            self.assertTrue(f in actions.keys())

        # Active is a 'boolean' field
        active = actions['active']

        self.assertTrue(active['default'])
        self.assertEqual(active['help_text'], 'Is this part active?')
        self.assertEqual(active['type'], 'boolean')
        self.assertEqual(active['read_only'], False)

        # String field
        ipn = actions['IPN']
        self.assertEqual(ipn['type'], 'string')
        self.assertFalse(ipn['required'])
        self.assertEqual(ipn['max_length'], 100)
        self.assertEqual(ipn['help_text'], 'Internal Part Number')

        # Related field
        category = actions['category']

        self.assertEqual(category['type'], 'related field')
        self.assertTrue(category['required'])
        self.assertFalse(category['read_only'])
        self.assertEqual(category['label'], 'Category')
        self.assertEqual(category['model'], 'partcategory')
        self.assertEqual(category['api_url'], reverse('api-part-category-list'))
        self.assertEqual(category['help_text'], 'Part category')

    def test_category(self):
        """Test the PartCategory API OPTIONS endpoint."""
        actions = self.getActions(reverse('api-part-category-list'))

        # actions should *not* contain 'POST' as we do not have the correct role
        self.assertFalse('POST' in actions)

        self.assignRole('part_category.add')

        actions = self.getActions(reverse('api-part-category-list'))['POST']

        name = actions['name']

        self.assertTrue(name['required'])
        self.assertEqual(name['label'], 'Name')

        loc = actions['default_location']
        self.assertEqual(loc['api_url'], reverse('api-location-list'))

    def test_bom_item(self):
        """Test the BomItem API OPTIONS endpoint."""
        actions = self.getActions(reverse('api-bom-list'))['POST']

        inherited = actions['inherited']

        self.assertEqual(inherited['type'], 'boolean')

        # 'part' reference
        part = actions['part']

        self.assertTrue(part['required'])
        self.assertFalse(part['read_only'])
        self.assertTrue(part['filters']['assembly'])

        # 'sub_part' reference
        sub_part = actions['sub_part']

        self.assertTrue(sub_part['required'])
        self.assertEqual(sub_part['type'], 'related field')
        self.assertTrue(sub_part['filters']['component'])


class PartAPITest(InvenTreeAPITestCase):
    """Series of tests for the Part DRF API.

    - Tests for Part API
    - Tests for PartCategory API
    """

    fixtures = [
        'category',
        'part',
        'location',
        'bom',
        'test_templates',
        'company',
    ]

    roles = [
        'part.change',
        'part.add',
        'part.delete',
        'part_category.change',
        'part_category.add',
    ]

    def test_get_categories(self):
        """Test that we can retrieve list of part categories, with various filtering options."""
        url = reverse('api-part-category-list')

        # Request *all* part categories
        response = self.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 8)

        # Request top-level part categories only
        response = self.get(
            url,
            {
                'parent': 'null',
            },
            format='json'
        )

        self.assertEqual(len(response.data), 2)

        # Children of PartCategory<1>, cascade
        response = self.get(
            url,
            {
                'parent': 1,
                'cascade': 'true',
            },
            format='json',
        )

        self.assertEqual(len(response.data), 5)

        # Children of PartCategory<1>, do not cascade
        response = self.get(
            url,
            {
                'parent': 1,
                'cascade': 'false',
            },
            format='json',
        )

        self.assertEqual(len(response.data), 3)

    def test_add_categories(self):
        """Check that we can add categories."""
        data = {
            'name': 'Animals',
            'description': 'All animals go here'
        }

        url = reverse('api-part-category-list')
        response = self.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        parent = response.data['pk']

        # Add some sub-categories to the top-level 'Animals' category
        for animal in ['cat', 'dog', 'zebra']:
            data = {
                'name': animal,
                'description': 'A sort of animal',
                'parent': parent,
            }
            response = self.post(url, data, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(response.data['parent'], parent)
            self.assertEqual(response.data['name'], animal)
            self.assertEqual(response.data['pathstring'], 'Animals/' + animal)

        # There should be now 8 categories
        response = self.get(url, format='json')
        self.assertEqual(len(response.data), 12)

    def test_cat_detail(self):
        """Test the PartCategoryDetail API endpoint"""
        url = reverse('api-part-category-detail', kwargs={'pk': 4})
        response = self.get(url, format='json')

        # Test that we have retrieved the category
        self.assertEqual(response.data['description'], 'Integrated Circuits')
        self.assertEqual(response.data['parent'], 1)

        # Change some data and post it back
        data = response.data
        data['name'] = 'Changing category'
        data['parent'] = None
        data['description'] = 'Changing the description'
        response = self.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['description'], 'Changing the description')
        self.assertIsNone(response.data['parent'])

    def test_filter_parts(self):
        """Test part filtering using the API"""
        url = reverse('api-part-list')
        data = {'cascade': True}
        response = self.get(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), Part.objects.count())

        # Test filtering parts by category
        data = {'category': 2}
        response = self.get(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # There should only be 2 objects in category C
        self.assertEqual(len(response.data), 2)

        for part in response.data:
            self.assertEqual(part['category'], 2)

    def test_filter_by_related(self):
        """Test that we can filter by the 'related' status"""
        url = reverse('api-part-list')

        # Initially there are no relations, so this should return zero results
        response = self.get(url, {'related': 1}, expected_code=200)
        self.assertEqual(len(response.data), 0)

        # Add some relationships
        PartRelated.objects.create(
            part_1=Part.objects.get(pk=1),
            part_2=Part.objects.get(pk=2),
        )

        PartRelated.objects.create(
            part_2=Part.objects.get(pk=1),
            part_1=Part.objects.get(pk=3)
        )

        response = self.get(url, {'related': 1}, expected_code=200)
        self.assertEqual(len(response.data), 2)

    def test_include_children(self):
        """Test the special 'include_child_categories' flag.

        If provided, parts are provided for ANY child category (recursive)
        """
        url = reverse('api-part-list')
        data = {'category': 1, 'cascade': True}

        # Now request to include child categories
        response = self.get(url, data, format='json')

        # Now there should be 5 total parts
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_test_templates(self):
        """Test the PartTestTemplate API"""
        url = reverse('api-part-test-template-list')

        # List ALL items
        response = self.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 7)

        # Request for a particular part
        response = self.get(url, data={'part': 10000})
        self.assertEqual(len(response.data), 5)

        response = self.get(url, data={'part': 10004})
        self.assertEqual(len(response.data), 7)

        # Try to post a new object (missing description)
        response = self.post(
            url,
            data={
                'part': 10000,
                'test_name': 'My very first test',
                'required': False,
            }
        )

        self.assertEqual(response.status_code, 400)

        # Try to post a new object (should succeed)
        response = self.post(
            url,
            data={
                'part': 10000,
                'test_name': 'New Test',
                'required': True,
                'description': 'a test description'
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Try to post a new test with the same name (should fail)
        response = self.post(
            url,
            data={
                'part': 10004,
                'test_name': "   newtest",
                'description': 'dafsdf',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Try to post a new test against a non-trackable part (should fail)
        response = self.post(
            url,
            data={
                'part': 1,
                'test_name': 'A simple test',
            }
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_thumbs(self):
        """Return list of part thumbnails."""
        url = reverse('api-part-thumbs')

        response = self.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_paginate(self):
        """Test pagination of the Part list API."""
        for n in [1, 5, 10]:
            response = self.get(reverse('api-part-list'), {'limit': n})

            data = response.data

            self.assertIn('count', data)
            self.assertIn('results', data)

            self.assertEqual(len(data['results']), n)

    def test_default_values(self):
        """Tests for 'default' values:

        Ensure that unspecified fields revert to "default" values
        (as specified in the model field definition)
        """
        url = reverse('api-part-list')

        response = self.post(url, {
            'name': 'all defaults',
            'description': 'my test part',
            'category': 1,
        })

        data = response.data

        # Check that the un-specified fields have used correct default values
        self.assertTrue(data['active'])
        self.assertFalse(data['virtual'])

        # By default, parts are purchaseable
        self.assertTrue(data['purchaseable'])

        # Set the default 'purchaseable' status to True
        InvenTreeSetting.set_setting(
            'PART_PURCHASEABLE',
            True,
            self.user
        )

        response = self.post(url, {
            'name': 'all defaults',
            'description': 'my test part 2',
            'category': 1,
        })

        # Part should now be purchaseable by default
        self.assertTrue(response.data['purchaseable'])

        # "default" values should not be used if the value is specified
        response = self.post(url, {
            'name': 'all defaults',
            'description': 'my test part 2',
            'category': 1,
            'active': False,
            'purchaseable': False,
        })

        self.assertFalse(response.data['active'])
        self.assertFalse(response.data['purchaseable'])

    def test_initial_stock(self):
        """Tests for initial stock quantity creation."""
        url = reverse('api-part-list')

        # Track how many parts exist at the start of this test
        n = Part.objects.count()

        # Set up required part data
        data = {
            'category': 1,
            'name': "My lil' test part",
            'description': 'A part with which to test',
        }

        # Signal that we want to add initial stock
        data['initial_stock'] = True

        # Post without a quantity
        response = self.post(url, data, expected_code=400)
        self.assertIn('initial_stock_quantity', response.data)

        # Post with an invalid quantity
        data['initial_stock_quantity'] = "ax"
        response = self.post(url, data, expected_code=400)
        self.assertIn('initial_stock_quantity', response.data)

        # Post with a negative quantity
        data['initial_stock_quantity'] = -1
        response = self.post(url, data, expected_code=400)
        self.assertIn('Must be greater than zero', response.data['initial_stock_quantity'])

        # Post with a valid quantity
        data['initial_stock_quantity'] = 12345

        response = self.post(url, data, expected_code=400)
        self.assertIn('initial_stock_location', response.data)

        # Check that the number of parts has not increased (due to form failures)
        self.assertEqual(Part.objects.count(), n)

        # Now, set a location
        data['initial_stock_location'] = 1

        response = self.post(url, data, expected_code=201)

        # Check that the part has been created
        self.assertEqual(Part.objects.count(), n + 1)

        pk = response.data['pk']

        new_part = Part.objects.get(pk=pk)

        self.assertEqual(new_part.total_stock, 12345)

    def test_initial_supplier_data(self):
        """Tests for initial creation of supplier / manufacturer data."""
        url = reverse('api-part-list')

        n = Part.objects.count()

        # Set up initial part data
        data = {
            'category': 1,
            'name': 'Buy Buy Buy',
            'description': 'A purchaseable part',
            'purchaseable': True,
        }

        # Signal that we wish to create initial supplier data
        data['add_supplier_info'] = True

        # Specify MPN but not manufacturer
        data['MPN'] = 'MPN-123'

        response = self.post(url, data, expected_code=400)
        self.assertIn('manufacturer', response.data)

        # Specify manufacturer but not MPN
        del data['MPN']
        data['manufacturer'] = 1
        response = self.post(url, data, expected_code=400)
        self.assertIn('MPN', response.data)

        # Specify SKU but not supplier
        del data['manufacturer']
        data['SKU'] = 'SKU-123'
        response = self.post(url, data, expected_code=400)
        self.assertIn('supplier', response.data)

        # Specify supplier but not SKU
        del data['SKU']
        data['supplier'] = 1
        response = self.post(url, data, expected_code=400)
        self.assertIn('SKU', response.data)

        # Check that no new parts have been created
        self.assertEqual(Part.objects.count(), n)

        # Now, fully specify the details
        data['SKU'] = 'SKU-123'
        data['supplier'] = 3
        data['MPN'] = 'MPN-123'
        data['manufacturer'] = 6

        response = self.post(url, data, expected_code=201)

        self.assertEqual(Part.objects.count(), n + 1)

        pk = response.data['pk']

        new_part = Part.objects.get(pk=pk)

        # Check that there is a new manufacturer part *and* a new supplier part
        self.assertEqual(new_part.supplier_parts.count(), 1)
        self.assertEqual(new_part.manufacturer_parts.count(), 1)

    def test_strange_chars(self):
        """Test that non-standard ASCII chars are accepted."""
        url = reverse('api-part-list')

        name = "KaltgerÃ¤testecker"
        description = "Gerät"

        data = {
            "name": name,
            "description": description,
            "category": 2
        }

        response = self.post(url, data, expected_code=201)

        self.assertEqual(response.data['name'], name)
        self.assertEqual(response.data['description'], description)

    def test_template_filters(self):
        """Unit tests for API filters related to template parts:

        - variant_of : Return children of specified part
        - ancestor : Return descendants of specified part

        Uses the 'chair template' part (pk=10000)
        """
        # Rebuild the MPTT structure before running these tests
        Part.objects.rebuild()

        url = reverse('api-part-list')

        response = self.get(
            url,
            {
                'variant_of': 10000,
            },
            expected_code=200
        )

        # 3 direct children of template part
        self.assertEqual(len(response.data), 3)

        response = self.get(
            url,
            {
                'ancestor': 10000,
            },
            expected_code=200,
        )

        # 4 total descendants
        self.assertEqual(len(response.data), 4)

        # Use the 'green chair' as our reference
        response = self.get(
            url,
            {
                'variant_of': 10003,
            },
            expected_code=200,
        )

        self.assertEqual(len(response.data), 1)

        response = self.get(
            url,
            {
                'ancestor': 10003,
            },
            expected_code=200,
        )

        self.assertEqual(len(response.data), 1)

        # Add some more variants

        p = Part.objects.get(pk=10004)

        for i in range(100):
            Part.objects.create(
                name=f'Chair variant {i}',
                description='A new chair variant',
                variant_of=p,
            )

        # There should still be only one direct variant
        response = self.get(
            url,
            {
                'variant_of': 10003,
            },
            expected_code=200,
        )

        self.assertEqual(len(response.data), 1)

        # However, now should be 101 descendants
        response = self.get(
            url,
            {
                'ancestor': 10003,
            },
            expected_code=200,
        )

        self.assertEqual(len(response.data), 101)

    def test_variant_stock(self):
        """Unit tests for the 'variant_stock' annotation, which provides a stock count for *variant* parts."""
        # Ensure the MPTT structure is in a known state before running tests
        Part.objects.rebuild()

        # Initially, there are no "chairs" in stock,
        # so each 'chair' template should report variant_stock=0
        url = reverse('api-part-list')

        # Look at the "detail" URL for the master chair template
        response = self.get('/api/part/10000/', {}, expected_code=200)

        # This part should report 'zero' as variant stock
        self.assertEqual(response.data['variant_stock'], 0)

        # Grab a list of all variant chairs *under* the master template
        response = self.get(
            url,
            {
                'ancestor': 10000,
            },
            expected_code=200,
        )

        # 4 total descendants
        self.assertEqual(len(response.data), 4)

        for variant in response.data:
            self.assertEqual(variant['variant_stock'], 0)

        # Now, let's make some variant stock
        for variant in Part.objects.get(pk=10000).get_descendants(include_self=False):
            StockItem.objects.create(
                part=variant,
                quantity=100,
            )

        response = self.get('/api/part/10000/', {}, expected_code=200)

        self.assertEqual(response.data['in_stock'], 0)
        self.assertEqual(response.data['variant_stock'], 400)

        # Check that each variant reports the correct stock quantities
        response = self.get(
            url,
            {
                'ancestor': 10000,
            },
            expected_code=200,
        )

        expected_variant_stock = {
            10001: 0,
            10002: 0,
            10003: 100,
            10004: 0,
        }

        for variant in response.data:
            self.assertEqual(variant['in_stock'], 100)
            self.assertEqual(variant['variant_stock'], expected_variant_stock[variant['pk']])

        # Add some 'sub variants' for the green chair variant
        green_chair = Part.objects.get(pk=10004)

        for i in range(10):
            gcv = Part.objects.create(
                name=f"GC Var {i}",
                description="Green chair variant",
                variant_of=green_chair,
            )

            StockItem.objects.create(
                part=gcv,
                quantity=50,
            )

        # Spot check of some values
        response = self.get('/api/part/10000/', {})
        self.assertEqual(response.data['variant_stock'], 900)

        response = self.get('/api/part/10004/', {})
        self.assertEqual(response.data['variant_stock'], 500)

    def test_part_download(self):
        """Test download of part data via the API."""
        url = reverse('api-part-list')

        required_cols = [
            'id',
            'name',
            'description',
            'in_stock',
            'category_name',
            'keywords',
            'is_template',
            'virtual',
            'trackable',
            'active',
            'notes',
            'creation_date',
        ]

        excluded_cols = [
            'lft', 'rght', 'level', 'tree_id',
            'metadata',
        ]

        with self.download_file(
            url,
            {
                'export': 'csv',
            },
            expected_fn='InvenTree_Parts.csv',
        ) as fo:

            data = self.process_csv(
                fo,
                excluded_cols=excluded_cols,
                required_cols=required_cols,
                required_rows=Part.objects.count(),
            )

            for row in data:
                part = Part.objects.get(pk=row['id'])

                if part.IPN:
                    self.assertEqual(part.IPN, row['IPN'])

                self.assertEqual(part.name, row['name'])
                self.assertEqual(part.description, row['description'])

                if part.category:
                    self.assertEqual(part.category.name, row['category_name'])


class PartDetailTests(InvenTreeAPITestCase):
    """Test that we can create / edit / delete Part objects via the API."""

    fixtures = [
        'category',
        'part',
        'location',
        'bom',
        'company',
        'test_templates',
        'manufacturer_part',
        'supplier_part',
        'order',
        'stock',
    ]

    roles = [
        'part.change',
        'part.add',
        'part.delete',
        'part_category.change',
        'part_category.add',
    ]

    def test_part_operations(self):
        """Test that Part instances can be adjusted via the API"""
        n = Part.objects.count()

        # Create a part
        response = self.post(
            reverse('api-part-list'),
            {
                'name': 'my test api part',
                'description': 'a part created with the API',
                'category': 1,
            }
        )

        self.assertEqual(response.status_code, 201)

        pk = response.data['pk']

        # Check that a new part has been added
        self.assertEqual(Part.objects.count(), n + 1)

        part = Part.objects.get(pk=pk)

        self.assertEqual(part.name, 'my test api part')

        # Edit the part
        url = reverse('api-part-detail', kwargs={'pk': pk})

        # Let's change the name of the part

        response = self.patch(url, {
            'name': 'a new better name',
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['pk'], pk)
        self.assertEqual(response.data['name'], 'a new better name')

        part = Part.objects.get(pk=pk)

        # Name has been altered
        self.assertEqual(part.name, 'a new better name')

        # Part count should not have changed
        self.assertEqual(Part.objects.count(), n + 1)

        # Now, try to set the name to the *same* value
        # 2021-06-22 this test is to check that the "duplicate part" checks don't do strange things
        response = self.patch(url, {
            'name': 'a new better name',
        })

        self.assertEqual(response.status_code, 200)

        # Try to remove the part
        response = self.delete(url)

        # As the part is 'active' we cannot delete it
        self.assertEqual(response.status_code, 405)

        # So, let's make it not active
        response = self.patch(url, {'active': False}, expected_code=200)

        response = self.delete(url)
        self.assertEqual(response.status_code, 204)

        # Part count should have reduced
        self.assertEqual(Part.objects.count(), n)

    def test_duplicates(self):
        """Check that trying to create 'duplicate' parts results in errors."""
        # Create a part
        response = self.post(reverse('api-part-list'), {
            'name': 'part',
            'description': 'description',
            'IPN': 'IPN-123',
            'category': 1,
            'revision': 'A',
        })

        self.assertEqual(response.status_code, 201)

        n = Part.objects.count()

        # Check that we cannot create a duplicate in a different category
        response = self.post(reverse('api-part-list'), {
            'name': 'part',
            'description': 'description',
            'IPN': 'IPN-123',
            'category': 2,
            'revision': 'A',
        })

        self.assertEqual(response.status_code, 400)

        # Check that only 1 matching part exists
        parts = Part.objects.filter(
            name='part',
            description='description',
            IPN='IPN-123'
        )

        self.assertEqual(parts.count(), 1)

        # A new part should *not* have been created
        self.assertEqual(Part.objects.count(), n)

        # But a different 'revision' *can* be created
        response = self.post(reverse('api-part-list'), {
            'name': 'part',
            'description': 'description',
            'IPN': 'IPN-123',
            'category': 2,
            'revision': 'B',
        })

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Part.objects.count(), n + 1)

        # Now, check that we cannot *change* an existing part to conflict
        pk = response.data['pk']

        url = reverse('api-part-detail', kwargs={'pk': pk})

        # Attempt to alter the revision code
        response = self.patch(
            url,
            {
                'revision': 'A',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 400)

        # But we *can* change it to a unique revision code
        response = self.patch(
            url,
            {
                'revision': 'C',
            }
        )

        self.assertEqual(response.status_code, 200)

    def test_image_upload(self):
        """Test that we can upload an image to the part API."""
        self.assignRole('part.add')

        # Create a new part
        response = self.post(
            reverse('api-part-list'),
            {
                'name': 'imagine',
                'description': 'All the people',
                'category': 1,
            },
            expected_code=201
        )

        pk = response.data['pk']

        url = reverse('api-part-detail', kwargs={'pk': pk})

        p = Part.objects.get(pk=pk)

        # Part should not have an image!
        with self.assertRaises(ValueError):
            print(p.image.file)

        # Create a custom APIClient for file uploads
        # Ref: https://stackoverflow.com/questions/40453947/how-to-generate-a-file-upload-test-request-with-django-rest-frameworks-apireq
        upload_client = APIClient()
        upload_client.force_authenticate(user=self.user)

        # Try to upload a non-image file
        with open('dummy_image.txt', 'w') as dummy_image:
            dummy_image.write('hello world')

        with open('dummy_image.txt', 'rb') as dummy_image:
            response = upload_client.patch(
                url,
                {
                    'image': dummy_image,
                },
                format='multipart',
            )

            self.assertEqual(response.status_code, 400)
            self.assertIn('Upload a valid image', str(response.data))

        # Now try to upload a valid image file, in multiple formats
        for fmt in ['jpg', 'j2k', 'png', 'bmp', 'webp']:
            fn = f'dummy_image.{fmt}'

            img = PIL.Image.new('RGB', (128, 128), color='red')
            img.save(fn)

            with open(fn, 'rb') as dummy_image:
                response = upload_client.patch(
                    url,
                    {
                        'image': dummy_image,
                    },
                    format='multipart',
                )

                self.assertEqual(response.status_code, 200)

            # And now check that the image has been set
            p = Part.objects.get(pk=pk)
            self.assertIsNotNone(p.image)

    def test_details(self):
        """Test that the required details are available."""
        p = Part.objects.get(pk=1)

        url = reverse('api-part-detail', kwargs={'pk': 1})

        data = self.get(url, expected_code=200).data

        # How many parts are 'on order' for this part?
        lines = order.models.PurchaseOrderLineItem.objects.filter(
            part__part__pk=1,
            order__status__in=PurchaseOrderStatus.OPEN,
        )

        on_order = 0

        # Calculate the "on_order" quantity by hand,
        # to check it matches the API value
        for line in lines:
            on_order += line.quantity
            on_order -= line.received

        self.assertEqual(on_order, data['ordering'])
        self.assertEqual(on_order, p.on_order)

        # Some other checks
        self.assertEqual(data['in_stock'], 9000)
        self.assertEqual(data['unallocated_stock'], 9000)

    def test_part_metadata(self):
        """Tests for the part metadata endpoint."""
        url = reverse('api-part-metadata', kwargs={'pk': 1})

        part = Part.objects.get(pk=1)

        # Metadata is initially null
        self.assertIsNone(part.metadata)

        part.metadata = {'foo': 'bar'}
        part.save()

        response = self.get(url, expected_code=200)

        self.assertEqual(response.data['metadata']['foo'], 'bar')

        # Add more data via the API
        # Using the 'patch' method causes the new data to be merged in
        self.patch(
            url,
            {
                'metadata': {
                    'hello': 'world',
                }
            },
            expected_code=200
        )

        part.refresh_from_db()

        self.assertEqual(part.metadata['foo'], 'bar')
        self.assertEqual(part.metadata['hello'], 'world')

        # Now, issue a PUT request (existing data will be replacted)
        self.put(
            url,
            {
                'metadata': {
                    'x': 'y'
                },
            },
            expected_code=200
        )

        part.refresh_from_db()

        self.assertFalse('foo' in part.metadata)
        self.assertFalse('hello' in part.metadata)
        self.assertEqual(part.metadata['x'], 'y')


class PartAPIAggregationTest(InvenTreeAPITestCase):
    """Tests to ensure that the various aggregation annotations are working correctly..."""

    fixtures = [
        'category',
        'company',
        'part',
        'location',
        'bom',
        'test_templates',
        'build',
        'location',
        'stock',
        'sales_order',
    ]

    roles = [
        'part.view',
        'part.change',
    ]

    def setUp(self):
        """Create test data as part of setup routine"""
        super().setUp()

        # Ensure the part "variant" tree is correctly structured
        Part.objects.rebuild()

        # Add a new part
        self.part = Part.objects.create(
            name='Banana',
            description='This is a banana',
            category=PartCategory.objects.get(pk=1),
        )

        # Create some stock items associated with the part

        # First create 600 units which are OK
        StockItem.objects.create(part=self.part, quantity=100)
        StockItem.objects.create(part=self.part, quantity=200)
        StockItem.objects.create(part=self.part, quantity=300)

        # Now create another 400 units which are LOST
        StockItem.objects.create(part=self.part, quantity=400, status=StockStatus.LOST)

    def get_part_data(self):
        """Helper function for retrieving part data"""
        url = reverse('api-part-list')

        response = self.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        for part in response.data:
            if part['pk'] == self.part.pk:
                return part

        # We should never get here!
        self.assertTrue(False)  # pragma: no cover

    def test_stock_quantity(self):
        """Simple test for the stock quantity."""
        data = self.get_part_data()

        self.assertEqual(data['in_stock'], 600)
        self.assertEqual(data['stock_item_count'], 4)

        # Add some more stock items!!
        for i in range(100):
            StockItem.objects.create(part=self.part, quantity=5)

        # Add another stock item which is assigned to a customer (and shouldn't count)
        customer = Company.objects.get(pk=4)
        StockItem.objects.create(part=self.part, quantity=9999, customer=customer)

        data = self.get_part_data()

        self.assertEqual(data['in_stock'], 1100)
        self.assertEqual(data['stock_item_count'], 105)

    def test_allocation_annotations(self):
        """Tests for query annotations which add allocation information.

        Ref: https://github.com/inventree/InvenTree/pull/2797
        """
        # We are looking at Part ID 100 ("Bob")
        url = reverse('api-part-detail', kwargs={'pk': 100})

        part = Part.objects.get(pk=100)

        response = self.get(url, expected_code=200)

        # Check that the expected annotated fields exist in the data
        data = response.data
        self.assertEqual(data['allocated_to_build_orders'], 0)
        self.assertEqual(data['allocated_to_sales_orders'], 0)

        # The unallocated stock count should equal the 'in stock' coutn
        in_stock = data['in_stock']
        self.assertEqual(in_stock, 126)
        self.assertEqual(data['unallocated_stock'], in_stock)

        # Check that model functions return the same values
        self.assertEqual(part.build_order_allocation_count(), 0)
        self.assertEqual(part.sales_order_allocation_count(), 0)
        self.assertEqual(part.total_stock, in_stock)
        self.assertEqual(part.available_stock, in_stock)

        # Now, let's create a sales order, and allocate some stock
        so = order.models.SalesOrder.objects.create(
            reference='001',
            customer=Company.objects.get(pk=1),
        )

        # We wish to send 50 units of "Bob" against this sales order
        line = order.models.SalesOrderLineItem.objects.create(
            quantity=50,
            order=so,
            part=part,
        )

        # Create a shipment against the order
        shipment_1 = order.models.SalesOrderShipment.objects.create(
            order=so,
            reference='001',
        )

        shipment_2 = order.models.SalesOrderShipment.objects.create(
            order=so,
            reference='002',
        )

        # Allocate stock items to this order, against multiple shipments
        order.models.SalesOrderAllocation.objects.create(
            line=line,
            shipment=shipment_1,
            item=StockItem.objects.get(pk=1007),
            quantity=17
        )

        order.models.SalesOrderAllocation.objects.create(
            line=line,
            shipment=shipment_1,
            item=StockItem.objects.get(pk=1008),
            quantity=18
        )

        order.models.SalesOrderAllocation.objects.create(
            line=line,
            shipment=shipment_2,
            item=StockItem.objects.get(pk=1006),
            quantity=15,
        )

        # Submit the API request again - should show us the sales order allocation
        data = self.get(url, expected_code=200).data

        self.assertEqual(data['allocated_to_sales_orders'], 50)
        self.assertEqual(data['in_stock'], 126)
        self.assertEqual(data['unallocated_stock'], 76)

        # Now, "ship" the first shipment (so the stock is not 'in stock' any more)
        shipment_1.complete_shipment(None)

        # Refresh the API data
        data = self.get(url, expected_code=200).data

        self.assertEqual(data['allocated_to_build_orders'], 0)
        self.assertEqual(data['allocated_to_sales_orders'], 15)
        self.assertEqual(data['in_stock'], 91)
        self.assertEqual(data['unallocated_stock'], 76)

        # Next, we create a build order and allocate stock against it
        bo = build.models.Build.objects.create(
            part=Part.objects.get(pk=101),
            quantity=10,
            title='Making some assemblies',
            status=BuildStatus.PRODUCTION,
        )

        bom_item = BomItem.objects.get(pk=6)

        # Allocate multiple stock items against this build order
        build.models.BuildItem.objects.create(
            build=bo,
            bom_item=bom_item,
            stock_item=StockItem.objects.get(pk=1000),
            quantity=10,
        )

        # Request data once more
        data = self.get(url, expected_code=200).data

        self.assertEqual(data['allocated_to_build_orders'], 10)
        self.assertEqual(data['allocated_to_sales_orders'], 15)
        self.assertEqual(data['in_stock'], 91)
        self.assertEqual(data['unallocated_stock'], 66)

        # Again, check that the direct model functions return the same values
        self.assertEqual(part.build_order_allocation_count(), 10)
        self.assertEqual(part.sales_order_allocation_count(), 15)
        self.assertEqual(part.total_stock, 91)
        self.assertEqual(part.available_stock, 66)

        # Allocate further stock against the build
        build.models.BuildItem.objects.create(
            build=bo,
            bom_item=bom_item,
            stock_item=StockItem.objects.get(pk=1001),
            quantity=10,
        )

        # Request data once more
        data = self.get(url, expected_code=200).data

        self.assertEqual(data['allocated_to_build_orders'], 20)
        self.assertEqual(data['allocated_to_sales_orders'], 15)
        self.assertEqual(data['in_stock'], 91)
        self.assertEqual(data['unallocated_stock'], 56)

        # Again, check that the direct model functions return the same values
        self.assertEqual(part.build_order_allocation_count(), 20)
        self.assertEqual(part.sales_order_allocation_count(), 15)
        self.assertEqual(part.total_stock, 91)
        self.assertEqual(part.available_stock, 56)


class BomItemTest(InvenTreeAPITestCase):
    """Unit tests for the BomItem API."""

    fixtures = [
        'category',
        'part',
        'location',
        'stock',
        'bom',
        'company',
    ]

    roles = [
        'part.add',
        'part.change',
        'part.delete',
    ]

    def test_bom_list(self):
        """Tests for the BomItem list endpoint."""
        # How many BOM items currently exist in the database?
        n = BomItem.objects.count()

        url = reverse('api-bom-list')
        response = self.get(url, expected_code=200)
        self.assertEqual(len(response.data), n)

        # Now, filter by part
        response = self.get(
            url,
            data={
                'part': 100,
            },
            expected_code=200
        )

        # Filter by "validated"
        response = self.get(
            url,
            data={
                'validated': True,
            },
            expected_code=200,
        )

        # Should be zero validated results
        self.assertEqual(len(response.data), 0)

        # Now filter by "not validated"
        response = self.get(
            url,
            data={
                'validated': False,
            },
            expected_code=200
        )

        # There should be at least one non-validated item
        self.assertTrue(len(response.data) > 0)

        # Now, let's validate an item
        bom_item = BomItem.objects.first()

        bom_item.validate_hash()

        response = self.get(
            url,
            data={
                'validated': True,
            },
            expected_code=200
        )

        # Check that the expected response is returned
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['pk'], bom_item.pk)

        # Each item in response should contain expected keys
        for el in response.data:

            for key in ['available_stock', 'available_substitute_stock']:
                self.assertTrue(key in el)

    def test_get_bom_detail(self):
        """Get the detail view for a single BomItem object."""
        url = reverse('api-bom-item-detail', kwargs={'pk': 3})

        response = self.get(url, expected_code=200)

        expected_values = [
            'allow_variants',
            'inherited',
            'note',
            'optional',
            'overage',
            'pk',
            'part',
            'quantity',
            'reference',
            'sub_part',
            'substitutes',
            'validated',
            'available_stock',
            'available_substitute_stock',
        ]

        for key in expected_values:
            self.assertTrue(key in response.data)

        self.assertEqual(int(float(response.data['quantity'])), 25)

        # Increase the quantity
        data = response.data
        data['quantity'] = 57
        data['note'] = 'Added a note'

        response = self.patch(url, data, expected_code=200)

        self.assertEqual(int(float(response.data['quantity'])), 57)
        self.assertEqual(response.data['note'], 'Added a note')

    def test_add_bom_item(self):
        """Test that we can create a new BomItem via the API."""
        url = reverse('api-bom-list')

        data = {
            'part': 100,
            'sub_part': 4,
            'quantity': 777,
        }

        self.post(url, data, expected_code=201)

        # Now try to create a BomItem which references itself
        data['part'] = 100
        data['sub_part'] = 100
        self.post(url, data, expected_code=400)

    def test_variants(self):
        """Tests for BomItem use with variants."""
        stock_url = reverse('api-stock-list')

        # BOM item we are interested in
        bom_item = BomItem.objects.get(pk=1)

        bom_item.allow_variants = True
        bom_item.save()

        # sub part that the BOM item points to
        sub_part = bom_item.sub_part

        sub_part.is_template = True
        sub_part.save()

        # How many stock items are initially available for this part?
        response = self.get(
            stock_url,
            {
                'bom_item': bom_item.pk,
            },
            expected_code=200
        )

        n_items = len(response.data)
        self.assertEqual(n_items, 2)

        loc = StockLocation.objects.get(pk=1)

        # Now we will create some variant parts and stock
        for ii in range(5):

            # Create a variant part!
            variant = Part.objects.create(
                name=f"Variant_{ii}",
                description="A variant part",
                component=True,
                variant_of=sub_part
            )

            variant.save()

            Part.objects.rebuild()

            # Create some stock items for this new part
            for jj in range(ii):
                StockItem.objects.create(
                    part=variant,
                    location=loc,
                    quantity=100
                )

            # Keep track of running total
            n_items += ii

            # Now, there should be more stock items available!
            response = self.get(
                stock_url,
                {
                    'bom_item': bom_item.pk,
                },
                expected_code=200
            )

            self.assertEqual(len(response.data), n_items)

        # Now, disallow variant parts in the BomItem
        bom_item.allow_variants = False
        bom_item.save()

        # There should now only be 2 stock items available again
        response = self.get(
            stock_url,
            {
                'bom_item': bom_item.pk,
            },
            expected_code=200
        )

        self.assertEqual(len(response.data), 2)

    def test_substitutes(self):
        """Tests for BomItem substitutes."""
        url = reverse('api-bom-substitute-list')
        stock_url = reverse('api-stock-list')

        # Initially we have no substitute parts
        response = self.get(url, expected_code=200)
        self.assertEqual(len(response.data), 0)

        # BOM item we are interested in
        bom_item = BomItem.objects.get(pk=1)

        # Filter stock items which can be assigned against this stock item
        response = self.get(
            stock_url,
            {
                "bom_item": bom_item.pk,
            },
            expected_code=200
        )

        n_items = len(response.data)

        loc = StockLocation.objects.get(pk=1)

        # Let's make some!
        for ii in range(5):
            sub_part = Part.objects.create(
                name=f"Substitute {ii}",
                description="A substitute part",
                component=True,
                is_template=False,
                assembly=False
            )

            # Create a new StockItem for this Part
            StockItem.objects.create(
                part=sub_part,
                quantity=1000,
                location=loc,
            )

            # Now, create an "alternative" for the BOM Item
            BomItemSubstitute.objects.create(
                bom_item=bom_item,
                part=sub_part
            )

            # We should be able to filter the API list to just return this new part
            response = self.get(url, data={'part': sub_part.pk}, expected_code=200)
            self.assertEqual(len(response.data), 1)

            # We should also have more stock available to allocate against this BOM item!
            response = self.get(
                stock_url,
                {
                    "bom_item": bom_item.pk,
                },
                expected_code=200
            )

            self.assertEqual(len(response.data), n_items + ii + 1)

        # There should now be 5 substitute parts available in the database
        response = self.get(url, expected_code=200)
        self.assertEqual(len(response.data), 5)

        # The BomItem detail endpoint should now also reflect the substitute data
        data = self.get(
            reverse('api-bom-item-detail', kwargs={'pk': bom_item.pk}),
            expected_code=200
        ).data

        # 5 substitute parts
        self.assertEqual(len(data['substitutes']), 5)

        # 5 x 1,000 stock quantity
        self.assertEqual(data['available_substitute_stock'], 5000)

        # 9,000 stock directly available
        self.assertEqual(data['available_stock'], 9000)

    def test_bom_item_uses(self):
        """Tests for the 'uses' field."""
        url = reverse('api-bom-list')

        # Test that the direct 'sub_part' association works

        assemblies = []

        for i in range(5):
            assy = Part.objects.create(
                name=f"Assy_{i}",
                description="An assembly made of other parts",
                active=True,
                assembly=True
            )

            assemblies.append(assy)

        components = []

        # Create some sub-components
        for i in range(5):

            cmp = Part.objects.create(
                name=f"Component_{i}",
                description="A sub component",
                active=True,
                component=True
            )

            for j in range(i):
                # Create a BOM item
                BomItem.objects.create(
                    quantity=10,
                    part=assemblies[j],
                    sub_part=cmp,
                )

            components.append(cmp)

            response = self.get(
                url,
                {
                    'uses': cmp.pk,
                },
                expected_code=200,
            )

            self.assertEqual(len(response.data), i)

    def test_bom_variant_stock(self):
        """Test for 'available_variant_stock' annotation."""
        Part.objects.rebuild()

        # BOM item we are interested in
        bom_item = BomItem.objects.get(pk=1)

        response = self.get('/api/bom/1/', {}, expected_code=200)

        # Initially, no variant stock available
        self.assertEqual(response.data['available_variant_stock'], 0)

        # Create some 'variants' of the referenced sub_part
        bom_item.sub_part.is_template = True
        bom_item.sub_part.save()

        for i in range(10):
            # Create a variant part
            vp = Part.objects.create(
                name=f"Var {i}",
                description="Variant part",
                variant_of=bom_item.sub_part,
            )

            # Create a stock item
            StockItem.objects.create(
                part=vp,
                quantity=100,
            )

        # There should now be variant stock available
        response = self.get('/api/bom/1/', {}, expected_code=200)

        self.assertEqual(response.data['available_variant_stock'], 1000)


class PartParameterTest(InvenTreeAPITestCase):
    """Tests for the ParParameter API."""
    superuser = True

    fixtures = [
        'category',
        'part',
        'location',
        'params',
    ]

    def test_list_params(self):
        """Test for listing part parameters."""
        url = reverse('api-part-parameter-list')

        response = self.get(url, format='json')

        self.assertEqual(len(response.data), 5)

        # Filter by part
        response = self.get(
            url,
            {
                'part': 3,
            },
            format='json'
        )

        self.assertEqual(len(response.data), 3)

        # Filter by template
        response = self.get(
            url,
            {
                'template': 1,
            },
            format='json',
        )

        self.assertEqual(len(response.data), 3)

    def test_create_param(self):
        """Test that we can create a param via the API."""
        url = reverse('api-part-parameter-list')

        response = self.post(
            url,
            {
                'part': '2',
                'template': '3',
                'data': 70
            }
        )

        self.assertEqual(response.status_code, 201)

        response = self.get(url, format='json')

        self.assertEqual(len(response.data), 6)

    def test_param_detail(self):
        """Tests for the PartParameter detail endpoint."""
        url = reverse('api-part-parameter-detail', kwargs={'pk': 5})

        response = self.get(url)

        self.assertEqual(response.status_code, 200)

        data = response.data

        self.assertEqual(data['pk'], 5)
        self.assertEqual(data['part'], 3)
        self.assertEqual(data['data'], '12')

        # PATCH data back in
        response = self.patch(url, {'data': '15'}, format='json')

        self.assertEqual(response.status_code, 200)

        # Check that the data changed!
        response = self.get(url, format='json')

        data = response.data

        self.assertEqual(data['data'], '15')
