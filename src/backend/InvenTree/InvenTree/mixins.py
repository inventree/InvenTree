"""Mixins for (API) views in the whole project."""

from django.core.exceptions import FieldDoesNotExist

from rest_framework import generics, mixins, status
from rest_framework.response import Response

from InvenTree.fields import InvenTreeNotesField
from InvenTree.helpers import (
    DownloadFile,
    GetExportFormats,
    current_date,
    remove_non_printable_characters,
    strip_html_tags,
)


class DataExportMixin:
    """Mixin class for exporting a dataset via the API.

    Adding this mixin to an API view allows the user to export the dataset to file in a variety of formats.

    We achieve this by overriding the 'get' method, and checking for the presence of the required query parameter.
    """

    EXPORT_QUERY_PARAMETER = 'export2'

    def get_exported_filename(self, serializer, export_format):
        """Return the filename for the exported data file.

        An implementing class can override this implementation if required.
        """
        model = serializer.Meta.model
        date = current_date().isoformat()

        return f'InvenTree_{model.__name__}_{date}.{export_format}'

    def export_data(self, request, export_format):
        """Export the data in the specified format.

        Use the provided serializer to generate the data, and return it as a file download.
        """
        from importer.operations import export_data_to_file

        serializer = self.get_serializer_class()
        queryset = self.filter_queryset(self.get_queryset())

        filename = self.get_exported_filename(serializer, export_format)

        data_file = export_data_to_file(serializer, queryset, export_format)

        return DownloadFile(data_file, filename=filename)

    def get(self, request, *args, **kwargs):
        """Override the 'get' method to check for the export query parameter."""
        print('running new export checker!')

        if export_format := request.query_params.get(self.EXPORT_QUERY_PARAMETER, None):
            export_format = str(export_format).strip().lower()
            if export_format in GetExportFormats():
                return self.export_data(request, export_format)

        # If the export query parameter is not present, return the default response
        return super().get(request, *args, **kwargs)


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
        cleaned = strip_html_tags(data, field_name=field)

        # By default, newline characters are removed
        remove_newline = True

        try:
            if hasattr(self, 'serializer_class'):
                model = self.serializer_class.Meta.model
                field = model._meta.get_field(field)

                # The following field types allow newline characters
                allow_newline = [InvenTreeNotesField]

                for field_type in allow_newline:
                    if issubclass(type(field), field_type):
                        remove_newline = False
                        break

        except AttributeError:
            pass
        except FieldDoesNotExist:
            pass

        cleaned = remove_non_printable_characters(
            cleaned, remove_newline=remove_newline
        )

        return cleaned

    def clean_data(self, data: dict) -> dict:
        """Clean / sanitize data.

        This uses mozillas bleach under the hood to disable certain html tags by
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

    pass


class RetrieveUpdateAPI(CleanMixin, generics.RetrieveUpdateAPIView):
    """View for retrieve and update API."""

    pass


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


class UpdateAPI(CleanMixin, generics.UpdateAPIView):
    """View for update API."""
