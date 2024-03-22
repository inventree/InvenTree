"""Status codes for common model types."""

from django.utils.translation import gettext_lazy as _

from generic.states import StatusCode


class DataImportStatusCode(StatusCode):
    """Defines a set of status codes for a DataImportSession."""

    INITIAL = 0, _('Initial'), 'secondary'  # Import session has been created
    MAPPED_FIELDS = (
        10,
        _('Mapped Fields'),
        'primary',
    )  # Import fields have been mapped successfully
    IMPORTING = 20, _('Importing'), 'primary'  # Data is being imported
    COMPLETE = 30, _('Complete'), 'success'  # Import has been completed
