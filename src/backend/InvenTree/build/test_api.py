"""Unit tests for the BuildOrder API."""

from datetime import datetime, timedelta
from typing import Optional

from django.urls import reverse

from rest_framework import status

from build.models import Build, BuildItem, BuildLine
from build.status_codes import BuildStatus
from InvenTree.unit_test import InvenTreeAPITestCase
from part.models import BomItem, Part
from stock.models import StockItem
from stock.status_codes import StockStatus


class TestBuildAPI(InvenTreeAPITestCase):
    """Series of tests for the Build DRF API.

    - Tests for Build API
    - Tests for BuildItem API
    """

    fixtures = ['category', 'part', 'location', 'bom', 'build', 'build_line', 'stock']

    roles = ['build.change', 'build.add', 'build.delete']

    def test_get_build_list(self):
        """Test that we can retrieve list of build objects."""
        url = reverse('api-build-list')

        response = self.get(url, expected_code=200)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(response.data), 5)

        # Filter query by build status
        response = self.get(
            url, {'status': BuildStatus.COMPLETE.value}, expected_code=200
        )

        self.assertEqual(len(response.data), 4)

        # Filter by "active" status
        response = self.get(url, {'active': True}, expected_code=200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['pk'], 1)

        response = self.get(url, {'active': False}, expected_code=200)
        self.assertEqual(len(response.data), 4)

        # Filter by 'part' status
        response = self.get(url, {'part': 25}, expected_code=200)
        self.assertEqual(len(response.data), 1)

        # Filter by an invalid part
        response = self.get(url, {'part': 99999}, expected_code=400)
        self.assertIn('Select a valid choice', str(response.data))

        # Get a certain reference
        response = self.get(url, {'reference': 'BO-0001'}, expected_code=200)
        self.assertEqual(len(response.data), 1)

        # Get a certain reference
        response = self.get(url, {'reference': 'BO-9999XX'}, expected_code=200)
        self.assertEqual(len(response.data), 0)

        # Filter by 'issued_by'
        response = self.get(url)

        build = Build.objects.first()

        build.issued_by = self.user
        build.save()

        response = self.get(url, {'issued_by': self.user.pk}, expected_code=200)

        self.assertEqual(len(response.data), 1)

        item = response.data[0]

        self.assertEqual(item['pk'], build.pk)
        self.assertEqual(item['issued_by'], self.user.pk)

    def test_get_build_item_list(self):
        """Test retrieving BuildItem list and applying filters like 'part' and 'output'."""
        url = reverse('api-build-item-list')

        #   Retrieve the full list of BuildItem objects
        response = self.get(url, expected_code=200)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        #  Filter by part ID (only items for part ID=1 expected)
        response = self.get(url, {'part': '1'}, expected_code=200)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        # Filter: output=null (install_into=None)
        response = self.get(url, {'output': 'null'}, expected_code=200)
        ids = [item['pk'] for item in response.data]
        self.assertIn(1, ids)
        self.assertNotIn(2, ids)

        #  Filter: output=<id> (install_into specific ID)
        response = self.get(url, {'output': 100}, expected_code=200)
        ids = [item['pk'] for item in response.data]
        self.assertIn(2, ids)
        self.assertNotIn(1, ids)

        # test output options
        # Test cases: (parameter_name, response_field_name)
        test_cases = [
            ('part_detail', 'part_detail'),
            ('location_detail', 'location_detail'),
            ('stock_detail', 'stock_item_detail'),
            ('build_detail', 'build_detail'),
        ]

        for param, field in test_cases:
            # Test with parameter set to 'true'
            response = self.get(url, {param: 'true'}, expected_code=200)
            self.assertIn(field, response.data[0])

            # Test with parameter set to 'false'
            response = self.get(url, {param: 'false'}, expected_code=200)
            self.assertNotIn(field, response.data[0])


class BuildAPITest(InvenTreeAPITestCase):
    """Series of tests for the Build DRF API."""

    fixtures = ['category', 'part', 'location', 'bom', 'build', 'build_line', 'stock']

    # Required roles to access Build API endpoints
    roles = ['build.change', 'build.add']


