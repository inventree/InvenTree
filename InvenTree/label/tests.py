# Tests for labels

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os

from django.conf import settings
from django.apps import apps
from django.urls import reverse
from django.core.exceptions import ValidationError

from InvenTree.helpers import validateFilterString
from InvenTree.api_tester import InvenTreeAPITestCase

from .models import StockItemLabel, StockLocationLabel, PartLabel
from stock.models import StockItem


class LabelTest(InvenTreeAPITestCase):

    fixtures = [
        'category',
        'part',
        'location',
        'stock'
    ]

    def setUp(self) -> None:
        super().setUp()
        # ensure the labels were created
        apps.get_app_config('label').create_labels()

    def test_default_labels(self):
        """
        Test that the default label templates are copied across
        """

        labels = StockItemLabel.objects.all()

        self.assertTrue(labels.count() > 0)

        labels = StockLocationLabel.objects.all()

        self.assertTrue(labels.count() > 0)

    def test_default_files(self):
        """
        Test that label files exist in the MEDIA directory
        """

        item_dir = os.path.join(
            settings.MEDIA_ROOT,
            'label',
            'inventree',
            'stockitem',
        )

        files = os.listdir(item_dir)

        self.assertTrue(len(files) > 0)

        loc_dir = os.path.join(
            settings.MEDIA_ROOT,
            'label',
            'inventree',
            'stocklocation',
        )

        files = os.listdir(loc_dir)

        self.assertTrue(len(files) > 0)

    def test_filters(self):
        """
        Test the label filters
        """

        filter_string = "part__pk=10"

        filters = validateFilterString(filter_string, model=StockItem)

        self.assertEqual(type(filters), dict)

        bad_filter_string = "part_pk=10"

        with self.assertRaises(ValidationError):
            validateFilterString(bad_filter_string, model=StockItem)

    def test_label_rendering(self):
        """Test label rendering"""

        labels = PartLabel.objects.all()
        part = PartLabel.objects.first()

        for label in labels:

            print("Printing label:", label.pk, part.pk)

            url = reverse('api-part-label-print', kwargs={'pk': label.pk})

            print("URL:", url)
            response = self.get(f'{url}?parts={part.pk}')

            print("Response:")
            print(response)
