"""Tests for the fast serializer representation path, and fast media URL generation."""

import datetime
import random
from zoneinfo import ZoneInfo

from django.core.files.storage import default_storage
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from rest_framework import serializers

import InvenTree.fast_representation as fr
from InvenTree.helpers import get_media_url
from InvenTree.serializers import InvenTreeModelSerializer
from InvenTree.unit_test import InvenTreeAPITestCase
from stock.models import StockItem


class SampleStockSerializer(InvenTreeModelSerializer):
    """Serializer exercising each fast-path mode, plus fallback cases."""

    class Meta:
        """Meta options."""

        model = StockItem
        fields = [
            'pk',
            'batch',
            'serial',
            'delete_on_deplete',
            'is_building',
            'part',
            'location',
            'updated',
            'creation_date',
            'char_from_int',
            'int_from_bool',
            'float_from_decimal',
            'readonly_value',
            'callable_source',
            'missing_null',
            'missing_skip',
        ]

    # VALUE fields with mismatched types -> field.to_representation() coercion
    char_from_int = serializers.CharField(source='part_id', read_only=True)
    int_from_bool = serializers.IntegerField(source='is_building', read_only=True)
    float_from_decimal = serializers.FloatField(source='quantity', read_only=True)
    readonly_value = serializers.ReadOnlyField(source='quantity')

    # Callable source -> generic path (DRF calls the method)
    callable_source = serializers.CharField(source='get_absolute_url', read_only=True)

    # Missing attributes -> DRF default handling (None, or key omitted)
    missing_null = serializers.CharField(
        source='no_such_attribute', read_only=True, allow_null=True
    )
    missing_skip = serializers.CharField(source='no_such_attribute', read_only=True)


class FastRepresentationTest(TestCase):
    """Unit tests for InvenTree.fast_representation."""

    fixtures = ['category', 'part', 'location', 'stock']

    def compare(self, serializer_class, instances, **kwargs):
        """Assert that fast and standard (DRF) output are identical."""
        self.assertGreater(len(instances), 0)

        try:
            serializer_class.FAST_REPRESENTATION = False
            expected = serializer_class(instances, many=True, **kwargs).data
        finally:
            serializer_class.FAST_REPRESENTATION = True

        result = serializer_class(instances, many=True, **kwargs).data

        self.assertEqual(len(result), len(expected))

        for a, b in zip(result, expected, strict=True):
            self.assertEqual(a, b)
            # Key order must also be preserved
            self.assertEqual(list(a.keys()), list(b.keys()))

        return result

    def test_plan_modes(self):
        """Fields are classified into the expected fast-path modes."""
        serializer = SampleStockSerializer()
        plan = {
            name: mode for name, _, mode, *_ in fr.build_plan(serializer, StockItem)
        }

        self.assertEqual(plan['batch'], fr.VALUE)
        self.assertEqual(plan['delete_on_deplete'], fr.VALUE)
        self.assertEqual(plan['readonly_value'], fr.VALUE)
        self.assertEqual(plan['part'], fr.PK)
        self.assertEqual(plan['location'], fr.PK)
        self.assertEqual(plan['updated'], fr.DATETIME)
        self.assertEqual(plan['creation_date'], fr.DATETIME)

        # Custom datetime format -> not supported by fast path
        field = serializers.DateTimeField(format='%Y')
        field.bind('x', serializer)
        self.assertEqual(fr.classify_field(field, StockItem)[0], fr.GENERIC)

        # Dotted source -> generic
        field = serializers.CharField(source='part.name')
        field.bind('y', serializer)
        self.assertEqual(fr.classify_field(field, StockItem)[0], fr.GENERIC)

    def test_sample_serializer(self):
        """Fast output matches DRF for all field modes and fallbacks."""
        items = list(StockItem.objects.all())

        # Include some edge-case values
        items[0].batch = None
        items[1].location = None
        items[2].updated = None
        items[3].serial = 12345  # Non-str value for a CharField

        result = self.compare(SampleStockSerializer, items)

        self.assertNotIn('missing_skip', result[0])
        self.assertIsNone(result[0]['missing_null'])
        self.assertEqual(result[3]['serial'], '12345')

    def test_datetime_timezones(self):
        """Datetime output matches DRF across timezone / format settings."""
        items = list(StockItem.objects.all()[:10])

        aware = datetime.datetime(2024, 6, 30, 23, 45, 12, tzinfo=datetime.UTC)
        naive = datetime.datetime(2024, 1, 15, 3, 4, 5)

        for idx, item in enumerate(items):
            item.updated = aware if idx % 2 else naive
            item.creation_date = naive if idx % 2 else aware

        for use_tz in (True, False):
            for tz in ('UTC', 'Australia/Sydney', 'America/New_York'):
                for fmt in ('%Y-%m-%d %H:%M', 'iso-8601', None):
                    with (
                        self.subTest(use_tz=use_tz, tz=tz, fmt=fmt),
                        override_settings(
                            USE_TZ=use_tz,
                            TIME_ZONE=tz,
                            REST_FRAMEWORK={'DATETIME_FORMAT': fmt},
                        ),
                        timezone.override(ZoneInfo(tz)),
                    ):
                        self.compare(SampleStockSerializer, items)

    def test_mro_guard(self):
        """A to_representation() override after the base class disables the fast path."""

        class LateMixin(serializers.Serializer):
            def to_representation(self, instance):
                data = super().to_representation(instance)
                data['late'] = True
                return data

        class GuardedSerializer(InvenTreeModelSerializer, LateMixin):
            class Meta:
                model = StockItem
                fields = ['pk', 'batch']

        self.assertFalse(
            fr.check_serializer_class(GuardedSerializer, InvenTreeModelSerializer)
        )
        self.assertTrue(
            fr.check_serializer_class(SampleStockSerializer, InvenTreeModelSerializer)
        )

        data = GuardedSerializer(StockItem.objects.first()).data
        self.assertTrue(data['late'])

    def test_non_model_instance(self):
        """Non-model instances (e.g. dicts) use the standard path."""

        class DictSerializer(InvenTreeModelSerializer):
            class Meta:
                model = StockItem
                fields = ['batch', 'serial']

        data = DictSerializer({'batch': 'B1', 'serial': 7}).data
        self.assertEqual(data, {'batch': 'B1', 'serial': '7'})


