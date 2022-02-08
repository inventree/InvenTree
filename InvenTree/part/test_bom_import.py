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

        dataset.append(['test', 'test'])
        dataset.append(['hello', 'world'])

        response = self.post_bom(
            'test.csv',
            bytes(dataset.csv, 'utf8'),
            expected_code=400,
            content_type='text/csv',
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