class BuildTest(BuildAPITest):
    """Unit testing for the build complete API endpoint."""

    def setUp(self):
        """Basic setup for this test suite."""
        super().setUp()

        self.build = Build.objects.get(pk=1)

        self.url = reverse('api-build-output-complete', kwargs={'pk': self.build.pk})

    def test_invalid(self):
        """Test with invalid data."""
        # Test with an invalid build ID
        self.post(
            reverse('api-build-output-complete', kwargs={'pk': 99999}),
            {},
            expected_code=400,
        )

        data = self.post(self.url, {}, expected_code=400).data

        self.assertIn('This field is required', str(data['outputs']))
        self.assertIn('This field is required', str(data['location']))

        # Test with an invalid location
        data = self.post(
            self.url, {'outputs': [], 'location': 999999}, expected_code=400
        ).data

        self.assertIn('Invalid pk', str(data['location']))

        data = self.post(
            self.url, {'outputs': [], 'location': 1}, expected_code=400
        ).data

        self.assertIn('A list of build outputs must be provided', str(data))

        stock_item = StockItem.objects.create(part=self.build.part, quantity=100)

        post_data = {'outputs': [{'output': stock_item.pk}], 'location': 1}

        # Post with a stock item that does not match the build
        data = self.post(self.url, post_data, expected_code=400).data

        self.assertIn(
            'Build output does not match the parent build', str(data['outputs'][0])
        )

        # Now, ensure that the stock item *does* match the build
        stock_item.build = self.build
        stock_item.save()

        data = self.post(self.url, post_data, expected_code=400).data

        self.assertIn(
            'This build output has already been completed',
            str(data['outputs'][0]['output']),
        )

    def test_complete(self):
        """Test build order completion."""
        # Initially, build should not be able to be completed
        self.assertFalse(self.build.can_complete)

        # We start without any outputs assigned against the build
        self.assertEqual(self.build.incomplete_outputs.count(), 0)

        # Create some more build outputs
        for _ in range(10):
            self.build.create_build_output(10)

        # Check that we are in a known state
        self.assertEqual(self.build.incomplete_outputs.count(), 10)
        self.assertEqual(self.build.incomplete_count, 100)
        self.assertEqual(self.build.completed, 0)

        # We shall complete 4 of these outputs
        outputs = self.build.incomplete_outputs.all()

        # TODO: (2025-07-15) Try to optimize this API query to reduce DB hits
        self.post(
            self.url,
            {
                'outputs': [{'output': output.pk} for output in outputs],
                'location': 1,
                'status': StockStatus.ATTENTION.value,
            },
            expected_code=201,
            max_query_count=400,
        )

        self.assertEqual(self.build.incomplete_outputs.count(), 0)

        # And there should be 10 completed outputs
        outputs = self.build.complete_outputs
        self.assertEqual(outputs.count(), 10)

        for output in outputs:
            self.assertFalse(output.is_building)
            self.assertEqual(output.build, self.build)

        self.build.refresh_from_db()
        self.assertEqual(self.build.completed, 100)

        # Try to complete the build (it should fail)
        finish_url = reverse('api-build-finish', kwargs={'pk': self.build.pk})

        response = self.post(finish_url, {}, expected_code=400)

        self.assertIn('accept_unallocated', response.data)

        # Accept unallocated stock
        self.post(finish_url, {'accept_unallocated': True}, expected_code=201)

        self.build.refresh_from_db()

        # Build should have been marked as complete
        self.assertTrue(self.build.is_complete)

    def test_cancel(self):
        """Test that we can cancel a BuildOrder via the API.

        - First test that all stock is returned to stock
        - Second test that stock is consumed by the build order
        """

        def make_new_build(ref):
            """Make a new build order, and allocate stock to it."""
            data = self.post(
                reverse('api-build-list'),
                {'part': 100, 'quantity': 10, 'title': 'Test build', 'reference': ref},
                expected_code=201,
            ).data

            build = Build.objects.get(pk=data['pk'])

            build.auto_allocate_stock()

            self.assertGreater(build.build_lines.count(), 0)

            return build

        bo = make_new_build('BO-12345')

        url = reverse('api-build-cancel', kwargs={'pk': bo.pk})

        self.assertEqual(bo.status, BuildStatus.PENDING)

        self.post(url, {}, expected_code=201)

        bo.refresh_from_db()

        self.assertEqual(bo.status, BuildStatus.CANCELLED)

        # No items were "consumed" by this build
        self.assertEqual(bo.consumed_stock.count(), 0)

        # Make another build, this time we will *consume* the allocated stock
        bo = make_new_build('BO-12346')

        url = reverse('api-build-cancel', kwargs={'pk': bo.pk})

        self.post(url, {'remove_allocated_stock': True}, expected_code=201)

        bo.refresh_from_db()

        self.assertEqual(bo.status, BuildStatus.CANCELLED)

        # This time, there should be *consumed* stock
        self.assertGreater(bo.consumed_stock.count(), 0)

    def test_delete(self):
        """Test that we can delete a BuildOrder via the API."""
        bo = Build.objects.get(pk=1)

        url = reverse('api-build-detail', kwargs={'pk': bo.pk})

        # At first we do not have the required permissions
        self.delete(url, expected_code=403)

        self.assignRole('build.delete')

        # As build is currently not 'cancelled', it cannot be deleted
        self.delete(url, expected_code=400)

        bo.status = BuildStatus.CANCELLED.value
        bo.save()

        # Now, we should be able to delete
        self.delete(url, expected_code=204)

        with self.assertRaises(Build.DoesNotExist):
            Build.objects.get(pk=1)

    def test_create_delete_output(self):
        """Test that we can create and delete build outputs via the API."""
        bo = Build.objects.get(pk=1)

        n_outputs = bo.output_count

        create_url = reverse('api-build-output-create', kwargs={'pk': 1})

        # Attempt to create outputs with invalid data
        response = self.post(
            create_url, {'quantity': 'not a number'}, expected_code=400
        )

        self.assertIn('A valid number is required', str(response.data))

        for q in [-100, -10.3, 0]:
            response = self.post(create_url, {'quantity': q}, expected_code=400)

            if q == 0:
                self.assertIn('Quantity must be greater than zero', str(response.data))
            else:
                self.assertIn(
                    'Ensure this value is greater than or equal to 0',
                    str(response.data),
                )

        # Mark the part being built as 'trackable' (requires integer quantity)
        bo.part.trackable = True
        bo.part.save()

        response = self.post(create_url, {'quantity': 12.3}, expected_code=400)

        self.assertIn(
            'Integer quantity required for trackable parts', str(response.data)
        )

        # Erroneous serial numbers
        response = self.post(
            create_url,
            {'quantity': 5, 'serial_numbers': '1, 2, 3, 4, 5, 6', 'batch': 'my-batch'},
            expected_code=400,
        )

        self.assertIn(
            'Number of unique serial numbers (6) must match quantity (5)',
            str(response.data),
        )

        # At this point, no new build outputs should have been created
        self.assertEqual(n_outputs, bo.output_count)

        # Now, create with *good* data
        self.post(
            create_url,
            {'quantity': 5, 'serial_numbers': '1, 2, 3, 4, 5', 'batch': 'my-batch'},
            expected_code=201,
        )

        # 5 new outputs have been created
        self.assertEqual(n_outputs + 5, bo.output_count)

        # Attempt to create with identical serial numbers
        response = self.post(
            create_url, {'quantity': 3, 'serial_numbers': '1-3'}, expected_code=400
        )

        self.assertIn(
            'The following serial numbers already exist or are invalid : 1,2,3',
            str(response.data),
        )

        # Double check no new outputs have been created
        self.assertEqual(n_outputs + 5, bo.output_count)

        # Now, let's delete each build output individually via the API
        outputs = bo.build_outputs.all()

        # Assert that each output is currently in production
        for output in outputs:
            self.assertTrue(output.is_building)

        delete_url = reverse('api-build-output-delete', kwargs={'pk': 1})

        response = self.post(delete_url, {'outputs': []}, expected_code=400)

        self.assertIn('A list of build outputs must be provided', str(response.data))

        # Mark 1 build output as complete
        bo.complete_build_output(outputs[0], self.user)

        self.assertEqual(n_outputs + 5, bo.output_count)
        self.assertEqual(1, bo.complete_count)

        # Delete all outputs at once
        # Note: One has been completed, so this should fail!
        response = self.post(
            delete_url,
            {'outputs': [{'output': output.pk} for output in outputs]},
            expected_code=400,
        )

        self.assertIn(
            'This build output has already been completed', str(response.data)
        )

        # No change to the build outputs
        self.assertEqual(n_outputs + 5, bo.output_count)
        self.assertEqual(1, bo.complete_count)

        # Let's delete 2 build outputs
        self.post(
            delete_url,
            {'outputs': [{'output': output.pk} for output in outputs[1:3]]},
            expected_code=201,
        )

        # Two build outputs have been removed
        self.assertEqual(n_outputs + 3, bo.output_count)
        self.assertEqual(1, bo.complete_count)

        # Tests for BuildOutputComplete serializer
        complete_url = reverse('api-build-output-complete', kwargs={'pk': 1})

        # Let's mark the remaining outputs as complete
        response = self.post(
            complete_url, {'outputs': [], 'location': 4}, expected_code=400
        )

        self.assertIn('A list of build outputs must be provided', str(response.data))

        for output in outputs[3:]:
            output.refresh_from_db()
            self.assertTrue(output.is_building)

        self.post(
            complete_url,
            {
                'outputs': [{'output': output.pk} for output in outputs[3:]],
                'location': 4,
            },
            expected_code=201,
        )

        # Check that the outputs have been completed
        self.assertEqual(3, bo.complete_count)

        for output in outputs[3:]:
            output.refresh_from_db()
            self.assertEqual(output.location.pk, 4)
            self.assertFalse(output.is_building)

        # Try again, with an output which has already been completed
        response = self.post(
            complete_url,
            {'outputs': [{'output': outputs.last().pk}]},
            expected_code=400,
        )

        self.assertIn(
            'This build output has already been completed', str(response.data)
        )

    def test_download_build_orders(self):
        """Test that we can download a list of build orders via the API."""
        required_cols = [
            'Reference',
            'Build Status',
            'Completed items',
            'Batch Code',
            'Description',
            'Part',
            'Part Name',
            'ID',
            'Quantity',
        ]

        excluded_cols = ['lft', 'rght', 'tree_id', 'level', 'metadata']

        with self.export_data(reverse('api-build-list')) as data_file:
            data = self.process_csv(
                data_file,
                required_cols=required_cols,
                excluded_cols=excluded_cols,
                required_rows=Build.objects.count(),
            )

            for row in data:
                build = Build.objects.get(pk=row['ID'])

                self.assertEqual(str(build.part.pk), row['Part'])
                self.assertEqual(build.part.name, row['Part Name'])

                self.assertEqual(build.reference, row['Reference'])
                self.assertEqual(build.title, row['Description'])

    def test_create(self):
        """Test creation of new build orders via the API."""
        url = reverse('api-build-list')

        # First, we'll create a tree of part assemblies
        part_a = Part.objects.create(
            name='Part A', description='Part A description', assembly=True
        )
        part_b = Part.objects.create(
            name='Part B', description='Part B description', assembly=True
        )
        part_c = Part.objects.create(
            name='Part C', description='Part C description', assembly=True
        )

        # Create a BOM for Part A
        BomItem.objects.create(part=part_a, sub_part=part_b, quantity=5)

        # Create a BOM for Part B
        BomItem.objects.create(part=part_b, sub_part=part_c, quantity=7)

        n = Build.objects.count()

        # Create a build order for Part A, with a quantity of 10
        response = self.post(
            url,
            {
                'reference': 'BO-9876',
                'part': part_a.pk,
                'quantity': 10,
                'title': 'A build',
            },
            expected_code=201,
        )

        self.assertEqual(n + 1, Build.objects.count())

        bo = Build.objects.get(pk=response.data['pk'])

        self.assertEqual(bo.children.count(), 0)


