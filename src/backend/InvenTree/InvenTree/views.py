"""Various Views which provide extra functionality over base Django Views."""

from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.utils.translation import gettext_lazy as _

from InvenTree.helpers import DownloadFile, GetExportFormats
from InvenTree.serializers import DataExportSerializerMixin


def auth_request(request):
    """Simple 'auth' endpoint used to determine if the user is authenticated.

    Useful for (for example) redirecting authentication requests through django's permission framework.
    """
    if request.user and request.user.is_authenticated:
        return HttpResponse(status=200)
    return HttpResponse(status=403)


class DataExportViewMixin:
    """Mixin class for exporting a dataset via the API.

    Adding this mixin to an API view allows the user to export the dataset to file in a variety of formats.

    We achieve this by overriding the 'get' method, and checking for the presence of the required query parameter.
    """

    EXPORT_QUERY_PARAMETER = 'export'

    def export_data(self, export_format):
        """Export the data in the specified format.

        Use the provided serializer to generate the data, and return it as a file download.
        """
        serializer_class = self.get_serializer_class()

        if not issubclass(serializer_class, DataExportSerializerMixin):
            raise TypeError(
                'Serializer class must inherit from DataExportSerializerMixin'
            )

        queryset = self.filter_queryset(self.get_queryset())

        serializer = serializer_class(exporting=True)
        serializer.initial_data = queryset

        # Export dataset with a second copy of the serializer
        # This is because when we pass many=True, the returned class is a ListSerializer
        data = serializer_class(queryset, many=True, exporting=True).data

        filename = serializer.get_exported_filename(export_format)
        datafile = serializer.export_to_file(data, export_format)

        return DownloadFile(datafile, filename=filename)

    def get(self, request, *args, **kwargs):
        """Override the 'get' method to check for the export query parameter."""
        if export_format := request.query_params.get(self.EXPORT_QUERY_PARAMETER, None):
            export_format = str(export_format).strip().lower()
            if export_format in GetExportFormats():
                return self.export_data(export_format)
            else:
                raise ValidationError({
                    self.EXPORT_QUERY_PARAMETER: _('Invalid export format')
                })

        # If the export query parameter is not present, return the default response
        return super().get(request, *args, **kwargs)
