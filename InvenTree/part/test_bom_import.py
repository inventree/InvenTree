"""
Unit testing for BOM import functionality
"""

import csv
import io

from django.urls.base import reverse

from rest_framework import status
from rest_framework.test import APIClient

from InvenTree.api_tester import InvenTreeAPITestCase

from part.models import Part


class BomImportTest(InvenTreeAPITestCase):
    """
    Unit testing for BOM import
    """

    roles = [
        'part.add',
        'part.change',
    ]

    def setUp(self):
        
        super().setUp()

        # Add some parts to the database
        self.assembly = Part.objects.create(
            name='An assembly',
            description='Can be assembled',
            assembly=True,
        )

        self.sub_parts = []

        # Create some compoments
        for i in range(10):
            self.sub_parts.append(Part.objects.create(
                name=f"Component {i}",
                description="A sub component which can be used in a BOM",
                component=True
            ))

    def test_file_upload(self):
        """
        Test that a BOM file can be uploaded
        """

        # Create an in-memory CSV file
        csv_file = io.StringIO()

        writer = csv.writer(csv_file, delimiter=',')

        headers = [
            'part_id',
            'part_name',
            'part_IPN',
            'part_description',
            'quantity',
            'optional',
        ]

        writer.writerow(headers)

        for ii, part in enumerate(self.sub_parts):
            writer.writerow([
                part.pk,
                part.name,
                part.IPN,
                part.description,
                ii,
                False
            ])

        csv_file.seek(0)

        response = self.client.post(
            reverse('api-bom-upload', kwargs={'pk': self.assembly.pk}),
            {
                'file': csv_file,
                'apple': 'banana',
            },
            format='multipart',
        )

        print(response)