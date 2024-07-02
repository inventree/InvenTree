"""Status codes for common model types."""

from django.utils.translation import gettext_lazy as _

from generic.states import StatusCode


class DataImportStatusCode(StatusCode):
    """Defines a set of status codes for a DataImportSession."""

    INITIAL = 0, _('Initializing'), 'secondary'  # Import session has been created
    MAPPING = 10, _('Mapping Columns'), 'primary'  # Import fields are being mapped
    IMPORTING = 20, _('Importing Data'), 'primary'  # Data is being imported
    PROCESSING = (
        30,
        _('Processing Data'),
        'primary',
    )  # Data is being processed by the user
    COMPLETE = 40, _('Complete'), 'success'  # Import has been completed
