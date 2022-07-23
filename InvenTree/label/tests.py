"""Tests for labels"""

from django.apps import apps
from django.conf import settings
from django.core.exceptions import ValidationError
from django.urls import reverse

from InvenTree.api_tester import InvenTreeAPITestCase
from InvenTree.helpers import validateFilterString
from part.models import Part
from stock.models import StockItem

from .models import PartLabel, StockItemLabel, StockLocationLabel


class LabelTest(InvenTreeAPITestCase):
    """Unit test class for label models"""

    fixtures = [
        'category',
        'part',
        'location',
        'stock'
    ]

    def setUp(self) -> None:
        """Ensure that some label instances exist as part of init routine"""
        super().setUp()
        apps.get_app_config('label').create_labels()

    def test_default_labels(self):
        """Test that the default label templates are copied across."""
        labels = StockItemLabel.objects.all()

        self.assertTrue(labels.count() > 0)

        labels = StockLocationLabel.objects.all()

        self.assertTrue(labels.count() > 0)

    def test_default_files(self):
        """Test that label files exist in the MEDIA directory."""
        item_dir = settings.MEDIA_ROOT.joinpath(
            'label',
            'inventree',
            'stockitem',
        )

        files = item_dir.iterdir()
        self.assertTrue(len(files) > 0)

        loc_dir = settings.MEDIA_ROOT.joinpath(
            'label',
            'inventree',
            'stocklocation',
        )

        files = loc_dir.iterdir()
        self.assertTrue(len(files) > 0)

    def test_filters(self):
        """Test the label filters."""
        filter_string = "part__pk=10"

        filters = validateFilterString(filter_string, model=StockItem)

        self.assertEqual(type(filters), dict)

        bad_filter_string = "part_pk=10"

        with self.assertRaises(ValidationError):
            validateFilterString(bad_filter_string, model=StockItem)

    def test_label_rendering(self):
        """Test label rendering."""
        labels = PartLabel.objects.all()
        part = Part.objects.first()

        for label in labels:
            url = reverse('api-part-label-print', kwargs={'pk': label.pk})
            self.get(f'{url}?parts={part.pk}', expected_code=200)
