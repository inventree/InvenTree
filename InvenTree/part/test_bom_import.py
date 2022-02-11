"""
Unit testing for BOM upload / import functionality
"""

import tablib

from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from InvenTree.api_tester import InvenTreeAPITestCase

from part.models import Part


class BomUploadTest(InvenTreeAPITestCase):
    """
    Test BOM file upload API endpoint
    """

    roles = [
        'part.add',
        'part.change',
    ]

    def setUp(self):
        super().setUp()

        self.part = Part.objects.create(
            name='Assembly',
            description='An assembled part',
            assembly=True,
            component=False,
        )

        for i in range(10):
            Part.objects.create(
                name=f"Component {i}",
                IPN=f"CMP_{i}",
                description="A subcomponent that can be used in a BOM",
                component=True,
                assembly=False,
            )

        self.url = reverse('api-bom-extract')

    def post_bom(self, filename, file_data, part=None, clear_existing=None, expected_code=None, content_type='text/plain'):

        bom_file = SimpleUploadedFile(
            filename,
            file_data,
            content_type=content_type,
        )

        if part is None:
            part = self.part.pk

        if clear_existing is None:
            clear_existing = False

        response = self.post(
            self.url,
            data={
                'bom_file': bom_file,
                'part': part,
                'clear_existing': clear_existing,
            },
            expected_code=expected_code,
            format='multipart',
        )

        return response

    def test_missing_file(self):
        """
        POST without a file
        """

        response = self.post(
            self.url,
            data={},
            expected_code=400
        )

        self.assertIn('No file was submitted', str(response.data['bom_file']))
        self.assertIn('This field is required', str(response.data['part']))
        self.assertIn('This field is required', str(response.data['clear_existing']))

    def test_unsupported_file(self):
        """
        POST with an unsupported file type
        """

        response = self.post_bom(
            'sample.txt',
            b'hello world',
            expected_code=400,
        )

        self.assertIn('Unsupported file type', str(response.data['bom_file']))

    def test_broken_file(self):
        """
        Test upload with broken (corrupted) files
        """

        response = self.post_bom(
            'sample.csv',
            b'',
            expected_code=400,
        )

        self.assertIn('The submitted file is empty', str(response.data['bom_file']))

        response = self.post_bom(
            'test.xls',
            b'hello world',
            expected_code=400,
            content_type='application/xls',
        )

        self.assertIn('Unsupported format, or corrupt file', str(response.data['bom_file']))

    def test_invalid_upload(self):
        """
        Test upload of an invalid file
        """

        dataset = tablib.Dataset()

        dataset.headers = [
            'apple',
            'banana',
        ]

        response = self.post_bom(
            'test.csv',
            bytes(dataset.csv, 'utf8'),
            content_type='text/csv',
            expected_code=400,
        )

        self.assertIn("Missing required column: 'quantity'", str(response.data))

        # Try again, with an .xlsx file
        response = self.post_bom(
            'bom.xlsx',
            dataset.xlsx,
            content_type='application/xlsx',
            expected_code=400,
        )

        self.assertIn("Missing required column: 'quantity'", str(response.data))

        # Add the quantity field (or close enough)
        dataset.headers.append('quAntiTy  ')

        response = self.post_bom(
            'test.csv',
            bytes(dataset.csv, 'utf8'),
            content_type='text/csv',
            expected_code=400,
        )

        self.assertIn('No part column found', str(response.data))

        dataset.headers.append('part_id')
        dataset.headers.append('part_name')

        response = self.post_bom(
            'test.csv',
            bytes(dataset.csv, 'utf8'),
            content_type='text/csv',
            expected_code=400,
        )

        self.assertIn('No data rows found', str(response.data))

    def test_invalid_data(self):
        """
        Upload data which contains errors
        """

        dataset = tablib.Dataset()

        # Only these headers are strictly necessary
        dataset.headers = ['part_id', 'quantity']

        components = Part.objects.filter(component=True)

        for idx, cmp in enumerate(components):

            if idx == 5:
                cmp.component = False
                cmp.save()

            dataset.append([cmp.pk, idx])

        # Add a duplicate part too
        dataset.append([components.first().pk, 'invalid'])

        response = self.post_bom(
            'test.csv',
            bytes(dataset.csv, 'utf8'),
            content_type='text/csv',
            expected_code=201
        )

        errors = response.data['errors']

        self.assertIn('Quantity must be greater than zero', str(errors[0]))
        self.assertIn('Part is not designated as a component', str(errors[5]))
        self.assertIn('Duplicate part selected', str(errors[-1]))
        self.assertIn('Invalid quantity', str(errors[-1]))

        for idx, row in enumerate(response.data['rows'][:-1]):
            self.assertEqual(str(row['part']), str(components[idx].pk))

    def test_part_guess(self):
        """
        Test part 'guessing' when PK values are not supplied
        """

        dataset = tablib.Dataset()

        # Should be able to 'guess' the part from the name
        dataset.headers = ['part_name', 'quantity']

        components = Part.objects.filter(component=True)

        for idx, cmp in enumerate(components):
            dataset.append([
                f"Component {idx}",
                10,
            ])

        response = self.post_bom(
            'test.csv',
            bytes(dataset.csv, 'utf8'),
            expected_code=201,
        )

        rows = response.data['rows']

        self.assertEqual(len(rows), 10)

        for idx in range(10):
            self.assertEqual(rows[idx]['part'], components[idx].pk)

        # Should also be able to 'guess' part by the IPN value
        dataset = tablib.Dataset()

        dataset.headers = ['part_ipn', 'quantity']

        for idx, cmp in enumerate(components):
            dataset.append([
                f"CMP_{idx}",
                10,
            ])

        response = self.post_bom(
            'test.csv',
            bytes(dataset.csv, 'utf8'),
            expected_code=201,
        )

        rows = response.data['rows']

        self.assertEqual(len(rows), 10)

        for idx in range(10):
            self.assertEqual(rows[idx]['part'], components[idx].pk)

    def test_levels(self):
        """
        Test that multi-level BOMs are correctly handled during upload
        """

        dataset = tablib.Dataset()

        dataset.headers = ['level', 'part', 'quantity']

        components = Part.objects.filter(component=True)

        for idx, cmp in enumerate(components):
            dataset.append([
                idx % 3,
                cmp.pk,
                2,
            ])

        response = self.post_bom(
            'test.csv',
            bytes(dataset.csv, 'utf8'),
            expected_code=201,
        )

        # Only parts at index 1, 4, 7 should have been returned
        self.assertEqual(len(response.data['rows']), 3)
