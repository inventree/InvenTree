"""Status codes for common model types."""

from django.utils.translation import gettext_lazy as _

from generic.states import ColorEnum, StatusCode


class DataImportStatusCode(StatusCode):
    """Defines a set of status codes for a DataImportSession."""

    INITIAL = (
        0,
        _('Initializing'),
        ColorEnum.secondary,
    )  # Import session has been created
    MAPPING = (
        10,
        _('Mapping Columns'),
        ColorEnum.primary,
    )  # Import fields are being mapped
    IMPORTING = 20, _('Importing Data'), ColorEnum.primary  # Data is being imported
    PROCESSING = (
        30,
        _('Processing Data'),
        ColorEnum.primary,
    )  # Data is being processed by the user
    COMPLETE = 40, _('Complete'), ColorEnum.success  # Import has been completed
