"""Mixins for (API) views in the whole project."""

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import connection, models, transaction

from rest_framework import generics, mixins, status
from rest_framework.response import Response

import data_exporter.mixins
import importer.mixins
from InvenTree.exceptions import ResourceLocked
from InvenTree.fields import OutputConfiguration
from InvenTree.helpers import remove_non_printable_characters, strip_html_tags
from InvenTree.helpers_model import RowLockTimeoutError, lock_row
from InvenTree.schema import schema_for_view_output_options
from InvenTree.serializers import FilterableSerializerMixin


class CleanCreate:  # noqa: D101
    def create(self, request, *args, **kwargs):  # noqa: D102
        # Override to clean data before processing it
        serializer = self.get_serializer(data=self.clean_data(request.data))
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )


class CleanUpdate:
    """Mixin which cleans the provided data before updating an object.

    The update is performed within a single database transaction, with the target row
    locked *before* it is read. Without this, the object is validated and saved using a
    snapshot which may be stale by the time it is written - silently reverting any change
    committed in the meantime (e.g. by a background task, or another request).

    If the row is locked by another (long-running) transaction, the request is rejected
    with a 409 (see InvenTree.exceptions.ResourceLocked) rather than blocking.
    """

    # Set to False to skip row locking for a particular view
    lock_on_update: bool = True

    def update(self, request, *args, **kwargs):  # noqa: D102
        # Override to clean data before processing it
        partial = kwargs.pop('partial', False)

        with transaction.atomic():
            instance = self.get_object_for_update()
            serializer = self.get_serializer(
                instance, data=self.clean_data(request.data), partial=partial
            )
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

    def get_object_for_update(self):
        """Return the object to be updated, with its database row locked.

        Must be called from within a database transaction.

        Raises:
            ResourceLocked: If the row is locked by another transaction
        """
        if not self.lock_on_update or not connection.features.has_select_for_update:
            return self.get_object()

        # Preferably, lock the row *before* reading the object.
        # This is possible if the primary key is provided directly by the URL
        locked = None
        target = self._get_lock_target()

        if target is not None:
            locked = target
            self._lock_row(*target)

        instance = self.get_object()

        if not isinstance(instance, models.Model) or instance.pk is None:
            return instance

        if locked == (type(instance), instance.pk):
            return instance

        # The object was resolved some other way (e.g. a custom lookup):
        # lock its row now, and then read it again as it may have changed
        self._lock_row(type(instance), instance.pk)

        return self.get_object()

    def _get_lock_target(self):
        """Return the (model, pk) which the URL of this request refers to, if known."""
        if self.lookup_field != 'pk':
            return None

        value = self.kwargs.get(self.lookup_url_kwarg or self.lookup_field)

        try:
            model = self.get_queryset().model
            return (model, model._meta.pk.to_python(value))
        except (AssertionError, AttributeError, DjangoValidationError):
            return None

    def _lock_row(self, model, pk) -> None:
        """Lock the specified database row, or raise ResourceLocked."""
        try:
            lock_row(model, pk)
        except RowLockTimeoutError:
            raise ResourceLocked()


class CleanBase:
    """Model mixin class which cleans inputs using nh3."""

    # Define a list of field names which will *not* be cleaned
    SAFE_FIELDS = []

    def clean_string(self, field: str, data: str) -> str:
        """Clean / sanitize a single input string."""
        cleaned = data

        cleaned = remove_non_printable_characters(cleaned, remove_newline=True)

        cleaned = strip_html_tags(cleaned, field_name=field)

        return cleaned

    def clean_data(self, data: dict) -> dict:
        """Clean / sanitize data.

        This uses nh3 under the hood to disable certain html tags by
        encoding them - this leads to script tags etc. to not work.
        The results can be longer then the input; might make some character combinations
        `ugly`. Prevents XSS on the server-level.

        Args:
            data (dict): Data that should be Sanitized.

        Returns:
            dict: Provided data Sanitized; still in the same order.
        """
        clean_data = {}

        for k, v in data.items():
            if k in self.SAFE_FIELDS:
                ret = v
            elif isinstance(v, str):
                ret = self.clean_string(k, v)
            elif isinstance(v, dict):
                ret = self.clean_data(v)
            else:
                ret = v

            clean_data[k] = ret

        return clean_data