class BuildAllocationTest(BuildAPITest):
    """Unit tests for allocation of stock items against a build order.

    For this test, we will be using Build ID=1;

    - This points to Part 100 (see fixture data in part.yaml)
    - This Part already has a BOM with 4 items (see fixture data in bom.yaml)
    - There are no BomItem objects yet created for this build
    """

    def setUp(self):
        """Basic operation as part of test suite setup."""
        super().setUp()

        self.assignRole('build.add')
        self.assignRole('build.change')

        self.url = reverse('api-build-allocate', kwargs={'pk': 1})

        self.build = Build.objects.get(pk=1)

        # Regenerate BuildLine objects
        self.build.create_build_line_items()

        # Record number of build items which exist at the start of each test
        self.n = BuildItem.objects.count()

    def test_build_data(self):
        """Check that our assumptions about the particular BuildOrder are correct."""
        self.assertEqual(self.build.part.pk, 100)

        # There should be 4x BOM items we can use
        self.assertEqual(self.build.part.bom_items.count(), 4)

        # No items yet allocated to this build
        self.assertEqual(
            BuildItem.objects.filter(build_line__build=self.build).count(), 0
        )

    def test_get(self):
        """A GET request to the endpoint should return an error."""
        self.get(self.url, expected_code=405)

    def test_options(self):
        """An OPTIONS request to the endpoint should return information about the endpoint."""
        response = self.options(self.url, expected_code=200)

        self.assertIn(
            'API endpoint to allocate stock items to a build order', str(response.data)
        )

    def test_empty(self):
        """Test without any POST data."""
        # Initially test with an empty data set
        data = self.post(self.url, {}, expected_code=400).data

        self.assertIn('This field is required', str(data['items']))

        # Now test but with an empty items list
        data = self.post(self.url, {'items': []}, expected_code=400).data

        self.assertIn('Allocation items must be provided', str(data))

        # No new BuildItem objects have been created during this test
        self.assertEqual(self.n, BuildItem.objects.count())

    def test_missing(self):
        """Test with missing data."""
        # Missing quantity
        data = self.post(
            self.url,
            {
                'items': [
                    {
                        'build_line': 1,  # M2x4 LPHS
                        'stock_item': 2,  # 5,000 screws available
                    }
                ]
            },
            expected_code=400,
        ).data

        self.assertIn('This field is required', str(data['items'][0]['quantity']))

        # Missing bom_item
        data = self.post(
            self.url,
            {'items': [{'stock_item': 2, 'quantity': 5000}]},
            expected_code=400,
        ).data

        self.assertIn('This field is required', str(data['items'][0]['build_line']))

        # Missing stock_item
        data = self.post(
            self.url,
            {'items': [{'build_line': 1, 'quantity': 5000}]},
            expected_code=400,
        ).data

        self.assertIn('This field is required', str(data['items'][0]['stock_item']))

        # No new BuildItem objects have been created during this test
        self.assertEqual(self.n, BuildItem.objects.count())

    def test_invalid_bom_item(self):
        """Test by passing an invalid BOM item."""
        # Find the right (in this case, wrong) BuildLine instance
        si = StockItem.objects.get(pk=11)
        lines = self.build.build_lines.all()

        wrong_line = None

        for line in lines:
            if line.bom_item.sub_part.pk != si.pk:
                wrong_line = line
                break

        if not wrong_line:
            raise self.fail(
                'No matching BuildLine found for the given stock item'
            )  # pragma: no cover

        data = self.post(
            self.url,
            {
                'items': [
                    {'build_line': wrong_line.pk, 'stock_item': 11, 'quantity': 500}
                ]
            },
            expected_code=400,
        ).data

        self.assertIn('Selected stock item does not match BOM line', str(data))

    def test_valid_data(self):
        """Test with valid data.

        This should result in creation of a new BuildItem object
        """
        # Find the correct BuildLine
        si = StockItem.objects.get(pk=2)

        right_line = None

        for line in self.build.build_lines.all():
            if line.bom_item.sub_part.pk == si.part.pk:
                right_line = line
                break

        if not right_line:
            raise self.fail(
                'No matching BuildLine found for the given stock item'
            )  # pragma: no cover

        self.post(
            self.url,
            {
                'items': [
                    {'build_line': right_line.pk, 'stock_item': 2, 'quantity': 5000}
                ]
            },
            expected_code=201,
        )

        # A new BuildItem should have been created
        self.assertEqual(self.n + 1, BuildItem.objects.count())

        allocation = BuildItem.objects.last()

        self.assertEqual(allocation.quantity, 5000)
        self.assertEqual(allocation.bom_item.pk, 1)
        self.assertEqual(allocation.stock_item.pk, 2)

    def test_reallocate(self):
        """Test reallocating an existing built item with the same stock item.

        This should increment the quantity of the existing BuildItem object
        """
        # Find the correct BuildLine
        si = StockItem.objects.get(pk=2)

        right_line: Optional[BuildLine] = None
        for line in self.build.build_lines.all():
            if line.bom_item.sub_part.pk == si.part.pk:
                right_line: BuildLine = line
                break
        if not right_line:
            raise self.fail(
                'No matching BuildLine found for the given stock item'
            )  # pragma: no cover

        self.post(
            self.url,
            {
                'items': [
                    {'build_line': right_line.pk, 'stock_item': 2, 'quantity': 3000}
                ]
            },
            expected_code=201,
        )

        # A new BuildItem should have been created
        self.assertEqual(self.n + 1, BuildItem.objects.count())

        allocation = BuildItem.objects.last()

        self.assertEqual(allocation.quantity, 3000)
        self.assertEqual(allocation.bom_item.pk, 1)
        self.assertEqual(allocation.stock_item.pk, 2)

        # Try to allocate more than the required quantity (this should fail)
        self.post(
            self.url,
            {
                'items': [
                    {'build_line': right_line.pk, 'stock_item': 2, 'quantity': 2001}
                ]
            },
            expected_code=400,
        )

        allocation.refresh_from_db()
        self.assertEqual(allocation.quantity, 3000)

        # Try to allocate the remaining items
        self.post(
            self.url,
            {
                'items': [
                    {'build_line': right_line.pk, 'stock_item': 2, 'quantity': 2000}
                ]
            },
            expected_code=201,
        )

        allocation.refresh_from_db()
        self.assertEqual(allocation.quantity, 5000)

    def test_fractional_allocation(self):
        """Test allocation of a fractional quantity of stock items.

        Ref: https://github.com/inventree/InvenTree/issues/6508
        """
        si = StockItem.objects.get(pk=2)

        # Find line item
        line = self.build.build_lines.all().filter(bom_item__sub_part=si.part).first()

        # Test a fractional quantity when the *available* quantity is greater than 1
        si.quantity = 100
        si.save()

        self.post(
            self.url,
            {
                'items': [
                    {'build_line': line.pk, 'stock_item': si.pk, 'quantity': 0.1616}
                ]
            },
            expected_code=201,
        )

        # Test a fractional quantity when the *available* quantity is less than 1
        si = StockItem.objects.create(
            part=si.part, quantity=0.3159, tree_id=0, level=0, lft=0, rght=0
        )

        self.post(
            self.url,
            {
                'items': [
                    {'build_line': line.pk, 'stock_item': si.pk, 'quantity': 0.1616}
                ]
            },
            expected_code=201,
        )

    def test_auto_allocate(self):
        """Test the allocation of tracked items against a Build."""
        N_BUILD_ITEMS = BuildItem.objects.count()

        assembly = Part.objects.create(
            name='Test Assembly',
            description='Test Assembly Description',
            assembly=True,
            trackable=True,
        )

        component = Part.objects.create(
            name='Test Component',
            description='Test Component Description',
            trackable=True,
            component=True,
        )

        # Create a BOM item for the assembly
        BomItem.objects.create(part=assembly, sub_part=component, quantity=1)

        # Create a build order for the assembly
        build = Build.objects.create(part=assembly, reference='BO-12347', quantity=10)

        serials = [str(x) for x in range(100, 110)]

        # Create serialized component items
        for sn in serials:
            StockItem.objects.create(part=component, quantity=1, serial=str(sn))

        self.assertEqual(N_BUILD_ITEMS, BuildItem.objects.count())

        # Generate build outputs via API
        url = reverse('api-build-output-create', kwargs={'pk': build.pk})

        response = self.post(
            url,
            {
                'quantity': 10,
                'serial_numbers': ', '.join(serials),
                'auto_allocate': True,
            },
            expected_code=201,
        )

        # 10 new build item objects should have been created
        self.assertEqual(N_BUILD_ITEMS + 10, BuildItem.objects.count())

        self.assertEqual(len(response.data), 10)

        # Check that the tracked items have been auto-allocated based on serial number
        for entry in response.data:
            self.assertIn(entry['serial'], serials)

            # Find the matching output
            output = StockItem.objects.filter(
                part=assembly, serial=entry['serial']
            ).first()

            self.assertIsNotNone(output)

            # Find the matching component
            c = StockItem.objects.filter(part=component, serial=entry['serial']).first()
            self.assertIsNotNone(c)

            # Find the matching BuildItem object
            bi = BuildItem.objects.filter(
                stock_item=c, quantity=1, install_into=output
            ).first()

            self.assertIsNotNone(bi)
            self.assertEqual(bi.build, build)


