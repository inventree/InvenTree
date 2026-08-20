"""Low level tests for serializers."""

import sys
import threading
from concurrent.futures import ThreadPoolExecutor

from django.contrib import admin
from django.contrib.auth.models import User
from django.urls import path, reverse

from rest_framework.serializers import SerializerMethodField

import InvenTree.serializers
from InvenTree.mixins import ListCreateAPI, OutputOptionsMixin
from InvenTree.serializers import OptionalField
from InvenTree.unit_test import InvenTreeAPITestCase
from InvenTree.urls import backendpatterns
from part.models import Part


class SampleSerializer(
    InvenTree.serializers.FilterableSerializerMixin,
    InvenTree.serializers.InvenTreeModelSerializer,
):
    """Sample serializer for testing FilterableSerializerMixin."""

    class Meta:
        """Meta options."""

        model = User
        fields = [
            'field_a',
            'field_b',
            'field_c',
            'field_d',
            'field_e',
            'field_f',
            'id',
        ]

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

    # Field which embeds a model the requesting user may not have permission to view
    field_f = OptionalField(
        serializer_class=SerializerMethodField,
        serializer_kwargs={'method_name': 'sample'},
        default_include=True,
        filter_name='field_f',
        model=Part,
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

    def test_permission_gating(self):
        """An OptionalField which embeds a model should respect the model's permissions.

        'field_f' defaults to included, but declares 'model=Part' - it should only
        appear in the response if the requesting user actually has 'part.view'.
        """
        with self.settings(
            ROOT_URLCONF=__name__,
            CSRF_TRUSTED_ORIGINS=['http://testserver'],
            SITE_URL='http://testserver',
        ):
            url = reverse('sample-list', urlconf=__name__)

            # No 'part' role assigned - field should be hidden despite default_include=True
            response = self.client.get(url)
            self.assertContains(response, 'field_a')
            self.assertNotContains(response, 'field_f')

            # Assign the 'part.view' role - field should now appear
            self.assignRole('part.view')
            response = self.client.get(url)
            self.assertContains(response, 'field_f')
            self.assertEqual(response.data[0]['field_f'], 'sample123')


class ConcurrentOptionalFieldTests(InvenTreeAPITestCase):
    """Regression test for a race condition in `FilterableSerializerMixin.get_field_names`.

    When `Meta.fields` is a plain list (as it is for every real serializer in this
    codebase), DRF's `ModelSerializer.get_field_names()` returns that *exact* list
    object rather than a copy - a single list shared by every instance of the
    serializer class, across every thread. `get_field_names()` used to `.append()`/
    `.remove()` an OptionalField's name directly on that shared list.

    Two concurrent requests that disagree on whether an OptionalField (here,
    `field_b`) should be included could then corrupt each other's output: one
    request's `.append('field_b')` could be immediately undone by another,
    concurrent request's `.remove('field_b')` on the *same* list object, before
    the first request's own field-building loop (DRF's `get_fields()`, which
    iterates this same list) reached it - silently dropping the field from a
    response that should have included it.
    """

    def test_concurrent_optional_field_inclusion(self):
        """Serializers built concurrently with conflicting field_b inclusion must not corrupt each other.

        Builds many `SampleSerializer` instances in parallel threads, alternating
        whether `field_b` should be included (passed directly as a constructor
        kwarg, per `FilterableSerializerMixin.is_field_included`, so this needs no
        HTTP request/response machinery). Every instance's rendered `.data` must
        match what *that* instance asked for, regardless of what other concurrently
        running instances asked for.
        """
        errors = []
        lock = threading.Lock()

        def worker(include: bool):
            serializer = SampleSerializer(self.user, field_b=include)
            has_field_b = 'field_b' in serializer.data
            if has_field_b != include:
                with lock:
                    errors.append((include, has_field_b))

        # Force frequent thread switches - the race window between the shared
        # list being fixed up and it being iterated over is only a handful of
        # bytecodes wide, so the default switch interval rarely lands inside it.
        old_interval = sys.getswitchinterval()
        sys.setswitchinterval(1e-6)
        try:
            with ThreadPoolExecutor(max_workers=16) as executor:
                futures = [executor.submit(worker, i % 2 == 0) for i in range(2000)]
                for future in futures:
                    future.result()
        finally:
            sys.setswitchinterval(old_interval)

        self.assertEqual(
            errors,
            [],
            f'{len(errors)} / 2000 concurrently-built serializers had the wrong '
            f"'field_b' inclusion (expected, got) pairs shown above",
        )
