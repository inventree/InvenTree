"""Unit tests for the various part API endpoints."""

import os
from datetime import datetime
from decimal import Decimal
from enum import IntEnum
from pathlib import Path
from random import randint

from django.core.exceptions import ValidationError
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

import PIL
from rest_framework import status
from rest_framework.test import APIClient

import build.models
import company.models
import order.models
from common.models import InvenTreeSetting
from company.models import Company, SupplierPart
from InvenTree.settings import BASE_DIR
from InvenTree.status_codes import BuildStatus, PurchaseOrderStatusGroups, StockStatus
from InvenTree.unit_test import InvenTreeAPITestCase
from part.models import (
    BomItem,
    BomItemSubstitute,
    Part,
    PartCategory,
    PartCategoryParameterTemplate,
    PartParameter,
    PartParameterTemplate,
    PartRelated,
    PartStocktake,
    PartTestTemplate,
)
from stock.models import StockItem, StockLocation


class PartCategoryAPITest(InvenTreeAPITestCase):
    """Unit tests for the PartCategory API."""

    fixtures = [
        'category',
        'part',
        'params',
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
        'part_category.delete',
    ]

    def test_category_list(self):
        """Test the PartCategoryList API endpoint."""
        url = reverse('api-part-category-list')

        # star categories manually for tests as it is not possible with fixures
        # because the current user is no fixure itself and throws an invalid
        # foreign key constrain
        for pk in [3, 4]:
            PartCategory.objects.get(pk=pk).set_starred(self.user, True)

        test_cases = [
            ({}, 8, 'no parameters'),
            ({'parent': 1, 'cascade': False}, 3, 'Filter by parent, no cascading'),
            ({'parent': 1, 'cascade': True}, 5, 'Filter by parent, cascading'),
            ({'cascade': True, 'depth': 0}, 2, 'Cascade with no parent, depth=0'),
            ({'cascade': False, 'depth': 10}, 2, 'Cascade with no parent, depth=10'),
            (
                {'cascade': True, 'depth': 10},
                8,
                'Cascade with null parent and bigger depth',
            ),
            (
                {'parent': 1, 'cascade': False, 'depth': 1},
                3,
                'Dont cascade with depth=0 and parent',
            ),
            (
                {'parent': 1, 'cascade': True, 'depth': 0},
                0,
                'Cascade with depth=0 and parent',
            ),
            (
                {'parent': 1, 'cascade': True, 'depth': 2},
                5,
                'Cascade with depth=1 with parent',
            ),
            (
                {'parent': 1, 'starred': True, 'cascade': True},
                2,
                'Should return the starred categories for the current user within the pk=1 tree',
            ),
            (
                {'parent': 1, 'starred': False, 'cascade': True},
                3,
                'Should return the not starred categories for the current user within the pk=1 tree',
            ),
        ]

        for params, res_len, description in test_cases:
            response = self.get(url, params, expected_code=200)
            self.assertEqual(len(response.data), res_len, description)

        # The following tests should fail (return 400 code)
        test_cases = [
            {'parent': 1, 'cascade': True, 'depth': 'abcdefg'},  # Invalid depth value
            {'parent': -42},  # Invalid parent
        ]

        for params in test_cases:
            response = self.get(url, params, expected_code=400)

        # Check that the required fields are present
        fields = [
            'pk',
            'name',
            'description',
            'default_location',
            'level',
            'parent',
            'part_count',
            'pathstring',
            'url',
        ]

        response = self.get(url, expected_code=200)
        for result in response.data:
            for f in fields:
                self.assertIn(
                    f, result, f'"{f}" is missing in result of PartCategory list'
                )

    def test_part_count(self):
        """Test that the 'part_count' field is annotated correctly."""
        url = reverse('api-part-category-list')

        # Create a parent category
        cat = PartCategory.objects.create(
            name='Parent Cat', description='Some name', parent=None
        )

        # Create child categories
        for ii in range(10):
            child = PartCategory.objects.create(
                name=f'Child cat {ii}', description='A child category', parent=cat
            )

            # Create parts in this category
            for jj in range(10):
                Part.objects.create(
                    name=f'Part xyz {jj}_{ii}',
                    description='A test part with a description',
                    category=child,
                )

        # Filter by parent category
        response = self.get(url, {'parent': cat.pk}, expected_code=200)

        # 10 child categories
        self.assertEqual(len(response.data), 10)

        for result in response.data:
            self.assertEqual(result['parent'], cat.pk)
            self.assertEqual(result['part_count'], 10)

        # Detail view for parent category
        response = self.get(f'/api/part/category/{cat.pk}/', expected_code=200)

        # Annotation should include parts from all sub-categories
        self.assertEqual(response.data['part_count'], 100)

    def test_category_parameters(self):
        """Test that the PartCategoryParameterTemplate API function work."""
        url = reverse('api-part-category-parameter-list')

        response = self.get(url, {}, expected_code=200)

        self.assertEqual(len(response.data), 2)

        # Add some more category templates via the API
        n = PartParameterTemplate.objects.count()

        for template in PartParameterTemplate.objects.all():
            response = self.post(
                url,
                {
                    'category': 2,
                    'parameter_template': template.pk,
                    'default_value': 'xyz',
                },
            )

        # Total number of category templates should have increased
        response = self.get(url, {}, expected_code=200)
        self.assertEqual(len(response.data), 2 + n)

        # Filter by category
        response = self.get(url, {'category': 2})

        self.assertEqual(len(response.data), n)

        # Test that we can retrieve individual templates via the API
        for template in PartCategoryParameterTemplate.objects.all():
            url = reverse(
                'api-part-category-parameter-detail', kwargs={'pk': template.pk}
            )

            data = self.get(url, {}, expected_code=200).data

            for key in [
                'pk',
                'category',
                'category_detail',
                'parameter_template',
                'parameter_template_detail',
                'default_value',
            ]:
                self.assertIn(key, data.keys())

            # Test that we can delete via the API also
            response = self.delete(url, expected_code=204)

        # There should not be any templates left at this point
        self.assertEqual(PartCategoryParameterTemplate.objects.count(), 0)

    def test_bleach(self):
        """Test that the data cleaning functionality is working.

        This helps to protect against XSS injection
        """
        url = reverse('api-part-category-detail', kwargs={'pk': 1})

        # Invalid values containing tags
        invalid_values = [
            '<img src="test"/>',
            '<a href="#">Link</a>',
            "<a href='#'>Link</a>",
            '<b>',
        ]

        for v in invalid_values:
            response = self.patch(url, {'description': v}, expected_code=400)

            self.assertIn('Remove HTML tags', str(response.data))

        # Raw characters should be allowed
        allowed = ['<< hello', 'Alpha & Omega', 'A > B > C']

        for val in allowed:
            response = self.patch(url, {'description': val}, expected_code=200)

            self.assertEqual(response.data['description'], val)

    def test_invisible_chars(self):
        """Test that invisible characters are removed from the input data."""
        url = reverse('api-part-category-detail', kwargs={'pk': 1})

        values = [
            'A part\n category\n\t',
            'A\t part\t category\t',
            'A pa\rrt cat\r\r\regory',
            'A part\u200e catego\u200fry\u202e',
        ]

        for val in values:
            response = self.patch(url, {'description': val}, expected_code=200)

            self.assertEqual(response.data['description'], 'A part category')

    def test_category_delete(self):
        """Test category deletion with different parameters."""

        class Target(IntEnum):
            move_subcategories_to_parent_move_parts_to_parent = (0,)
            move_subcategories_to_parent_delete_parts = (1,)
            delete_subcategories_move_parts_to_parent = (2,)
            delete_subcategories_delete_parts = (3,)

        for i in range(4):
            delete_child_categories: bool = False
            delete_parts: bool = False

            if i in (
                Target.move_subcategories_to_parent_delete_parts,
                Target.delete_subcategories_delete_parts,
            ):
                delete_parts = True
            if i in (
                Target.delete_subcategories_move_parts_to_parent,
                Target.delete_subcategories_delete_parts,
            ):
                delete_child_categories = True

            # Create a parent category
            parent_category = PartCategory.objects.create(
                name='Parent category',
                description='This is the parent category where the child categories and parts are moved to',
                parent=None,
            )

            category_count_before = PartCategory.objects.count()
            part_count_before = Part.objects.count()

            # Create a category to delete
            cat_to_delete = PartCategory.objects.create(
                name='Category to delete',
                description='This is the category to be deleted',
                parent=parent_category,
            )

            url = reverse('api-part-category-detail', kwargs={'pk': cat_to_delete.id})

            parts = []
            # Create parts in the category to be deleted
            for jj in range(3):
                parts.append(
                    Part.objects.create(
                        name=f'Part xyz {i}_{jj}',
                        description='Child part of the deleted category',
                        category=cat_to_delete,
                    )
                )

            child_categories = []
            child_categories_parts = []
            # Create child categories under the category to be deleted
            for ii in range(3):
                child = PartCategory.objects.create(
                    name=f'Child parent_cat {i}_{ii}',
                    description='A child category of the deleted category',
                    parent=cat_to_delete,
                )
                child_categories.append(child)

                # Create parts in the child categories
                for jj in range(3):
                    child_categories_parts.append(
                        Part.objects.create(
                            name=f'Part xyz {i}_{jj}_{ii}',
                            description='Child part in the child category of the deleted category',
                            category=child,
                        )
                    )

            # Delete the created category (sub categories and their parts will be moved under the parent)
            params = {}
            if delete_parts:
                params['delete_parts'] = '1'
            if delete_child_categories:
                params['delete_child_categories'] = '1'
            response = self.delete(url, params, expected_code=204)

            self.assertEqual(response.status_code, 204)

            if delete_parts:
                if i == Target.delete_subcategories_delete_parts:
                    # Check if all parts deleted
                    self.assertEqual(Part.objects.count(), part_count_before)
                elif i == Target.move_subcategories_to_parent_delete_parts:
                    # Check if all parts deleted
                    self.assertEqual(
                        Part.objects.count(),
                        part_count_before + len(child_categories_parts),
                    )
            else:
                # parts moved to the parent category
                for part in parts:
                    part.refresh_from_db()
                    self.assertEqual(part.category, parent_category)

                if delete_child_categories:
                    for part in child_categories_parts:
                        part.refresh_from_db()
                        self.assertEqual(part.category, parent_category)

            if delete_child_categories:
                # Check if all categories are deleted
                self.assertEqual(PartCategory.objects.count(), category_count_before)
            else:
                #  Check if all subcategories to parent moved to parent and all parts deleted
                for child in child_categories:
                    child.refresh_from_db()
                    self.assertEqual(child.parent, parent_category)

    def test_structural(self):
        """Test the effectiveness of structural categories.

        Make sure:
        - Parts cannot be created in structural categories
        - Parts cannot be assigned to structural categories
        """
        # Create our structural part category
        structural_category = PartCategory.objects.create(
            name='Structural category',
            description='This is the structural category',
            parent=None,
            structural=True,
        )

        part_count_before = Part.objects.count()

        # Make sure that we get an error if we try to create part in the structural category
        with self.assertRaises(ValidationError):
            part = Part.objects.create(
                name='-',
                description='Part which shall not be created',
                category=structural_category,
            )

        # Ensure that the part really did not get created in the structural category
        self.assertEqual(part_count_before, Part.objects.count())

        # Create a non structural category for test part category change
        non_structural_category = PartCategory.objects.create(
            name='Non-structural category',
            description='This is a non-structural category',
            parent=None,
            structural=False,
        )

        # Create the test part assigned to a non-structural category
        part = Part.objects.create(
            name='-',
            description='Part which category will be changed to structural',
            category=non_structural_category,
        )

        # Assign the test part to a structural category and make sure it gives an error
        part.category = structural_category
        with self.assertRaises(ValidationError):
            part.save()

        # Ensure that the part did not get saved to the DB
        part.refresh_from_db()
        self.assertEqual(part.category.pk, non_structural_category.pk)

    def test_path_detail(self):
        """Test path_detail information."""
        url = reverse('api-part-category-detail', kwargs={'pk': 5})

        # First, request without path detail
        response = self.get(url, {'path_detail': False}, expected_code=200)

        # Check that the path detail information is not included
        self.assertFalse('path' in response.data.keys())

        # Now, request *with* path detail
        response = self.get(url, {'path_detail': True}, expected_code=200)

        self.assertTrue('path' in response.data.keys())

        path = response.data['path']

        self.assertEqual(len(path), 3)
        self.assertEqual(path[0]['name'], 'Electronics')
        self.assertEqual(path[1]['name'], 'IC')
        self.assertEqual(path[2]['name'], 'MCU')

    def test_part_category_tree(self):
        """Test the PartCategoryTree API endpoint."""
        # Create a number of new part categories
        loc = None

        for idx in range(50):
            loc = PartCategory.objects.create(
                name=f'Test Category {idx}',
                description=f'Test category {idx}',
                parent=loc,
            )

        PartCategory.objects.rebuild()

        with self.assertNumQueriesLessThan(10):
            response = self.get(reverse('api-part-category-tree'), expected_code=200)

        self.assertEqual(len(response.data), PartCategory.objects.count())

        for item in response.data:
            category = PartCategory.objects.get(pk=item['pk'])
            parent = category.parent.pk if category.parent else None
            subcategories = category.get_descendants(include_self=False).count()

            self.assertEqual(item['name'], category.name)
            self.assertEqual(item['parent'], parent)
            self.assertEqual(item['subcategories'], subcategories)


