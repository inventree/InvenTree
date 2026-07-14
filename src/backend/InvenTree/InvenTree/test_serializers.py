"""Low level tests for serializers."""

from django.contrib import admin
from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured
from django.urls import path, reverse

from rest_framework.serializers import SerializerMethodField

import InvenTree.serializers
from InvenTree.mixins import ListCreateAPI, OutputOptionsMixin
from InvenTree.serializers import OptionalField
from InvenTree.unit_test import InvenTreeAPITestCase
from InvenTree.urls import backendpatterns


class SampleSerializer(
    InvenTree.serializers.FilterableSerializerMixin,
    InvenTree.serializers.InvenTreeModelSerializer,
):
    """Sample serializer for testing FilterableSerializerMixin."""

    class Meta:
        """Meta options."""

        model = User
        fields = ['field_a', 'field_b', 'field_c', 'field_d', 'field_e', 'id']

    field_a = SerializerMethodField(method_name='sample')
    field_b = OptionalField(
        serializer_class=SerializerMethodField,
        serializer_kwargs={'method_name': 'sample'},
    )
    field_c = OptionalField(
        serializer_class=SerializerMethodField,
        serializer_kwargs={'method_name': 'sample'},
        default_include=True,
        filter_name='crazy_name',
    )
    field_d = OptionalField(
        serializer_class=SerializerMethodField,
        serializer_kwargs={'method_name': 'sample'},
        default_include=True,
        filter_name='crazy_name',
    )
    field_e = OptionalField(
        serializer_class=SerializerMethodField,
        serializer_kwargs={'method_name': 'sample'},
        filter_name='field_e',
        filter_by_query=False,
    )

    def sample(self, obj):
        """Sample method field."""
        return 'sample123'


class SampleList(OutputOptionsMixin, ListCreateAPI):
    """List endpoint sample."""

    serializer_class = SampleSerializer
    queryset = User.objects.all()
    permission_classes = []


urlpatterns = [
    path('', SampleList.as_view(), name='sample-list'),
    path('admin/', admin.site.urls, name='inventree-admin'),
]
urlpatterns += backendpatterns


class FilteredSerializers(InvenTreeAPITestCase):
    """Tests for functionality of FilteredSerializerMixin / adjacent functions."""

    def test_basic_setup(self):
        """Test simple sample setup."""
        with self.settings(
            ROOT_URLCONF=__name__,
            CSRF_TRUSTED_ORIGINS=['http://testserver'],
            SITE_URL='http://testserver',
        ):
            url = reverse('sample-list', urlconf=__name__)

            # Default request (no filters)
            response = self.client.get(url)
            self.assertContains(response, 'field_a')
            self.assertNotContains(response, 'field_b')
            self.assertContains(response, 'field_c')
            self.assertContains(response, 'field_d')

            # Request with filter for field_b
            response = self.client.get(url, {'field_b': True})
            self.assertContains(response, 'field_a')
            self.assertContains(response, 'field_b')
            self.assertContains(response, 'field_c')
            self.assertContains(response, 'field_d')

            self.assertEqual(response.data[0]['field_b'], 'sample123')

            # Disable field_c using custom filter name
            response = self.client.get(url, {'crazy_name': 'false'})
            self.assertContains(response, 'field_a')
            self.assertNotContains(response, 'field_b')
            self.assertNotContains(response, 'field_c')
            self.assertNotContains(response, 'field_d')

            # Query parameters being turned off means it should not be enable-able
            response = self.client.get(url, {'field_e': True})
            self.assertContains(response, 'field_a')
            self.assertNotContains(response, 'field_b')
            self.assertContains(response, 'field_c')
            self.assertContains(response, 'field_d')
            self.assertNotContains(response, 'field_e')


class BarcodeSerializerMixinTest(InvenTreeAPITestCase):
    """Tests for the shared BarcodeSerializerMixin.

    Ref #11745: every model which supports custom (third-party) barcodes must
    expose the linked barcode string ('barcode_data') via its API serializer,
    as a read-only field, so that it can be displayed in the user interface.
    """

    def test_barcode_data_field_exposed(self):
        """'barcode_data' must be present and read-only on every barcode serializer."""
        from build.serializers import BuildSerializer
        from company.serializers import (
            ManufacturerPartSerializer,
            SupplierPartSerializer,
        )
        from order.serializers import (
            PurchaseOrderSerializer,
            ReturnOrderSerializer,
            SalesOrderSerializer,
            SalesOrderShipmentSerializer,
            TransferOrderSerializer,
        )
        from part.serializers import PartSerializer
        from stock.serializers import LocationSerializer, StockItemSerializer

        serializers = [
            PartSerializer,
            StockItemSerializer,
            LocationSerializer,
            BuildSerializer,
            ManufacturerPartSerializer,
            SupplierPartSerializer,
            PurchaseOrderSerializer,
            SalesOrderSerializer,
            ReturnOrderSerializer,
            TransferOrderSerializer,
            SalesOrderShipmentSerializer,
        ]

        for serializer in serializers:
            fields = serializer().fields
            self.assertIn(
                'barcode_data',
                fields,
                f"'barcode_data' missing from {serializer.__name__}",
            )
            self.assertTrue(
                fields['barcode_data'].read_only,
                f"'barcode_data' must be read-only in {serializer.__name__}",
            )

    def test_misconfiguration_raises(self):
        """The mixin must reject serializers which are configured incorrectly."""
        from part.models import Part

        # Case 1: the model does not support custom barcodes
        class NoBarcodeModelSerializer(
            InvenTree.serializers.BarcodeSerializerMixin,
            InvenTree.serializers.InvenTreeModelSerializer,
        ):
            class Meta:
                model = User
                fields = ['id', 'barcode_data']

        with self.assertRaises(ImproperlyConfigured):
            NoBarcodeModelSerializer()

        # Case 2: 'barcode_data' is omitted from Meta.fields
        class MissingFieldSerializer(
            InvenTree.serializers.BarcodeSerializerMixin,
            InvenTree.serializers.InvenTreeModelSerializer,
        ):
            class Meta:
                model = Part
                fields = ['pk']

        with self.assertRaises(ImproperlyConfigured):
            MissingFieldSerializer()