class FastRepresentationApiTest(InvenTreeAPITestCase):
    """Compare API list output with the fast path enabled vs disabled."""

    fixtures = [
        'category',
        'part',
        'location',
        'stock',
        'bom',
        'company',
        'supplier_part',
        'manufacturer_part',
        'params',
        'test_templates',
    ]

    roles = 'all'
    superuser = True

    URLS = [
        (
            'api-stock-list',
            'part_detail=true&location_detail=true&supplier_part_detail=true',
        ),
        ('api-part-list', 'category_detail=true&location_detail=true&parameters=true'),
        ('api-part-category-list', 'path_detail=true'),
        ('api-location-list', 'path_detail=true'),
        ('api-company-list', ''),
        (
            'api-supplier-part-list',
            'part_detail=true&supplier_detail=true&manufacturer_detail=true',
        ),
        ('api-manufacturer-part-list', 'part_detail=true&manufacturer_detail=true'),
        ('api-bom-list', 'part_detail=true&sub_part_detail=true'),
    ]

    def test_api_equivalence(self):
        """API responses are identical with and without the fast path."""
        for name, query in self.URLS:
            url = f'{reverse(name)}?{query}'

            with self.subTest(url=url):
                try:
                    InvenTreeModelSerializer.FAST_REPRESENTATION = False
                    expected = self.get(url, expected_code=200).data
                finally:
                    InvenTreeModelSerializer.FAST_REPRESENTATION = True

                result = self.get(url, expected_code=200).data

                self.assertGreater(len(result), 0)
                self.assertEqual(result, expected)


class MediaUrlTest(TestCase):
    """Tests for InvenTree.helpers.get_media_url."""

    NAMES = [
        '',
        'a.png',
        '/a.png',
        '//a.png',
        'part_images/x.thumbnail.png',
        'a/./b.png',
        'a/../b.png',
        '../x',
        './x',
        '.',
        '..',
        'a/..b/c',
        'a//b',
        'a?b#c;d:e',
        'http://evil.com/x',
        'C:\\x\\y.png',
        'ünï cödé.png',
        '%2e%2e/x',
        'x/',
    ]

    def check_names(self, names):
        """Assert get_media_url matches default_storage.url for all names."""
        for name in names:
            self.assertEqual(get_media_url(name), default_storage.url(name), name)

    def test_equivalence(self):
        """Output matches default_storage.url() for the filesystem backend."""
        rnd = random.Random(0)
        alphabet = "ab./\\?#;:%~!*()'é "
        fuzz = [
            ''.join(rnd.choice(alphabet) for _ in range(rnd.randint(0, 12)))
            for _ in range(2000)
        ]

        for media_url in ('/media/', 'https://cdn.example.com/media/'):
            with override_settings(MEDIA_URL=media_url):
                self.check_names(self.NAMES + fuzz)

    @override_settings(
        STORAGES={
            'default': {
                'BACKEND': 'django.core.files.storage.InMemoryStorage',
                'OPTIONS': {'base_url': '/memory/'},
            },
            'staticfiles': {
                'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'
            },
        }
    )
    def test_other_backend(self):
        """Other storage backends are delegated to default_storage.url()."""
        self.assertEqual(get_media_url('a/b.png'), '/memory/a/b.png')
        self.check_names(self.NAMES)