class BuildItemTest(BuildAPITest):
    """Unit tests for build items.

    For this test, we will be using Build ID=1;

    - This points to Part 100 (see fixture data in part.yaml)
    - This Part already has a BOM with 4 items (see fixture data in bom.yaml)
    - There are no BomItem objects yet created for this build
    """

    def setUp(self):
        """Basic operation as part of test suite setup."""
        super().setUp()

        self.assignRole('build.add')
        self.assignRole('build.change')

        self.build = Build.objects.get(pk=1)

        # Regenerate BuildLine objects
        self.build.create_build_line_items()

        # Record number of build items which exist at the start of each test
        self.n = BuildItem.objects.count()

    def test_update_overallocated(self):
        """Test update of overallocated stock items."""
        si = StockItem.objects.get(pk=2)

        # Find line item
        line = self.build.build_lines.all().filter(bom_item__sub_part=si.part).first()

        # Set initial stock item quantity
        si.quantity = 100
        si.save()

        # Create build item
        bi = BuildItem(build_line=line, stock_item=si, quantity=100)
        bi.save()

        # Reduce stock item quantity
        si.quantity = 50
        si.save()

        # Reduce build item quantity
        url = reverse('api-build-item-detail', kwargs={'pk': bi.pk})

        self.patch(url, {'quantity': 50}, expected_code=200)


