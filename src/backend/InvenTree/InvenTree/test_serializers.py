"""Low level tests for serializers."""

from django.contrib import admin
from django.contrib.auth.models import User
from django.urls import path, reverse

from rest_framework.serializers import SerializerMethodField

import InvenTree.serializers
from InvenTree.mixins import ListCreateAPI, OutputOptionsMixin
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
    field_b = InvenTree.serializers.enable_filter(
        InvenTree.serializers.FilterableSerializerMethodField(method_name='sample')
    )
    field_c = InvenTree.serializers.enable_filter(
        InvenTree.serializers.FilterableSerializerMethodField(method_name='sample'),
        True,
        filter_name='crazy_name',
    )
    field_d = InvenTree.serializers.enable_filter(
        InvenTree.serializers.FilterableSerializerMethodField(method_name='sample'),
        True,
        filter_name='crazy_name',
    )
    field_e = InvenTree.serializers.enable_filter(
        InvenTree.serializers.FilterableSerializerMethodField(method_name='sample'),
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

    def test_failiure_enable_filter(self):
        """Test sanity check for enable_filter."""
        # Allowed usage
        field_b = InvenTree.serializers.enable_filter(  # noqa: F841
            InvenTree.serializers.FilterableSerializerMethodField(method_name='sample')
        )

        # Disallowed usage
        with self.assertRaises(Exception) as cm:
            field_a = InvenTree.serializers.enable_filter(  # noqa: F841
                SerializerMethodField(method_name='sample')
            )
        self.assertIn(
            'INVE-I2: `enable_filter` can only be applied to serializer fields',
            str(cm.exception),
        )

    def test_failiure_FilterableSerializerMixin(self):
        """Test failure case for FilteredSerializerMixin."""

        class BadSerializer(
            InvenTree.serializers.FilterableSerializerMixin,
            InvenTree.serializers.InvenTreeModelSerializer,
        ):
            """Bad serializer for testing FilterableSerializerMixin."""

            class Meta:
                """Meta options."""

                model = User
                fields = ['field_a', 'id']

            field_a = SerializerMethodField(method_name='sample')

            def sample(self, obj):
                """Sample method field."""
                return 'sample'  # pragma: no cover

        with self.assertRaises(Exception) as cm:
            _ = BadSerializer()
        self.assertIn(
            'INVE-I2: No filter targets found in fields, remove `PathScopedMixin`',
            str(cm.exception),
        )

        # Test override
        BadSerializer.no_filters = True
        _ = BadSerializer()
        self.assertTrue(True)  # Dummy assertion to ensure we reach here

    def test_failure_OutputOptionsMixin(self):
        """Test failure case for OutputOptionsMixin."""

        class BadSerializer(InvenTree.serializers.InvenTreeModelSerializer):
            """Sample serializer."""

            class Meta:
                """Meta options."""

                model = User
                fields = ['id']

            field_a = SerializerMethodField(method_name='sample')

        # Bad implementation of OutputOptionsMixin
        with self.assertRaises(Exception) as cm:

            class BadList(OutputOptionsMixin, ListCreateAPI):
                """Bad list endpoint for testing OutputOptionsMixin."""

                serializer_class = BadSerializer
                queryset = User.objects.all()
                permission_classes = []

            self.assertTrue(True)
            _ = BadList()  # this should raise an exception
        self.assertEqual(
            str(cm.exception),
            'INVE-I2: `OutputOptionsMixin` can only be used with serializers that contain the `FilterableSerializerMixin` mixin',
        )

        # More creative bad implementation
        with self.assertRaises(Exception) as cm:

            class BadList(OutputOptionsMixin, ListCreateAPI):
                """Bad list endpoint for testing OutputOptionsMixin."""

                queryset = User.objects.all()
                permission_classes = []

                def get_serializer(self, *args, **kwargs):
                    """Get serializer override."""
                    self.serializer_class = BadSerializer
                    return super().get_serializer(*args, **kwargs)

            view = BadList()
            self.assertTrue(True)
            # mock some stuff to allow get_serializer to run
            view.request = self.client.request()
            view.format_kwarg = {}
            view.get_serializer()  # this should raise an exception

        self.assertEqual(
            str(cm.exception),
            'INVE-I2: `OutputOptionsMixin` can only be used with serializers that contain the `FilterableSerializerMixin` mixin',
        )
