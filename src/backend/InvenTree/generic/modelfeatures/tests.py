"""Tests for the model features functionality."""

from django.urls import reverse

from taggit.models import Tag

import InvenTree.models
from InvenTree.unit_test import InvenTreeAPITestCase
from part.models import Part

from . import func
from .func import ModelFeatureMixin, clear_model_features_cache, get_model_features


class ContentTypeFeatureAPITests(InvenTreeAPITestCase):
    """Tests for the 'features' field on the ContentType API."""

    def test_features(self):
        """Test that the list endpoint reports features per model type."""
        url = reverse('api-contenttype-list')

        # The 'features' field is not included by default
        data = self.get(url, expected_code=200).data
        self.assertNotIn('features', data[0])

        data = self.get(url, {'features': True}, expected_code=200).data
        features = {item['model']: item['features'] for item in data}
        for f in ['attachments', 'notes', 'parameters', 'barcode']:
            self.assertIn(f'org.inventree.i.modelfeatures.{f}', features['part'])

        self.assertIn(
            'org.inventree.i.modelfeatures.attachments', features['salesorder']
        )
        self.assertIn('org.inventree.i.modelfeatures.notes', features['stockitem'])
        self.assertEqual(features['contenttype'], [])

    def test_model_features(self):
        """Test that features are declared by the model mixins, and cached per application."""
        clear_model_features_cache()

        features = get_model_features(Part)

        self.assertIn('org.inventree.i.modelfeatures.attachments', features)
        self.assertIn('org.inventree.i.modelfeatures.report', features)

        # The cache is built for all models on first access, and reused afterwards
        self.assertIsNotNone(func._model_features_cache)
        self.assertIs(features, get_model_features(Part))

        # Clearing the cache (e.g. after a plugin reload) rebuilds it
        clear_model_features_cache()
        self.assertIsNone(func._model_features_cache)
        self.assertEqual(features, get_model_features(Part))
        self.assertIsNotNone(func._model_features_cache)

        self.assertEqual(get_model_features(None), [])
        self.assertEqual(get_model_features(Tag), [])

        # A custom mixin (e.g. provided by a plugin) can declare a new feature
        class CustomFeatureMixin(ModelFeatureMixin):
            MODEL_FEATURE = 'custom'

        class CustomModel(CustomFeatureMixin, InvenTree.models.InvenTreeNoteMixin):
            class Meta:
                abstract = True

        self.assertEqual(
            get_model_features(CustomModel),
            ['custom', 'org.inventree.i.modelfeatures.notes'],
        )
        self.assertNotIn('custom', get_model_features(Part))