class BuildOverallocationTest(BuildAPITest):
    """Unit tests for over allocation of stock items against a build order.

    Using same Build ID=1 as allocation test above.
    """

    @classmethod
    def setUpTestData(cls):
        """Basic operation as part of test suite setup."""
        super().setUpTestData()

        cls.assignRole('build.add')
        cls.assignRole('build.change')

        cls.build = Build.objects.get(pk=1)
        cls.url = reverse('api-build-finish', kwargs={'pk': cls.build.pk})

        StockItem.objects.create(part=Part.objects.get(pk=50), quantity=30)

        # Keep some state for use in later assertions, and then overallocate
        cls.state = {}
        cls.allocation = {}

        items_to_create = []

        for idx, build_line in enumerate(cls.build.build_lines.all()):
            required = build_line.quantity + idx + 1
            sub_part = build_line.bom_item.sub_part
            si = StockItem.objects.filter(part=sub_part, quantity__gte=required).first()

            cls.state[sub_part] = (si, si.quantity, required)

            items_to_create.append(
                BuildItem(build_line=build_line, stock_item=si, quantity=required)
            )

        BuildItem.objects.bulk_create(items_to_create)

        # create and complete outputs
        cls.build.create_build_output(cls.build.quantity)
        outputs = cls.build.build_outputs.all()
        cls.build.complete_build_output(outputs[0], cls.user)

    def setUp(self):
        """Basic operation as part of test suite setup."""
        super().setUp()

        self.generate_exchange_rates()

    def test_setup(self):
        """Validate expected state after set-up."""
        self.assertEqual(self.build.incomplete_outputs.count(), 0)
        self.assertEqual(self.build.complete_outputs.count(), 1)
        self.assertEqual(self.build.completed, self.build.quantity)

    def test_overallocated_requires_acceptance(self):
        """Test build order cannot complete with overallocated items."""
        # Try to complete the build (it should fail due to overallocation)
        response = self.post(self.url, {}, expected_code=400)
        self.assertIn('accept_overallocated', response.data)

        # Check stock items have not reduced at all
        for si, oq, _ in self.state.values():
            si.refresh_from_db()
            self.assertEqual(si.quantity, oq)

        # Accept overallocated stock
        # TODO: (2025-07-16) Look into optimizing this API query to reduce DB hits
        self.post(
            self.url,
            {'accept_overallocated': 'accept'},
            expected_code=201,
            max_query_count=400,
        )

        self.build.refresh_from_db()

        # Build should have been marked as complete
        self.assertTrue(self.build.is_complete)

        # Check stock items have reduced in-line with the overallocation
        for si, oq, rq in self.state.values():
            si.refresh_from_db()
            self.assertEqual(si.quantity, oq - rq)

    def test_overallocated_can_trim(self):
        """Test build order will trim/de-allocate overallocated stock when requested."""
        # TODO: (2025-07-16) Look into optimizing this API query to reduce DB hits
        self.post(
            self.url,
            {'accept_overallocated': 'trim'},
            expected_code=201,
            max_query_count=450,
        )

        # Note: Large number of queries is due to pricing recalculation for each stock item

        self.build.refresh_from_db()

        # Build should have been marked as complete
        self.assertTrue(self.build.is_complete)

        # Check stock items have reduced only by bom requirement (overallocation trimmed)
        for line in self.build.build_lines.all():
            si, oq, _ = self.state[line.bom_item.sub_part]
            rq = line.quantity
            si.refresh_from_db()
            self.assertEqual(si.quantity, oq - rq)


