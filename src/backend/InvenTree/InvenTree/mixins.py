"""Mixins for (API) views in the whole project."""

from django.core.exceptions import FieldDoesNotExist

from rest_framework import generics, mixins, status
from rest_framework.response import Response

import data_exporter.mixins
import data_exporter.serializers
import importer.mixins
from InvenTree.fields import InvenTreeNotesField, OutputConfiguration
from InvenTree.helpers import (
    clean_markdown,
    remove_non_printable_characters,
    strip_html_tags,
)
from InvenTree.schema import schema_for_view_output_options
from InvenTree.serializers import FilterableSerializerMixin


class CleanMixin:
    """Model mixin class which cleans inputs using the Mozilla bleach tools."""

    # Define a list of field names which will *not* be cleaned
    SAFE_FIELDS = []

    def create(self, request, *args, **kwargs):
        """Override to clean data before processing it."""
        serializer = self.get_serializer(data=self.clean_data(request.data))
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def update(self, request, *args, **kwargs):
        """Override to clean data before processing it."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
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

    def clean_string(self, field: str, data: str) -> str:
        """Clean / sanitize a single input string.

        Note that this function will *allow* orphaned <>& characters,
        which would normally be escaped by bleach.

        Nominally, the only thing that will be "cleaned" will be HTML tags

        Ref: https://github.com/mozilla/bleach/issues/192

        """
        cleaned = data

        # By default, newline characters are removed
        remove_newline = True
        is_markdown = False

        try:
            if hasattr(self, 'serializer_class'):
                model = self.serializer_class.Meta.model
                field_base = model._meta.get_field(field)

                # The following field types allow newline characters
                allow_newline = [(InvenTreeNotesField, True)]

                for field_type in allow_newline:
                    if issubclass(type(field_base), field_type[0]):
                        remove_newline = False
                        is_markdown = field_type[1]
                        break

        except AttributeError:
            pass
        except FieldDoesNotExist:
            pass

        cleaned = remove_non_printable_characters(
            cleaned, remove_newline=remove_newline
        )

        cleaned = strip_html_tags(cleaned, field_name=field)

        if is_markdown:
            cleaned = clean_markdown(cleaned)

        return cleaned

    def clean_data(self, data: dict) -> dict:
        """Clean / sanitize data.

        This uses Mozilla's bleach under the hood to disable certain html tags by
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

    def __init__(self) -> None:
        """Initialize the mixin. Check that the serializer is compatible."""
        super().__init__()

        # Check that the serializer was defined
        if (
            hasattr(self, 'serializer_class')
            and isinstance(self.serializer_class, type)
            and (not issubclass(self.serializer_class, FilterableSerializerMixin))
        ):
            raise Exception(
                'INVE-I2: `OutputOptionsMixin` can only be used with serializers that contain the `FilterableSerializerMixin` mixin'
            )

    def get_serializer(self, *args, **kwargs):
        """Return serializer instance with output options applied."""
        request = getattr(self, 'request', None)

        if self.output_options and request:
            params = self.request.query_params
            kwargs.update(self.output_options.format_params(params))

        # Ensure the request is included in the serializer context
        context = kwargs.get('context', {})
        context['request'] = request
        kwargs['context'] = context

        serializer = super().get_serializer(*args, **kwargs)

        # Check if the serializer actually can be filtered - makes not much sense to use this mixin without that prerequisite
        if isinstance(
            serializer, data_exporter.serializers.DataExportOptionsSerializer
        ):
            # Skip in this instance, special case for determining export options
            pass
        elif not isinstance(serializer, FilterableSerializerMixin):
            raise Exception(
                'INVE-I2: `OutputOptionsMixin` can only be used with serializers that contain the `FilterableSerializerMixin` mixin'
            )

        return serializer

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