class PartOptionsAPITest(InvenTreeAPITestCase):
    """Tests for the various OPTIONS endpoints in the /part/ API.

    Ensure that the required field details are provided!
    """

    roles = ['part.add']

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


class PartAPITestBase(InvenTreeAPITestCase):
    """Base class for running tests on the Part API endpoints."""

    fixtures = [
        'category',
        'part',
        'location',
        'bom',
        'build',
        'company',
        'test_templates',
        'manufacturer_part',
        'params',
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


class PartAPITest(PartAPITestBase):
    """Series of tests for the Part DRF API."""

    fixtures = [
        'category',
        'part',
        'location',
        'bom',
        'company',
        'test_templates',
        'manufacturer_part',
        'params',
        'supplier_part',
        'order',
    ]

    def test_get_categories(self):
        """Test that we can retrieve list of part categories, with various filtering options."""
        url = reverse('api-part-category-list')

        # Request *all* part categories
        response = self.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 8)

        # Request top-level part categories only
        response = self.get(url, {'cascade': False})

        self.assertEqual(len(response.data), 2)

        # Children of PartCategory<1>, cascade
        response = self.get(url, {'parent': 1, 'cascade': 'true'})

        self.assertEqual(len(response.data), 5)

        # Children of PartCategory<1>, do not cascade
        response = self.get(url, {'parent': 1, 'cascade': 'false'})

        self.assertEqual(len(response.data), 3)

    def test_add_categories(self):
        """Check that we can add categories."""
        data = {'name': 'Animals', 'description': 'All animals go here'}

        url = reverse('api-part-category-list')
        response = self.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        parent = response.data['pk']

        # Add some sub-categories to the top-level 'Animals' category
        for animal in ['cat', 'dog', 'zebra']:
            data = {'name': animal, 'description': 'A sort of animal', 'parent': parent}
            response = self.post(url, data)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(response.data['parent'], parent)
            self.assertEqual(response.data['name'], animal)
            self.assertEqual(response.data['pathstring'], 'Animals/' + animal)

        # There should be now 8 categories
        response = self.get(url)
        self.assertEqual(len(response.data), 12)

    def test_cat_detail(self):
        """Test the PartCategoryDetail API endpoint."""
        url = reverse('api-part-category-detail', kwargs={'pk': 4})
        response = self.get(url)

        # Test that we have retrieved the category
        self.assertEqual(response.data['description'], 'Integrated Circuits')
        self.assertEqual(response.data['parent'], 1)

        # Change some data and post it back
        data = response.data
        data['name'] = 'Changing category'
        data['parent'] = None
        data['description'] = 'Changing the description'
        response = self.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['description'], 'Changing the description')
        self.assertIsNone(response.data['parent'])

    def test_filter_parts(self):
        """Test part filtering using the API."""
        url = reverse('api-part-list')
        data = {'cascade': True}
        response = self.get(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), Part.objects.count())

        # Test filtering parts by category
        data = {'category': 2}
        response = self.get(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # There should only be 2 objects in category C
        self.assertEqual(len(response.data), 2)

        for part in response.data:
            self.assertEqual(part['category'], 2)

    def test_filter_by_in_bom(self):
        """Test that we can filter part list by the 'in_bom_for' parameter."""
        url = reverse('api-part-list')

        response = self.get(url, {'in_bom_for': 100}, expected_code=200)

        self.assertEqual(len(response.data), 4)

    def test_filter_by_related(self):
        """Test that we can filter by the 'related' status."""
        url = reverse('api-part-list')

        # Initially there are no relations, so this should return zero results
        response = self.get(url, {'related': 1}, expected_code=200)
        self.assertEqual(len(response.data), 0)

        # Add some relationships
        PartRelated.objects.create(
            part_1=Part.objects.get(pk=1), part_2=Part.objects.get(pk=2)
        )

        PartRelated.objects.create(
            part_2=Part.objects.get(pk=1), part_1=Part.objects.get(pk=3)
        )

        response = self.get(url, {'related': 1}, expected_code=200)
        self.assertEqual(len(response.data), 2)

    def test_filter_by_convert(self):
        """Test that we can correctly filter the Part list by conversion options."""
        category = PartCategory.objects.get(pk=3)

        # First, construct a set of template / variant parts
        master_part = Part.objects.create(
            name='Master',
            description='Master part which has some variants',
            category=category,
            is_template=True,
        )

        # Construct a set of variant parts
        variants = []

        for color in ['Red', 'Green', 'Blue', 'Yellow', 'Pink', 'Black']:
            variants.append(
                Part.objects.create(
                    name=f'{color} Variant',
                    description='Variant part with a specific color',
                    variant_of=master_part,
                    category=category,
                )
            )

        url = reverse('api-part-list')

        # An invalid part ID will return an error
        response = self.get(url, {'convert_from': 999999}, expected_code=400)

        self.assertIn('Select a valid choice', str(response.data['convert_from']))

        for variant in variants:
            response = self.get(url, {'convert_from': variant.pk}, expected_code=200)

            # There should be the same number of results for each request
            self.assertEqual(len(response.data), 6)

            id_values = [p['pk'] for p in response.data]

            self.assertIn(master_part.pk, id_values)

            for v in variants:
                # Check that all *other* variants are included also
                if v == variant:
                    continue

                self.assertIn(v.pk, id_values)

    def test_include_children(self):
        """Test the special 'include_child_categories' flag.

        If provided, parts are provided for ANY child category (recursive)
        """
        url = reverse('api-part-list')
        data = {'category': 1, 'cascade': True}

        # Now request to include child categories
        response = self.get(url, data)

        # Now there should be 5 total parts
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_test_templates(self):
        """Test the PartTestTemplate API."""
        url = reverse('api-part-test-template-list')

        # List ALL items
        response = self.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 9)

        # Request for a particular part
        response = self.get(url, data={'part': 10000})
        self.assertEqual(len(response.data), 5)

        response = self.get(url, data={'part': 10004})
        self.assertEqual(len(response.data), 6)

        # Try to post a new object (missing description)
        response = self.post(
            url,
            data={'part': 10000, 'test_name': 'My very first test', 'required': False},
        )

        self.assertEqual(response.status_code, 400)

        # Try to post a new object (should succeed)
        response = self.post(
            url,
            data={
                'part': 10000,
                'test_name': 'New Test',
                'required': True,
                'description': 'a test description',
            },
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Try to post a new test with the same name (should fail)
        response = self.post(
            url,
            data={'part': 10004, 'test_name': '   newtest', 'description': 'dafsdf'},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Try to post a new test against a non-trackable part (should fail)
        response = self.post(url, data={'part': 1, 'test_name': 'A simple test'})

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

    def test_template_filters(self):
        """Unit tests for API filters related to template parts.

        Test:
        - variant_of : Return children of specified part
        - ancestor : Return descendants of specified part

        Uses the 'chair template' part (pk=10000)
        """
        # Rebuild the MPTT structure before running these tests
        Part.objects.rebuild()

        url = reverse('api-part-list')

        response = self.get(url, {'variant_of': 10000}, expected_code=200)

        # 3 direct children of template part
        self.assertEqual(len(response.data), 3)

        response = self.get(url, {'ancestor': 10000}, expected_code=200)

        # 4 total descendants
        self.assertEqual(len(response.data), 4)

        # Use the 'green chair' as our reference
        response = self.get(url, {'variant_of': 10003}, expected_code=200)

        self.assertEqual(len(response.data), 1)

        response = self.get(url, {'ancestor': 10003}, expected_code=200)

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
        response = self.get(url, {'variant_of': 10003}, expected_code=200)

        self.assertEqual(len(response.data), 1)

        # However, now should be 101 descendants
        response = self.get(url, {'ancestor': 10003}, expected_code=200)

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
        response = self.get(url, {'ancestor': 10000}, expected_code=200)

        # 4 total descendants
        self.assertEqual(len(response.data), 4)

        for variant in response.data:
            self.assertEqual(variant['variant_stock'], 0)

        # Now, let's make some variant stock
        for variant in Part.objects.get(pk=10000).get_descendants(include_self=False):
            StockItem.objects.create(part=variant, quantity=100)

        response = self.get('/api/part/10000/', {}, expected_code=200)

        self.assertEqual(response.data['in_stock'], 0)
        self.assertEqual(response.data['variant_stock'], 400)

        # Check that each variant reports the correct stock quantities
        response = self.get(url, {'ancestor': 10000}, expected_code=200)

        expected_variant_stock = {10001: 0, 10002: 0, 10003: 100, 10004: 0}

        for variant in response.data:
            self.assertEqual(variant['in_stock'], 100)
            self.assertEqual(
                variant['variant_stock'], expected_variant_stock[variant['pk']]
            )

        # Add some 'sub variants' for the green chair variant
        green_chair = Part.objects.get(pk=10004)

        for i in range(10):
            gcv = Part.objects.create(
                name=f'GC Var {i}',
                description='Green chair variant',
                variant_of=green_chair,
            )

            StockItem.objects.create(part=gcv, quantity=50)

        # Spot check of some values
        response = self.get('/api/part/10000/', {})
        self.assertEqual(response.data['variant_stock'], 900)

        response = self.get('/api/part/10004/', {})
        self.assertEqual(response.data['variant_stock'], 500)

    def test_part_download(self):
        """Test download of part data via the API."""
        url = reverse('api-part-list')

        required_cols = [
            'Part ID',
            'Part Name',
            'Part Description',
            'In Stock',
            'Category Name',
            'Keywords',
            'Template',
            'Virtual',
            'Trackable',
            'Active',
            'Notes',
            'creation_date',
        ]

        excluded_cols = ['lft', 'rght', 'level', 'tree_id', 'metadata']

        with self.download_file(
            url, {'export': 'csv'}, expected_fn='InvenTree_Parts.csv'
        ) as file:
            data = self.process_csv(
                file,
                excluded_cols=excluded_cols,
                required_cols=required_cols,
                required_rows=Part.objects.count(),
            )

            for row in data:
                part = Part.objects.get(pk=row['Part ID'])

                if part.IPN:
                    self.assertEqual(part.IPN, row['IPN'])

                self.assertEqual(part.name, row['Part Name'])
                self.assertEqual(part.description, row['Part Description'])

                if part.category:
                    self.assertEqual(part.category.name, row['Category Name'])

    def test_date_filters(self):
        """Test that the creation date filters work correctly."""
        url = reverse('api-part-list')

        response = self.get(url)

        n = len(response.data)

        date_compare = datetime.fromisoformat('2019-01-01')

        # Filter by creation date
        response = self.get(url, {'created_before': '2019-01-01'}, expected_code=200)

        self.assertTrue(len(response.data) < n)
        self.assertTrue(len(response.data) > 0)

        for item in response.data:
            self.assertIsNotNone(item['creation_date'])

            date = datetime.fromisoformat(item['creation_date'])
            self.assertLessEqual(date, date_compare)

        response = self.get(url, {'created_after': '2019-01-01'}, expected_code=200)

        self.assertTrue(len(response.data) < n)
        self.assertTrue(len(response.data) > 0)

        for item in response.data:
            self.assertIsNotNone(item['creation_date'])

            date = datetime.fromisoformat(item['creation_date'])
            self.assertGreaterEqual(date, date_compare)


class PartCreationTests(PartAPITestBase):
    """Tests for creating new Part instances via the API."""

    def test_default_values(self):
        """Tests for 'default' values.

        Ensure that unspecified fields revert to "default" values
        (as specified in the model field definition)
        """
        url = reverse('api-part-list')

        response = self.post(
            url,
            {'name': 'all defaults', 'description': 'my test part', 'category': 1},
            expected_code=201,
        )

        data = response.data

        # Check that the un-specified fields have used correct default values
        self.assertTrue(data['active'])
        self.assertFalse(data['virtual'])

        # By default, parts are purchaseable
        self.assertTrue(data['purchaseable'])

        # Set the default 'purchaseable' status to True
        InvenTreeSetting.set_setting('PART_PURCHASEABLE', True, self.user)

        response = self.post(
            url,
            {'name': 'all defaults 2', 'description': 'my test part 2', 'category': 1},
            expected_code=201,
        )

        # Part should now be purchaseable by default
        self.assertTrue(response.data['purchaseable'])

        # "default" values should not be used if the value is specified
        response = self.post(
            url,
            {
                'name': 'all defaults 3',
                'description': 'my test part 3',
                'category': 1,
                'active': False,
                'purchaseable': False,
            },
            expected_code=201,
        )

        self.assertFalse(response.data['active'])
        self.assertFalse(response.data['purchaseable'])

    def test_initial_stock(self):
        """Tests for initial stock quantity creation."""

        def submit(stock_data, expected_code=None):
            """Helper function for submitting with initial stock data."""
            data = {
                'category': 1,
                'name': "My lil' test part",
                'description': 'A part with which to test',
            }

            data['initial_stock'] = stock_data

            response = self.post(
                reverse('api-part-list'), data, expected_code=expected_code
            )

            return response.data

        # Track how many parts exist at the start of this test
        n = Part.objects.count()

        # Submit with empty data
        response = submit({}, expected_code=400)
        self.assertIn(
            'This field is required', str(response['initial_stock']['quantity'])
        )

        # Submit with invalid quantity
        response = submit({'quantity': 'ax'}, expected_code=400)
        self.assertIn(
            'A valid number is required', str(response['initial_stock']['quantity'])
        )

        # Submit with valid data
        response = submit({'quantity': 50, 'location': 1}, expected_code=201)

        part = Part.objects.get(pk=response['pk'])
        self.assertEqual(part.total_stock, 50)
        self.assertEqual(n + 1, Part.objects.count())

    def test_initial_supplier_data(self):
        """Tests for initial creation of supplier / manufacturer data."""

        def submit(supplier_data, expected_code=400):
            """Helper function for submitting with supplier data."""
            data = {
                'name': 'My test part',
                'description': 'A test part thingy',
                'category': 1,
            }

            data['initial_supplier'] = supplier_data

            response = self.post(
                reverse('api-part-list'), data, expected_code=expected_code
            )

            return response.data

        n_part = Part.objects.count()
        n_mp = company.models.ManufacturerPart.objects.count()
        n_sp = company.models.SupplierPart.objects.count()

        # Submit with an invalid manufacturer
        response = submit({'manufacturer': 99999})

        self.assertIn(
            'object does not exist', str(response['initial_supplier']['manufacturer'])
        )

        response = submit({'manufacturer': 8})

        self.assertIn(
            'Selected company is not a valid manufacturer',
            str(response['initial_supplier']['manufacturer']),
        )

        # Submit with an invalid supplier
        response = submit({'supplier': 8})

        self.assertIn(
            'Selected company is not a valid supplier',
            str(response['initial_supplier']['supplier']),
        )

        # Test for duplicate MPN
        response = submit({'manufacturer': 6, 'mpn': 'MPN123'})

        self.assertIn(
            'Manufacturer part matching this MPN already exists', str(response)
        )

        # Test for duplicate SKU
        response = submit({'supplier': 2, 'sku': 'MPN456-APPEL'})

        self.assertIn('Supplier part matching this SKU already exists', str(response))

        # Test fields which are too long
        response = submit({'sku': 'abc' * 100, 'mpn': 'xyz' * 100})

        too_long = 'Ensure this field has no more than 100 characters'

        self.assertIn(too_long, str(response['initial_supplier']['sku']))
        self.assertIn(too_long, str(response['initial_supplier']['mpn']))

        # Finally, submit a valid set of information
        response = submit(
            {'supplier': 2, 'sku': 'ABCDEFG', 'manufacturer': 6, 'mpn': 'QWERTY'},
            expected_code=201,
        )

        self.assertEqual(n_part + 1, Part.objects.count())
        self.assertEqual(n_sp + 1, company.models.SupplierPart.objects.count())
        self.assertEqual(n_mp + 1, company.models.ManufacturerPart.objects.count())

    def test_strange_chars(self):
        """Test that non-standard ASCII chars are accepted."""
        url = reverse('api-part-list')

        name = 'KaltgerÃ¤testecker'
        description = 'Gerät KaltgerÃ¤testecker strange chars should get through'

        data = {'name': name, 'description': description, 'category': 2}

        response = self.post(url, data, expected_code=201)

        self.assertEqual(response.data['name'], name)
        self.assertEqual(response.data['description'], description)

    def test_duplication(self):
        """Test part duplication options."""
        # Run a matrix of tests
        for bom in [True, False]:
            for img in [True, False]:
                for params in [True, False]:
                    response = self.post(
                        reverse('api-part-list'),
                        {
                            'name': f'thing_{bom}{img}{params}',
                            'description': 'Some long description text for this part',
                            'category': 1,
                            'duplicate': {
                                'part': 100,
                                'copy_bom': bom,
                                'copy_image': img,
                                'copy_parameters': params,
                            },
                        },
                        expected_code=201,
                    )

                    part = Part.objects.get(pk=response.data['pk'])

                    # Check new part
                    self.assertEqual(part.bom_items.count(), 4 if bom else 0)
                    self.assertEqual(part.parameters.count(), 2 if params else 0)

    def test_category_parameters(self):
        """Test that category parameters are correctly applied."""
        cat = PartCategory.objects.get(pk=1)

        # Add some parameter template to the parent category
        for pk in [1, 2, 3]:
            PartCategoryParameterTemplate.objects.create(
                parameter_template=PartParameterTemplate.objects.get(pk=pk),
                category=cat,
                default_value=f'Value {pk}',
            )

        self.assertEqual(cat.parameter_templates.count(), 3)

        # Creat a new Part, without copying category parameters
        data = self.post(
            reverse('api-part-list'),
            {
                'category': 1,
                'name': 'Some new part',
                'description': 'A new part without parameters',
                'copy_category_parameters': False,
            },
            expected_code=201,
        ).data

        prt = Part.objects.get(pk=data['pk'])
        self.assertEqual(prt.parameters.count(), 0)

        # Create a new part, this time copying category parameters
        data = self.post(
            reverse('api-part-list'),
            {
                'category': 1,
                'name': 'Another new part',
                'description': 'A new part with parameters',
                'copy_category_parameters': True,
            },
            expected_code=201,
        ).data

        prt = Part.objects.get(pk=data['pk'])
        self.assertEqual(prt.parameters.count(), 3)


class PartDetailTests(PartAPITestBase):
    """Test that we can create / edit / delete Part objects via the API."""

    @classmethod
    def setUpTestData(cls):
        """Custom setup routine for this class."""
        super().setUpTestData()

        # Create a custom APIClient for file uploads
        # Ref: https://stackoverflow.com/questions/40453947/how-to-generate-a-file-upload-test-request-with-django-rest-frameworks-apireq
        cls.upload_client = APIClient()
        cls.upload_client.force_authenticate(user=cls.user)

    def test_part_operations(self):
        """Test that Part instances can be adjusted via the API."""
        n = Part.objects.count()

        # Create a part
        response = self.post(
            reverse('api-part-list'),
            {
                'name': 'my test api part',
                'description': 'a part created with the API',
                'category': 1,
                'tags': '["tag1", "tag2"]',
            },
        )

        self.assertEqual(response.status_code, 201)

        pk = response.data['pk']

        # Check that a new part has been added
        self.assertEqual(Part.objects.count(), n + 1)

        part = Part.objects.get(pk=pk)

        self.assertEqual(part.name, 'my test api part')
        self.assertEqual(part.tags.count(), 2)
        self.assertEqual([a.name for a in part.tags.order_by('slug')], ['tag1', 'tag2'])

        # Edit the part
        url = reverse('api-part-detail', kwargs={'pk': pk})

        # Let's change the name of the part

        response = self.patch(url, {'name': 'a new better name'})

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
        response = self.patch(url, {'name': 'a new better name'})

        self.assertEqual(response.status_code, 200)

        # Try to remove a tag
        response = self.patch(url, {'tags': ['tag1']})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['tags'], ['tag1'])

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
        response = self.post(
            reverse('api-part-list'),
            {
                'name': 'part',
                'description': 'description',
                'IPN': 'IPN-123',
                'category': 1,
                'revision': 'A',
            },
        )

        self.assertEqual(response.status_code, 201)

        n = Part.objects.count()

        # Check that we cannot create a duplicate in a different category
        response = self.post(
            reverse('api-part-list'),
            {
                'name': 'part',
                'description': 'description',
                'IPN': 'IPN-123',
                'category': 2,
                'revision': 'A',
            },
        )

        self.assertEqual(response.status_code, 400)

        # Check that only 1 matching part exists
        parts = Part.objects.filter(
            name='part', description='description', IPN='IPN-123'
        )

        self.assertEqual(parts.count(), 1)

        # A new part should *not* have been created
        self.assertEqual(Part.objects.count(), n)

        # But a different 'revision' *can* be created
        response = self.post(
            reverse('api-part-list'),
            {
                'name': 'part',
                'description': 'description',
                'IPN': 'IPN-123',
                'category': 2,
                'revision': 'B',
            },
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Part.objects.count(), n + 1)

        # Now, check that we cannot *change* an existing part to conflict
        pk = response.data['pk']

        url = reverse('api-part-detail', kwargs={'pk': pk})

        # Attempt to alter the revision code
        response = self.patch(url, {'revision': 'A'})

        self.assertEqual(response.status_code, 400)

        # But we *can* change it to a unique revision code
        response = self.patch(url, {'revision': 'C'})

        self.assertEqual(response.status_code, 200)

    def test_image_upload(self):
        """Test that we can upload an image to the part API."""
        self.assignRole('part.add')

        # Create a new part
        response = self.post(
            reverse('api-part-list'),
            {'name': 'imagine', 'description': 'All the people', 'category': 1},
            expected_code=201,
        )

        pk = response.data['pk']

        url = reverse('api-part-detail', kwargs={'pk': pk})

        p = Part.objects.get(pk=pk)

        # Part should not have an image!
        with self.assertRaises(ValueError):
            print(p.image.file)

        # Try to upload a non-image file
        test_path = BASE_DIR / '_testfolder' / 'dummy_image'
        with open(f'{test_path}.txt', 'w') as dummy_image:
            dummy_image.write('hello world')

        with open(f'{test_path}.txt', 'rb') as dummy_image:
            response = self.upload_client.patch(
                url, {'image': dummy_image}, format='multipart'
            )

            self.assertEqual(response.status_code, 400)
            self.assertIn('Upload a valid image', str(response.data))

        # Now try to upload a valid image file, in multiple formats
        for fmt in ['jpg', 'j2k', 'png', 'bmp', 'webp']:
            fn = f'{test_path}.{fmt}'

            img = PIL.Image.new('RGB', (128, 128), color='red')
            img.save(fn)

            with open(fn, 'rb') as dummy_image:
                response = self.upload_client.patch(
                    url, {'image': dummy_image}, format='multipart'
                )

                self.assertEqual(response.status_code, 200)

            # And now check that the image has been set
            p = Part.objects.get(pk=pk)
            self.assertIsNotNone(p.image)

    def test_existing_image(self):
        """Test that we can allocate an existing uploaded image to a new Part."""
        # First, upload an image for an existing part
        p = Part.objects.first()

        fn = BASE_DIR / '_testfolder' / 'part_image_123abc.png'

        img = PIL.Image.new('RGB', (128, 128), color='blue')
        img.save(fn)

        with open(fn, 'rb') as img_file:
            response = self.upload_client.patch(
                reverse('api-part-detail', kwargs={'pk': p.pk}), {'image': img_file}
            )

            self.assertEqual(response.status_code, 200)
            image_name = response.data['image']
            self.assertTrue(image_name.startswith('/media/part_images/part_image'))

        # Attempt to create, but with an invalid image name
        response = self.post(
            reverse('api-part-list'),
            {
                'name': 'New part',
                'description': 'New Part description',
                'category': 1,
                'existing_image': 'does_not_exist.png',
            },
            expected_code=400,
        )

        # Now, create a new part and assign the same image
        response = self.post(
            reverse('api-part-list'),
            {
                'name': 'New part',
                'description': 'New part description',
                'category': 1,
                'existing_image': image_name.split(os.path.sep)[-1],
            },
            expected_code=201,
        )

        self.assertEqual(response.data['image'], image_name)

    def test_update_existing_image(self):
        """Test that we can update the image of an existing part with an already existing image."""
        # First, upload an image for an existing part
        p = Part.objects.first()

        fn = BASE_DIR / '_testfolder' / 'part_image_123abc.png'

        img = PIL.Image.new('RGB', (128, 128), color='blue')
        img.save(fn)

        # Upload the image to a part
        with open(fn, 'rb') as img_file:
            response = self.upload_client.patch(
                reverse('api-part-detail', kwargs={'pk': p.pk}), {'image': img_file}
            )

            self.assertEqual(response.status_code, 200)
            image_name = response.data['image']
            self.assertTrue(image_name.startswith('/media/part_images/part_image'))

        # Create a new part without an image
        response = self.post(
            reverse('api-part-list'),
            {
                'name': 'Some New Part',
                'description': 'Description of the part',
                'category': 1,
            },
            expected_code=201,
        )

        self.assertEqual(response.data['image'], None)
        part_pk = response.data['pk']

        # Add image from the first part to the new part
        response = self.patch(
            reverse('api-part-detail', kwargs={'pk': part_pk}),
            {'existing_image': image_name},
            expected_code=200,
        )

        self.assertEqual(response.data['image'], image_name)

        # Attempt to add a non-existent image to an existing part
        last_p = Part.objects.last()
        response = self.patch(
            reverse('api-part-detail', kwargs={'pk': last_p.pk}),
            {'existing_image': 'bogus_image.jpg'},
            expected_code=400,
        )

    def test_details(self):
        """Test that the required details are available."""
        p = Part.objects.get(pk=1)

        url = reverse('api-part-detail', kwargs={'pk': 1})

        data = self.get(url, expected_code=200).data

        # How many parts are 'on order' for this part?
        lines = order.models.PurchaseOrderLineItem.objects.filter(
            part__part__pk=1, order__status__in=PurchaseOrderStatusGroups.OPEN
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

    def test_path_detail(self):
        """Check that path_detail can be requested against the serializer."""
        response = self.get(
            reverse('api-part-detail', kwargs={'pk': 1}),
            {'path_detail': True},
            expected_code=200,
        )

        self.assertIn('category_path', response.data)
        self.assertEqual(len(response.data['category_path']), 2)


class PartListTests(PartAPITestBase):
    """Unit tests for the Part List API endpoint."""

    def test_query_count(self):
        """Test that the query count is unchanged, independent of query results."""
        queries = [{'limit': 1}, {'limit': 10}, {'limit': 50}, {'category': 1}, {}]

        url = reverse('api-part-list')

        # Create a bunch of extra parts (efficiently)
        parts = []

        for ii in range(100):
            parts.append(
                Part(
                    name=f'Extra part {ii}',
                    description='A new part which will appear via the API',
                    level=0,
                    tree_id=0,
                    lft=0,
                    rght=0,
                )
            )

        Part.objects.bulk_create(parts)

        for query in queries:
            with CaptureQueriesContext(connection) as ctx:
                self.get(url, query, expected_code=200)

            # No more than 20 database queries
            self.assertLess(len(ctx), 20)

        # Test 'category_detail' annotation
        for b in [False, True]:
            with CaptureQueriesContext(connection) as ctx:
                results = self.get(
                    reverse('api-part-list'), {'category_detail': b}, expected_code=200
                )

                for result in results.data:
                    if b and result['category'] is not None:
                        self.assertIn('category_detail', result)

            # No more than 20 DB queries
            self.assertLessEqual(len(ctx), 20)


class PartNotesTests(InvenTreeAPITestCase):
    """Tests for the 'notes' field (markdown field)."""

    fixtures = ['category', 'part', 'location', 'company']

    roles = ['part.change', 'part.add']

    def test_long_notes(self):
        """Test that very long notes field is rejected."""
        # Ensure that we cannot upload a very long piece of text
        url = reverse('api-part-detail', kwargs={'pk': 1})

        response = self.patch(url, {'notes': 'abcde' * 10001}, expected_code=400)

        self.assertIn(
            'Ensure this field has no more than 50000 characters',
            str(response.data['notes']),
        )

    def test_multiline_formatting(self):
        """Ensure that markdown formatting is retained."""
        url = reverse('api-part-detail', kwargs={'pk': 1})

        notes = """
        ### Title

        1. Numbered list
        2. Another item
        3. Another item again

        [A link](http://link.com.go)

        """

        response = self.patch(url, {'notes': notes}, expected_code=200)

        # Ensure that newline chars have not been removed
        self.assertIn('\n', response.data['notes'])

        # Entire notes field should match original value
        self.assertEqual(response.data['notes'], notes.strip())


class PartPricingDetailTests(InvenTreeAPITestCase):
    """Tests for the part pricing API endpoint."""

    fixtures = ['category', 'part', 'location']

    roles = ['part.change']

    def url(self, pk):
        """Construct a pricing URL."""
        return reverse('api-part-pricing', kwargs={'pk': pk})

    def test_pricing_detail(self):
        """Test an empty pricing detail."""
        response = self.get(self.url(1), expected_code=200)

        # Check for expected fields
        expected_fields = [
            'currency',
            'updated',
            'bom_cost_min',
            'bom_cost_max',
            'purchase_cost_min',
            'purchase_cost_max',
            'internal_cost_min',
            'internal_cost_max',
            'supplier_price_min',
            'supplier_price_max',
            'overall_min',
            'overall_max',
        ]

        for field in expected_fields:
            self.assertIn(field, response.data)

        # Empty fields (no pricing by default)
        for field in expected_fields[2:]:
            self.assertIsNone(response.data[field])


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

    roles = ['part.view', 'part.change']

    @classmethod
    def setUpTestData(cls):
        """Create test data as part of setup routine."""
        super().setUpTestData()

        # Ensure the part "variant" tree is correctly structured
        Part.objects.rebuild()

        # Add a new part
        cls.part = Part.objects.create(
            name='Banana',
            description='This is a banana',
            category=PartCategory.objects.get(pk=1),
        )

        # Create some stock items associated with the part

        # First create 600 units which are OK
        StockItem.objects.create(part=cls.part, quantity=100)
        StockItem.objects.create(part=cls.part, quantity=200)
        StockItem.objects.create(part=cls.part, quantity=300)

        # Now create another 400 units which are LOST
        StockItem.objects.create(
            part=cls.part, quantity=400, status=StockStatus.LOST.value
        )

    def get_part_data(self):
        """Helper function for retrieving part data."""
        url = reverse('api-part-list')

        response = self.get(url)

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
        for _ in range(100):
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
            reference='001', customer=Company.objects.get(pk=1)
        )

        # We wish to send 50 units of "Bob" against this sales order
        line = order.models.SalesOrderLineItem.objects.create(
            quantity=50, order=so, part=part
        )

        # Create a shipment against the order
        shipment_1 = order.models.SalesOrderShipment.objects.create(
            order=so, reference='001'
        )

        shipment_2 = order.models.SalesOrderShipment.objects.create(
            order=so, reference='002'
        )

        # Allocate stock items to this order, against multiple shipments
        order.models.SalesOrderAllocation.objects.create(
            line=line,
            shipment=shipment_1,
            item=StockItem.objects.get(pk=1007),
            quantity=17,
        )

        order.models.SalesOrderAllocation.objects.create(
            line=line,
            shipment=shipment_1,
            item=StockItem.objects.get(pk=1008),
            quantity=18,
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
            reference='BO-9999',
            status=BuildStatus.PRODUCTION.value,
        )

        bom_item = BomItem.objects.get(pk=6)

        line = build.models.BuildLine.objects.get(bom_item=bom_item, build=bo)

        # Allocate multiple stock items against this build order
        build.models.BuildItem.objects.create(
            build_line=line, stock_item=StockItem.objects.get(pk=1000), quantity=10
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
            build_line=line, stock_item=StockItem.objects.get(pk=1001), quantity=10
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

    def test_on_order(self):
        """Test that the 'on_order' queryset annotation works as expected.

        This queryset annotation takes into account any outstanding line items for active orders,
        and should also use the 'pack_size' of the supplier part objects.
        """
        supplier = Company.objects.create(
            name='Paint Supplies', description='A supplier of paints', is_supplier=True
        )

        # First, create some parts
        paint = PartCategory.objects.create(
            parent=None, name='Paint', description='Paints and such'
        )

        for color in ['Red', 'Green', 'Blue', 'Orange', 'Yellow']:
            p = Part.objects.create(
                category=paint,
                units='litres',
                name=f'{color} Paint',
                description=f'Paint which is {color} in color',
            )

            # Create multiple supplier parts in different sizes
            for pk_sz in [1, 10, 25, 100]:
                sp = SupplierPart.objects.create(
                    part=p,
                    supplier=supplier,
                    SKU=f'PNT-{color}-{pk_sz}L',
                    pack_quantity=str(pk_sz),
                )

            self.assertEqual(p.supplier_parts.count(), 4)

        # Check that we have the right base data to start with
        self.assertEqual(paint.parts.count(), 5)
        self.assertEqual(supplier.supplied_parts.count(), 20)

        supplier_parts = supplier.supplied_parts.all()

        # Create multiple orders
        for _ii in range(5):
            po = order.models.PurchaseOrder.objects.create(
                supplier=supplier, description='ordering some paint'
            )

            # Order an assortment of items
            for sp in supplier_parts:
                # Generate random quantity to order
                quantity = randint(10, 20)

                # Mark up to half of the quantity as received
                received = randint(0, quantity // 2)

                # Add a line item
                item = order.models.PurchaseOrderLineItem.objects.create(
                    part=sp, order=po, quantity=quantity, received=received
                )

        # Now grab a list of parts from the API
        response = self.get(
            reverse('api-part-list'), {'category': paint.pk}, expected_code=200
        )

        # Check that the correct number of items have been returned
        self.assertEqual(len(response.data), 5)

        for item in response.data:
            # Calculate the 'ordering' quantity from first principles
            p = Part.objects.get(pk=item['pk'])

            on_order = 0

            for sp in p.supplier_parts.all():
                for line_item in sp.purchase_order_line_items.all():
                    po = line_item.order

                    if po.status in PurchaseOrderStatusGroups.OPEN:
                        remaining = line_item.quantity - line_item.received

                        if remaining > 0:
                            on_order += sp.base_quantity(remaining)

            # The annotated quantity must be equal to the hand-calculated quantity
            self.assertEqual(on_order, item['ordering'])

            # The annotated quantity must also match the part.on_order quantity
            self.assertEqual(on_order, p.on_order)


class BomItemTest(InvenTreeAPITestCase):
    """Unit tests for the BomItem API."""

    fixtures = ['category', 'part', 'location', 'stock', 'bom', 'company']

    roles = ['part.add', 'part.change', 'part.delete']

    def setUp(self):
        """Set up the test case."""
        super().setUp()

        # Rebuild part tree so BOM items validate correctly
        Part.objects.rebuild()

    def test_bom_list(self):
        """Tests for the BomItem list endpoint."""
        # How many BOM items currently exist in the database?
        n = BomItem.objects.count()

        url = reverse('api-bom-list')
        response = self.get(url, expected_code=200)
        self.assertEqual(len(response.data), n)

        # Now, filter by part
        response = self.get(url, data={'part': 100}, expected_code=200)

        # Filter by "validated"
        response = self.get(url, data={'validated': True}, expected_code=200)

        # Should be zero validated results
        self.assertEqual(len(response.data), 0)

        # Now filter by "not validated"
        response = self.get(url, data={'validated': False}, expected_code=200)

        # There should be at least one non-validated item
        self.assertTrue(len(response.data) > 0)

        # Now, let's validate an item
        bom_item = BomItem.objects.first()

        bom_item.validate_hash()

        response = self.get(url, data={'validated': True}, expected_code=200)

        # Check that the expected response is returned
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['pk'], bom_item.pk)

        # Each item in response should contain expected keys
        for el in response.data:
            for key in ['available_stock', 'available_substitute_stock']:
                self.assertTrue(key in el)

    def test_bom_list_search(self):
        """Test that we can search the BOM list API endpoint."""
        url = reverse('api-bom-list')

        response = self.get(url, expected_code=200)

        self.assertEqual(len(response.data), 6)

        # Limit the results with a search term
        response = self.get(url, {'search': '0805'}, expected_code=200)

        self.assertEqual(len(response.data), 3)

        # Search by 'reference' field
        for q in ['ABCDE', 'LMNOP', 'VWXYZ']:
            response = self.get(url, {'search': q}, expected_code=200)

            self.assertEqual(len(response.data), 1)
            self.assertEqual(response.data[0]['reference'], q)

        # Search by nonsense data
        response = self.get(url, {'search': 'xxxxxxxxxxxxxxxxx'}, expected_code=200)

        self.assertEqual(len(response.data), 0)

    def test_bom_list_ordering(self):
        """Test that the BOM list results can be ordered."""
        url = reverse('api-bom-list')

        # Order by increasing quantity
        response = self.get(f'{url}?ordering=+quantity', expected_code=200)

        self.assertEqual(len(response.data), 6)

        q1 = response.data[0]['quantity']
        q2 = response.data[-1]['quantity']

        self.assertTrue(q1 < q2)

        # Order by decreasing quantity
        response = self.get(f'{url}?ordering=-quantity', expected_code=200)

        self.assertEqual(q1, response.data[-1]['quantity'])
        self.assertEqual(q2, response.data[0]['quantity'])

        # Now test ordering by 'sub_part' (which is actually 'sub_part__name')
        response = self.get(
            url, {'ordering': 'sub_part', 'sub_part_detail': True}, expected_code=200
        )

        n1 = response.data[0]['sub_part_detail']['name']
        n2 = response.data[-1]['sub_part_detail']['name']

        response = self.get(
            url, {'ordering': '-sub_part', 'sub_part_detail': True}, expected_code=200
        )

        self.assertEqual(n1, response.data[-1]['sub_part_detail']['name'])
        self.assertEqual(n2, response.data[0]['sub_part_detail']['name'])

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

        data = {'part': 100, 'sub_part': 4, 'quantity': 777}

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
        response = self.get(stock_url, {'bom_item': bom_item.pk}, expected_code=200)

        n_items = len(response.data)
        self.assertEqual(n_items, 2)

        loc = StockLocation.objects.get(pk=1)

        # Now we will create some variant parts and stock
        for ii in range(5):
            # Create a variant part!
            variant = Part.objects.create(
                name=f'Variant_{ii}',
                description='A variant part, with a description',
                component=True,
                variant_of=sub_part,
            )

            variant.save()

            Part.objects.rebuild()

            # Create some stock items for this new part
            for _ in range(ii):
                StockItem.objects.create(part=variant, location=loc, quantity=100)

            # Keep track of running total
            n_items += ii

            # Now, there should be more stock items available!
            response = self.get(stock_url, {'bom_item': bom_item.pk}, expected_code=200)

            self.assertEqual(len(response.data), n_items)

        # Now, disallow variant parts in the BomItem
        bom_item.allow_variants = False
        bom_item.save()

        # There should now only be 2 stock items available again
        response = self.get(stock_url, {'bom_item': bom_item.pk}, expected_code=200)

        self.assertEqual(len(response.data), 2)

    def test_substitutes(self):
        """Tests for BomItem substitutes."""
        url = reverse('api-bom-substitute-list')
        stock_url = reverse('api-stock-list')

        # Initially we may have substitute parts
        # Count first, operate directly on Model
        countbefore = BomItemSubstitute.objects.count()

        # Now, make sure API returns the same count
        response = self.get(url, expected_code=200)
        self.assertEqual(len(response.data), countbefore)

        # BOM item we are interested in
        bom_item = BomItem.objects.get(pk=1)

        # Filter stock items which can be assigned against this stock item
        response = self.get(stock_url, {'bom_item': bom_item.pk}, expected_code=200)

        n_items = len(response.data)

        loc = StockLocation.objects.get(pk=1)

        # Let's make some!
        for ii in range(5):
            sub_part = Part.objects.create(
                name=f'Substitute {ii}',
                description='A substitute part',
                component=True,
                is_template=False,
                assembly=False,
            )

            # Create a new StockItem for this Part
            StockItem.objects.create(part=sub_part, quantity=1000, location=loc)

            # Now, create an "alternative" for the BOM Item
            BomItemSubstitute.objects.create(bom_item=bom_item, part=sub_part)

            # We should be able to filter the API list to just return this new part
            response = self.get(url, data={'part': sub_part.pk}, expected_code=200)
            self.assertEqual(len(response.data), 1)

            # We should also have more stock available to allocate against this BOM item!
            response = self.get(stock_url, {'bom_item': bom_item.pk}, expected_code=200)

            self.assertEqual(len(response.data), n_items + ii + 1)

        # There should now be 5 more substitute parts available in the database
        response = self.get(url, expected_code=200)
        self.assertEqual(len(response.data), countbefore + 5)

        # The BomItem detail endpoint should now also reflect the substitute data
        data = self.get(
            reverse('api-bom-item-detail', kwargs={'pk': bom_item.pk}),
            expected_code=200,
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
                name=f'Assy_{i}',
                description='An assembly made of other parts',
                active=True,
                assembly=True,
            )

            assemblies.append(assy)

        components = []

        # Create some sub-components
        for i in range(5):
            cmp = Part.objects.create(
                name=f'Component_{i}',
                description='A sub component',
                active=True,
                component=True,
            )

            for j in range(i):
                # Create a BOM item
                BomItem.objects.create(quantity=10, part=assemblies[j], sub_part=cmp)

            components.append(cmp)

            response = self.get(url, {'uses': cmp.pk}, expected_code=200)

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
                name=f'Var {i}',
                description='Variant part description field',
                variant_of=bom_item.sub_part,
            )

            # Create a stock item
            StockItem.objects.create(part=vp, quantity=100)

        # There should now be variant stock available
        response = self.get('/api/bom/1/', {}, expected_code=200)

        self.assertEqual(response.data['available_variant_stock'], 1000)


class PartAttachmentTest(InvenTreeAPITestCase):
    """Unit tests for the PartAttachment API endpoint."""

    fixtures = ['category', 'part', 'location']

    def test_add_attachment(self):
        """Test that we can create a new PartAttachment via the API."""
        url = reverse('api-part-attachment-list')

        # Upload without permission
        response = self.post(url, {}, expected_code=403)

        # Add required permission
        self.assignRole('part.add')

        # Upload without specifying part (will fail)
        response = self.post(url, {'comment': 'Hello world'}, expected_code=400)

        self.assertIn('This field is required', str(response.data['part']))

        # Upload without file OR link (will fail)
        response = self.post(
            url, {'part': 1, 'comment': 'Hello world'}, expected_code=400
        )

        self.assertIn('Missing file', str(response.data['attachment']))
        self.assertIn('Missing external link', str(response.data['link']))

        # Upload an invalid link (will fail)
        response = self.post(
            url, {'part': 1, 'link': 'not-a-link.py'}, expected_code=400
        )

        self.assertIn('Enter a valid URL', str(response.data['link']))

        link = 'https://www.google.com/test'

        # Upload a valid link (will pass)
        response = self.post(
            url, {'part': 1, 'link': link, 'comment': 'Hello world'}, expected_code=201
        )

        data = response.data

        self.assertEqual(data['part'], 1)
        self.assertEqual(data['link'], link)
        self.assertEqual(data['comment'], 'Hello world')


class PartInternalPriceBreakTest(InvenTreeAPITestCase):
    """Unit tests for the PartInternalPrice API endpoints."""

    fixtures = [
        'category',
        'part',
        'params',
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
        'part_category.delete',
    ]

    def test_create_price_breaks(self):
        """Test we can create price breaks at various quantities."""
        url = reverse('api-part-internal-price-list')

        breaks = [
            (1.0, 101),
            (1.1, 92.555555555),
            (1.5, 90.999999999),
            (1.756, 89),
            (2, 86),
            (25, 80),
        ]

        for q, p in breaks:
            data = self.post(
                url, {'part': 1, 'quantity': q, 'price': p}, expected_code=201
            ).data

            self.assertEqual(data['part'], 1)
            self.assertEqual(round(Decimal(data['quantity']), 4), round(Decimal(q), 4))
            self.assertEqual(round(Decimal(data['price']), 4), round(Decimal(p), 4))

        # Now, ensure that we can delete the Part via the API
        # In particular this test checks that there are no circular post_delete relationships
        # Ref: https://github.com/inventree/InvenTree/pull/3986

        # First, ensure the part instance can be deleted
        p = Part.objects.get(pk=1)
        p.active = False
        p.save()

        response = self.delete(reverse('api-part-detail', kwargs={'pk': 1}))
        self.assertEqual(response.status_code, 204)

        with self.assertRaises(Part.DoesNotExist):
            p.refresh_from_db()


class PartStocktakeTest(InvenTreeAPITestCase):
    """Unit tests for the part stocktake functionality."""

    superuser = False
    is_staff = False

    fixtures = ['category', 'part', 'location', 'stock']

    def test_list_endpoint(self):
        """Test the list endpoint for the stocktake data."""
        url = reverse('api-part-stocktake-list')

        self.assignRole('part.view')

        # Initially, no stocktake entries
        response = self.get(url, expected_code=200)

        self.assertEqual(len(response.data), 0)

        total = 0

        # Iterate over (up to) 5 parts in the database
        for p in Part.objects.all()[:5]:
            # Create some entries
            to_create = []

            n = p.pk % 10

            for idx in range(n):
                to_create.append(PartStocktake(part=p, quantity=(idx + 1) * 100))

                total += 1

            # Create all entries in a single bulk-create
            PartStocktake.objects.bulk_create(to_create)

            # Query list endpoint
            response = self.get(url, {'part': p.pk}, expected_code=200)

            # Check that the expected number of PartStocktake instances has been created
            self.assertEqual(len(response.data), n)

        # List all entries
        response = self.get(url, {}, expected_code=200)

        self.assertEqual(len(response.data), total)

    def test_create_stocktake(self):
        """Test that stocktake entries can be created via the API."""
        url = reverse('api-part-stocktake-list')

        self.assignRole('stocktake.add')
        self.assignRole('stocktake.view')

        for p in Part.objects.all():
            # Initially no stocktake information available
            self.assertIsNone(p.latest_stocktake)

            note = f'Note {p.pk}'
            quantity = p.pk + 5

            self.post(
                url,
                {'part': p.pk, 'quantity': quantity, 'note': note},
                expected_code=201,
            )

            p.refresh_from_db()
            stocktake = p.latest_stocktake

            self.assertIsNotNone(stocktake)
            self.assertEqual(stocktake.quantity, quantity)
            self.assertEqual(stocktake.part, p)
            self.assertEqual(stocktake.note, note)

    def test_edit_stocktake(self):
        """Test that a Stoctake instance can be edited and deleted via the API.

        Note that only 'staff' users can perform these actions.
        """
        p = Part.objects.all().first()

        st = PartStocktake.objects.create(part=p, quantity=10)

        url = reverse('api-part-stocktake-detail', kwargs={'pk': st.pk})
        self.assignRole('part.view')

        # Test we can retrieve via API
        self.get(url, expected_code=200)

        # Try to edit data
        self.patch(url, {'note': 'Another edit'}, expected_code=403)

        # Assign 'edit' role permission
        self.assignRole('stocktake.change')

        # Try again
        self.patch(url, {'note': 'Editing note field again'}, expected_code=200)

        # Try to delete
        self.delete(url, expected_code=403)

        self.assignRole('stocktake.delete')

        self.delete(url, expected_code=204)

    def test_report_list(self):
        """Test for PartStocktakeReport list endpoint."""
        from part.stocktake import generate_stocktake_report

        # Initially, no stocktake records are available
        self.assertEqual(PartStocktake.objects.count(), 0)

        # Generate stocktake data for all parts (default configuration)
        generate_stocktake_report()

        # At least one report now created
        n = PartStocktake.objects.count()
        self.assertGreater(n, 0)

        self.assignRole('stocktake.view')

        response = self.get(reverse('api-part-stocktake-list'), expected_code=200)

        self.assertEqual(len(response.data), n)

        # Stocktake report should be available via the API, also
        response = self.get(
            reverse('api-part-stocktake-report-list'), expected_code=200
        )

        self.assertEqual(len(response.data), 1)

        data = response.data[0]

        self.assertEqual(data['part_count'], 14)
        self.assertEqual(data['user'], None)
        self.assertTrue(data['report'].endswith('.csv'))

    def test_report_generate(self):
        """Test API functionality for generating a new stocktake report."""
        url = reverse('api-part-stocktake-report-generate')

        # Permission denied, initially
        self.assignRole('stocktake.view')
        response = self.post(url, data={}, expected_code=403)

        # Stocktake functionality disabled
        InvenTreeSetting.set_setting('STOCKTAKE_ENABLE', False, None)
        self.assignRole('stocktake.add')
        response = self.post(url, data={}, expected_code=400)

        self.assertIn('Stocktake functionality is not enabled', str(response.data))

        InvenTreeSetting.set_setting('STOCKTAKE_ENABLE', True, None)
        response = self.post(url, data={}, expected_code=400)
        self.assertIn('Background worker check failed', str(response.data))


class PartMetadataAPITest(InvenTreeAPITestCase):
    """Unit tests for the various metadata endpoints of API."""

    fixtures = [
        'category',
        'part',
        'params',
        'location',
        'bom',
        'company',
        'test_templates',
        'manufacturer_part',
        'supplier_part',
        'order',
        'stock',
    ]

    roles = ['part.change', 'part_category.change']

    def setUp(self):
        """Setup unit tets."""
        super().setUp()
        Part.objects.rebuild()

    def metatester(self, apikey, model):
        """Generic tester."""
        modeldata = model.objects.first()

        # Useless test unless a model object is found
        self.assertIsNotNone(modeldata)

        url = reverse(apikey, kwargs={'pk': modeldata.pk})

        # Metadata is initially null
        self.assertIsNone(modeldata.metadata)

        numstr = randint(100, 900)

        self.patch(
            url,
            {'metadata': {f'abc-{numstr}': f'xyz-{apikey}-{numstr}'}},
            expected_code=200,
        )

        # Refresh
        modeldata.refresh_from_db()
        self.assertEqual(
            modeldata.get_metadata(f'abc-{numstr}'), f'xyz-{apikey}-{numstr}'
        )

    def test_metadata(self):
        """Test all endpoints."""
        for apikey, model in {
            'api-part-category-parameter-metadata': PartCategoryParameterTemplate,
            'api-part-category-metadata': PartCategory,
            'api-part-test-template-metadata': PartTestTemplate,
            'api-part-related-metadata': PartRelated,
            'api-part-parameter-template-metadata': PartParameterTemplate,
            'api-part-parameter-metadata': PartParameter,
            'api-part-metadata': Part,
            'api-bom-substitute-metadata': BomItemSubstitute,
            'api-bom-item-metadata': BomItem,
        }.items():
            self.metatester(apikey, model)


class PartSchedulingTest(PartAPITestBase):
    """Unit tests for the 'part scheduling' API endpoint."""

    def test_get_schedule(self):
        """Test that the scheduling endpoint returns OK."""
        part_ids = [1, 3, 100, 101]

        for pk in part_ids:
            url = reverse('api-part-scheduling', kwargs={'pk': pk})
            data = self.get(url, expected_code=200).data

            for entry in data:
                for k in ['date', 'quantity', 'label']:
                    self.assertIn(k, entry)