class BuildListTest(BuildAPITest):
    """Tests for the BuildOrder LIST API."""

    url = reverse('api-build-list')

    def test_api_options(self):
        """Test OPTIONS endpoint for the Build list API."""
        data = self.options(self.url, expected_code=200).data

        self.assertEqual(data['name'], 'Build List')
        actions = data['actions']['POST']

        for field_name in [
            'pk',
            'title',
            'part',
            'part_detail',
            'project_code',
            'project_code_detail',
            'quantity',
        ]:
            self.assertIn(field_name, actions)

        # Specific checks for certain fields
        for field_name in ['part', 'project_code', 'take_from']:
            field = actions[field_name]
            self.assertEqual(field['type'], 'related field')

            for key in ['model', 'api_url', 'pk_field']:
                self.assertIn(key, field)

    def test_detail_fields(self):
        """Test inclusion of detail fields."""
        # Test without extra detail fields
        for val in [True, False]:
            response = self.get(
                self.url,
                data={'part_detail': val, 'project_code_detail': val, 'limit': 1},
                expected_code=200,
            )

            data = response.data['results'][0]

            if val:
                self.assertIn('part_detail', data)
                self.assertIn('project_code_detail', data)
            else:
                self.assertNotIn('part_detail', data)
                self.assertNotIn('project_code_detail', data)

    def test_get_all_builds(self):
        """Retrieve *all* builds via the API."""
        builds = self.get(self.url)

        self.assertEqual(len(builds.data), 5)

        builds = self.get(self.url, data={'active': True})
        self.assertEqual(len(builds.data), 1)

        builds = self.get(self.url, data={'status': BuildStatus.COMPLETE.value})
        self.assertEqual(len(builds.data), 4)

        builds = self.get(self.url, data={'overdue': False})
        self.assertEqual(len(builds.data), 5)

        builds = self.get(self.url, data={'overdue': True})
        self.assertEqual(len(builds.data), 0)

    def test_overdue(self):
        """Create a new build, in the past."""
        in_the_past = datetime.now().date() - timedelta(days=50)

        part = Part.objects.get(pk=50)

        Build.objects.create(
            part=part,
            reference='BO-0006',
            quantity=10,
            title='Just some thing',
            status=BuildStatus.PRODUCTION.value,
            target_date=in_the_past,
        )

        response = self.get(self.url, data={'overdue': True})

        builds = response.data

        self.assertEqual(len(builds), 1)

    def test_sub_builds(self):
        """Test the build / sub-build relationship."""
        parent = Build.objects.get(pk=5)

        part = Part.objects.get(pk=50)

        n = Build.objects.count()

        # Make some sub builds
        for i in range(5):
            Build.objects.create(
                part=part,
                quantity=10,
                reference=f'BO-{i + 10}',
                title=f'Sub build {i}',
                parent=parent,
            )

        # And some sub-sub builds
        for ii, sub_build in enumerate(Build.objects.filter(parent=parent)):
            for i in range(3):
                x = ii * 10 + i + 50
                Build.objects.create(
                    part=part,
                    reference=f'BO-{x}',
                    title=f'{sub_build.reference}-00{i}-sub',
                    quantity=40,
                    parent=sub_build,
                )

        # 20 new builds should have been created!
        self.assertEqual(Build.objects.count(), (n + 20))

        parent.refresh_from_db()

        # There should be 5 sub-builds
        self.assertEqual(parent.get_children().count(), 5)

        # Check tree structure for direct children
        for sub_build in parent.get_children():
            self.assertEqual(sub_build.parent, parent)
            self.assertLess(sub_build.rght, parent.rght)
            self.assertGreater(sub_build.lft, parent.lft)
            self.assertEqual(sub_build.level, parent.level + 1)
            self.assertEqual(sub_build.tree_id, parent.tree_id)
            self.assertEqual(sub_build.get_children().count(), 3)

        # And a total of 20 descendants
        self.assertEqual(parent.get_descendants().count(), 20)

        # Search by parent
        response = self.get(self.url, data={'parent': parent.pk})

        builds = response.data

        self.assertEqual(len(builds), 5)

        # Search by ancestor
        response = self.get(self.url, data={'ancestor': parent.pk})

        builds = response.data

        self.assertEqual(len(builds), 20)

    def test_output_options(self):
        """Test the output options for BuildOrderList list."""
        self.run_output_test(
            self.url,
            [
                'part_detail',
                'project_code_detail',
                ('user_detail', 'responsible_detail'),
                ('user_detail', 'issued_by_detail'),
            ],
            additional_params={'limit': 1},
            assert_fnc=lambda x: x.data['results'][0],
        )


class BuildOutputCreateTest(BuildAPITest):
    """Unit test for creating build output via API."""

    def test_create_serialized_output(self):
        """Create a serialized build output via the API."""
        build_id = 1

        url = reverse('api-build-output-create', kwargs={'pk': build_id})

        build = Build.objects.get(pk=build_id)
        part = build.part

        n_outputs = build.output_count
        n_items = part.stock_items.count()

        # Post with invalid data
        response = self.post(
            url, data={'quantity': 10, 'serial_numbers': '1-100'}, expected_code=400
        )

        self.assertIn(
            'Group range 1-100 exceeds allowed quantity (10)',
            str(response.data['serial_numbers']),
        )

        # Build outputs have not increased
        self.assertEqual(n_outputs, build.output_count)

        # Stock items have not increased
        self.assertEqual(n_items, part.stock_items.count())

        response = self.post(
            url, data={'quantity': 5, 'serial_numbers': '1,2,3-5'}, expected_code=201
        )

        # Build outputs have incdeased
        self.assertEqual(n_outputs + 5, build.output_count)

        # Stock items have increased
        self.assertEqual(n_items + 5, part.stock_items.count())

        # Serial numbers have been created
        for sn in range(1, 6):
            self.assertTrue(part.stock_items.filter(serial=sn).exists())

    def test_create_unserialized_output(self):
        """Create an unserialized build output via the API."""
        build_id = 1
        url = reverse('api-build-output-create', kwargs={'pk': build_id})

        build = Build.objects.get(pk=build_id)
        part = build.part

        n_outputs = build.output_count
        n_items = part.stock_items.count()

        # Create a single new output
        self.post(url, data={'quantity': 10}, expected_code=201)

        # Build outputs have increased
        self.assertEqual(n_outputs + 1, build.output_count)

        # Stock items have increased
        self.assertEqual(n_items + 1, part.stock_items.count())


