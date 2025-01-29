"""Mixins for (API) views in the whole project."""

from django.core.exceptions import FieldDoesNotExist

from rest_framework import generics, mixins, status
from rest_framework.response import Response

from InvenTree.fields import InvenTreeNotesField
from InvenTree.helpers import (
    clean_markdown,
    remove_non_printable_characters,
    strip_html_tags,
)


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