class CleanMixin(CleanCreate, CleanUpdate, CleanBase):
    """Model mixin class which cleans inputs using nh3."""


class CleanUpdateOnlyMixin(CleanUpdate, CleanBase):
    """Model mixin class which cleans inputs using nh3."""


class ListAPI(generics.ListAPIView):
    """View for list API."""


class ListCreateAPI(CleanMixin, generics.ListCreateAPIView):
    """View for list and create API."""


class CreateAPI(CleanMixin, generics.CreateAPIView):
    """View for create API."""


class RetrieveAPI(generics.RetrieveAPIView):
    """View for retrieve API."""


class RetrieveUpdateAPI(CleanMixin, generics.RetrieveUpdateAPIView):
    """View for retrieve and update API."""


class CustomDestroyModelMixin:
    """This mixin was created pass the kwargs from the API to the models."""

    def destroy(self, request, *args, **kwargs):
        """Custom destroy method to pass kwargs."""
        instance = self.get_object()
        self.perform_destroy(instance, **kwargs)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance, **kwargs):
        """Custom destroy method to pass kwargs."""
        instance.delete(**kwargs)


class CustomRetrieveUpdateDestroyAPIView(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    CustomDestroyModelMixin,
    generics.GenericAPIView,
):
    """This APIView was created pass the kwargs from the API to the models."""

    def get(self, request, *args, **kwargs):
        """Custom get method to pass kwargs."""
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        """Custom put method to pass kwargs."""
        return self.update(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        """Custom patch method to pass kwargs."""
        return self.partial_update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        """Custom delete method to pass kwargs."""
        return self.destroy(request, *args, **kwargs)


class CustomRetrieveUpdateDestroyAPI(CleanMixin, CustomRetrieveUpdateDestroyAPIView):
    """This APIView was created pass the kwargs from the API to the models."""


class RetrieveUpdateDestroyAPI(CleanMixin, generics.RetrieveUpdateDestroyAPIView):
    """View for retrieve, update and destroy API."""


class RetrieveDestroyAPI(generics.RetrieveDestroyAPIView):
    """View for retrieve and destroy API."""


class UpdateAPI(CleanMixin, generics.UpdateAPIView):
    """View for update API."""


class DataImportExportSerializerMixin(
    data_exporter.mixins.DataExportSerializerMixin,
    importer.mixins.DataImportSerializerMixin,
):
    """Mixin class for adding data import/export functionality to a DRF serializer."""


class OutputOptionsMixin:
    """Mixin to handle output options for API endpoints."""

    output_options: OutputConfiguration = None

    def __init_subclass__(cls, **kwargs):
        """Automatically attaches OpenAPI schema parameters for its output options."""
        super().__init_subclass__(**kwargs)

        if getattr(cls, 'output_options', None) is not None:
            schema_for_view_output_options(cls)

    def get_serializer(self, *args, **kwargs):
        """Return serializer instance with output options applied."""
        request = getattr(self, 'request', None)
        serializer_class = self.get_serializer_class()

        # Only inject output-option flags into serializers that know how to consume them.
        # Action-specific serializers (e.g. transition endpoints) may not accept these kwargs.
        if (
            self.output_options
            and request
            and issubclass(serializer_class, FilterableSerializerMixin)
        ):
            params = self.request.query_params
            kwargs.update(self.output_options.format_params(params))

        # Ensure the request is included in the serializer context
        context = kwargs.get('context', {})
        context['request'] = request
        kwargs['context'] = context

        return super().get_serializer(*args, **kwargs)

    def get_queryset(self):
        """Return the queryset with output options applied.

        This automatically applies any prefetching defined against the optional fields.
        """
        queryset = super().get_queryset()
        serializer = self.get_serializer()

        if isinstance(serializer, FilterableSerializerMixin):
            queryset = serializer.prefetch_queryset(queryset)

        return queryset


class SerializerContextMixin:
    """Mixin to add context to serializer."""

    def get_serializer(self, *args, **kwargs):
        """Add context to serializer."""
        kwargs['context'] = self.get_serializer_context()
        return super().get_serializer(*args, **kwargs)