class BuildOutputScrapTest(BuildAPITest):
    """Unit tests for scrapping build outputs."""

    def scrap(self, build_id, data, expected_code=None):
        """Helper method to POST to the scrap API."""
        url = reverse('api-build-output-scrap', kwargs={'pk': build_id})

        response = self.post(url, data, expected_code=expected_code)

        return response.data

    def test_invalid_scraps(self):
        """Test that invalid scrap attempts are rejected."""
        # Test with missing required fields
        response = self.scrap(1, {}, expected_code=400)

        for field in ['outputs', 'location', 'notes']:
            self.assertIn('This field is required', str(response[field]))

        # Scrap with no outputs specified
        response = self.scrap(1, {'outputs': [], 'location': 1, 'notes': 'Should fail'})

        self.assertIn('A list of build outputs must be provided', str(response))

        # Scrap with an invalid output ID
        response = self.scrap(
            1,
            {'outputs': [{'output': 9999}], 'location': 1, 'notes': 'Should fail'},
            expected_code=400,
        )

        self.assertIn('object does not exist', str(response['outputs']))

        # Create a build output, for a different build
        build = Build.objects.get(pk=2)
        output = StockItem.objects.create(
            part=build.part,
            quantity=10,
            batch='BATCH-TEST',
            is_building=True,
            build=build,
        )

        response = self.scrap(
            1,
            {'outputs': [{'output': output.pk}], 'location': 1, 'notes': 'Should fail'},
            expected_code=400,
        )

        self.assertIn(
            'Build output does not match the parent build', str(response['outputs'])
        )

    def test_valid_scraps(self):
        """Test that valid scrap attempts succeed."""
        # Create a build output
        build = Build.objects.get(pk=1)

        for _ in range(3):
            build.create_build_output(2)

        outputs = build.build_outputs.all()

        self.assertEqual(outputs.count(), 3)
        self.assertEqual(StockItem.objects.filter(build=build).count(), 3)

        for output in outputs:
            self.assertEqual(output.status, StockStatus.OK)
            self.assertTrue(output.is_building)

        # Scrap all three outputs
        self.scrap(
            1,
            {
                'outputs': [
                    {'output': outputs[0].pk, 'quantity': outputs[0].quantity},
                    {'output': outputs[1].pk, 'quantity': outputs[1].quantity},
                    {'output': outputs[2].pk, 'quantity': outputs[2].quantity},
                ],
                'location': 1,
                'notes': 'Should succeed',
            },
            expected_code=201,
        )

        # There should still be three outputs associated with this build
        self.assertEqual(StockItem.objects.filter(build=build).count(), 3)

        for output in outputs:
            output.refresh_from_db()
            self.assertEqual(output.status, StockStatus.REJECTED)
            self.assertFalse(output.is_building)

    def test_partial_scrap(self):
        """Test partial scrapping of a build output."""
        # Create a build output
        build = Build.objects.get(pk=1)
        output = build.create_build_output(10).first()

        self.assertEqual(build.build_outputs.count(), 1)

        data = {
            'outputs': [{'output': output.pk, 'quantity': 3}],
            'location': 1,
            'notes': 'Invalid scrap',
        }

        # Ensure that an invalid quantity raises an error
        for q in [-3, 0, 99]:
            data['outputs'][0]['quantity'] = q
            self.scrap(build.pk, data, expected_code=400)

        # Partially scrap the output (with a valid quantity)
        data['outputs'][0]['quantity'] = 3
        self.scrap(build.pk, data)

        self.assertEqual(build.build_outputs.count(), 2)
        output.refresh_from_db()
        self.assertEqual(output.quantity, 7)
        self.assertTrue(output.is_building)

        scrapped = output.children.first()
        self.assertEqual(scrapped.quantity, 3)
        self.assertEqual(scrapped.status, StockStatus.REJECTED)
        self.assertFalse(scrapped.is_building)

    def test_partial_complete(self):
        """Test partial completion of a build output."""
        build = Build.objects.get(pk=1)
        output = build.create_build_output(10).first()
        self.assertEqual(build.build_outputs.count(), 1)
        self.assertEqual(output.quantity, 10)
        self.assertTrue(output.is_building)
        self.assertEqual(build.completed, 0)

        url = reverse('api-build-output-complete', kwargs={'pk': build.pk})

        data = {
            'outputs': [{'output': output.pk, 'quantity': 4}],
            'location': 1,
            'notes': 'Partial complete',
        }

        # Ensure that an invalid quantity raises an error
        for q in [-4, 0, 999]:
            data['outputs'][0]['quantity'] = q
            self.post(url, data, expected_code=400)

        # Partially complete the output (with a valid quantity)
        data['outputs'][0]['quantity'] = 4
        self.post(url, data, expected_code=201)

        build.refresh_from_db()
        output.refresh_from_db()
        self.assertEqual(build.completed, 4)
        self.assertEqual(build.build_outputs.count(), 2)
        self.assertEqual(output.quantity, 6)
        self.assertTrue(output.is_building)

        completed_output = output.children.first()
        self.assertEqual(completed_output.quantity, 4)
        self.assertEqual(completed_output.status, StockStatus.OK)
        self.assertFalse(completed_output.is_building)


