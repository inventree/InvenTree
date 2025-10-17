"""Low level tests for serializers."""

from django.contrib import admin
from django.contrib.auth.models import User
from django.urls import path, reverse

from rest_framework.serializers import SerializerMethodField

import InvenTree.serializers
from InvenTree.mixins import ListCreateAPI, OutputOptionsMixin
from InvenTree.unit_test import InvenTreeAPITestCase
from InvenTree.urls import third_backendpatterns


class SampleSerializer(
    InvenTree.serializers.FilterableSerializerMixin,
    InvenTree.serializers.InvenTreeModelSerializer,
):
    """Sample serializer for testing FilterableSerializerMixin."""

    class Meta:
        """Meta options."""

        model = User
        fields = ['field_a', 'field_b', 'field_c', 'field_d', 'id']

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

    def sample(self, obj):
        """Sample method field."""
        return 'sample'


class SampleList(OutputOptionsMixin, ListCreateAPI):
    """List endpoint sample."""

    serializer_class = SampleSerializer
    queryset = User.objects.all()
    permission_classes = []


urlpatterns = [
    path('', SampleList.as_view(), name='sample-list'),
    path('admin/', admin.site.urls, name='inventree-admin'),
]
urlpatterns += third_backendpatterns


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

            # Disable field_c using custom filter name
            response = self.client.get(url, {'crazy_name': 'false'})
            self.assertContains(response, 'field_a')
            self.assertNotContains(response, 'field_b')
            self.assertNotContains(response, 'field_c')
            self.assertNotContains(response, 'field_d')