class BuildLineTests(BuildAPITest):
    """Unit tests for the BuildLine API endpoints."""

    def test_filter_available(self):
        """Filter BuildLine objects by 'available' status."""
        url = reverse('api-build-line-list')

        # First *all* BuildLine objects
        response = self.get(url)
        self.assertEqual(len(response.data), BuildLine.objects.count())

        # Filter by 'available' status
        # Note: The max_query_time is bumped up here, as postgresql backend has some strange issues (only during testing)
        response = self.get(url, data={'available': True}, max_query_time=15)
        n_t = len(response.data)
        self.assertGreater(n_t, 0)

        # Note: The max_query_time is bumped up here, as postgresql backend has some strange issues (only during testing)
        response = self.get(url, data={'available': False}, max_query_time=15)
        n_f = len(response.data)
        self.assertGreater(n_f, 0)

        self.assertEqual(n_t + n_f, BuildLine.objects.count())

    def test_output_options(self):
        """Test output options  for the BuildLine endpoint."""
        self.run_output_test(
            reverse('api-build-line-detail', kwargs={'pk': 2}),
            [
                'bom_item_detail',
                'assembly_detail',
                'part_detail',
                'build_detail',
                'allocations',
            ],
        )

    def test_filter_consumed(self):
        """Filter for the 'consumed' status."""
        # Create a new build order
        assembly = Part.objects.create(
            name='Test Assembly',
            description='Test Assembly Description',
            assembly=True,
            trackable=True,
        )

        for idx in range(3):
            component = Part.objects.create(
                name=f'Test Component {idx}',
                description=f'Test Component Description {idx}',
                trackable=True,
                component=True,
            )

            # Create a BOM item for the assembly
            BomItem.objects.create(part=assembly, sub_part=component, quantity=10)

        build = Build.objects.create(
            part=assembly, reference='BO-12348', quantity=10, title='Test Build'
        )

        lines = list(build.build_lines.all())
        self.assertEqual(len(lines), 3)

        for line in lines:
            self.assertEqual(line.quantity, 100)
            self.assertEqual(line.consumed, 0)

        # Artificially "consume" some of the build lines
        lines[0].consumed = 1
        lines[0].save()

        lines[1].consumed = 50
        lines[1].save()

        lines[2].consumed = 100
        lines[2].save()

        url = reverse('api-build-line-list')

        response = self.get(url, {'build': build.pk, 'consumed': True})

        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['pk'], lines[2].pk)
        self.assertEqual(response.data[0]['consumed'], 100)
        self.assertEqual(response.data[0]['quantity'], 100)

        response = self.get(url, {'build': build.pk, 'consumed': False})

        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['pk'], lines[0].pk)
        self.assertEqual(response.data[0]['consumed'], 1)
        self.assertEqual(response.data[0]['quantity'], 100)
        self.assertEqual(response.data[1]['pk'], lines[1].pk)
        self.assertEqual(response.data[1]['consumed'], 50)
        self.assertEqual(response.data[1]['quantity'], 100)

        # Check that the 'available' filter works correctly also when lines are partially consumed
        for line in lines:
            StockItem.objects.create(part=line.bom_item.sub_part, quantity=60)

        # TODO: 2025-10-02: Work out why this query takes so long with PostgreSQL (in CI)
        # Note: The max_query_time is bumped up here, as postgresql backend has some strange issues (only during testing)
        response = self.get(
            url, {'build': build.pk, 'available': True}, max_query_time=30
        )

        # We expect 2 lines to have "available" stock
        self.assertEqual(len(response.data), 2)

        # TODO: 2025-10-02: Work out why this query takes so long with PostgreSQL (in CI)
        # Note: The max_query_time is bumped up here, as postgresql backend has some strange issues (only during testing)
        response = self.get(
            url, {'build': build.pk, 'available': False}, max_query_time=30
        )

        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['pk'], lines[0].pk)


class BuildConsumeTest(BuildAPITest):
    """Test consuming allocated stock."""

    def setUp(self):
        """Set up test data."""
        super().setUp()

        self.assembly = Part.objects.create(
            name='Test Assembly', description='Test Assembly Description', assembly=True
        )

        self.components = [
            Part.objects.create(
                name=f'Test Component {i}',
                description=f'Test Component Description {i}',
                component=True,
            )
            for i in range(3)
        ]

        self.stock_items = [
            StockItem.objects.create(part=component, quantity=1000)
            for component in self.components
        ]

        self.bom_items = [
            BomItem.objects.create(part=self.assembly, sub_part=component, quantity=10)
            for component in self.components
        ]

        self.build = Build.objects.create(
            part=self.assembly, reference='BO-12349', quantity=10, title='Test Build'
        )

    def allocate_stock(self):
        """Allocate stock items to the build."""
        data = {
            'items': [
                {'build_line': line.pk, 'stock_item': si.pk, 'quantity': 100}
                for line, si in zip(
                    self.build.build_lines.all(), self.stock_items, strict=False
                )
            ]
        }

        self.post(
            reverse('api-build-allocate', kwargs={'pk': self.build.pk}),
            data,
            expected_code=201,
        )

    def test_consume_lines(self):
        """Test consuming against build lines."""
        self.allocate_stock()

        self.assertEqual(self.build.allocated_stock.count(), 3)
        self.assertEqual(self.build.consumed_stock.count(), 0)
        url = reverse('api-build-consume', kwargs={'pk': self.build.pk})

        data = {
            'lines': [{'build_line': line.pk} for line in self.build.build_lines.all()]
        }

        self.post(url, data, expected_code=201)

        self.assertEqual(self.build.allocated_stock.count(), 0)
        self.assertEqual(self.build.consumed_stock.count(), 3)

        for line in self.build.build_lines.all():
            self.assertEqual(line.consumed, 100)

    def test_consume_items(self):
        """Test consuming against build items."""
        self.allocate_stock()

        self.assertEqual(self.build.allocated_stock.count(), 3)
        self.assertEqual(self.build.consumed_stock.count(), 0)
        url = reverse('api-build-consume', kwargs={'pk': self.build.pk})

        data = {
            'items': [
                {'build_item': item.pk, 'quantity': item.quantity}
                for item in self.build.allocated_stock.all()
            ]
        }

        self.post(url, data, expected_code=201)

        self.assertEqual(self.build.allocated_stock.count(), 0)
        self.assertEqual(self.build.consumed_stock.count(), 3)

        for line in self.build.build_lines.all():
            self.assertEqual(line.consumed, 100)
