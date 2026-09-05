"""Status codes for common model types."""

from django.utils.translation import gettext_lazy as _

from generic.states import ColorEnum, StatusCode


class DataImportStatusCode(StatusCode):
    """Defines a set of status codes for a DataImportSession.

    Attributes:
        INITIAL: Import session has been created
        MAPPING: Import fields are being mapped
        IMPORTING: Data is being imported
        PROCESSING: Data is being processed by the user
        COMPLETE: Import has been completed
    """

    INITIAL = 0, _('Initializing'), ColorEnum.secondary
    MAPPING = 10, _('Mapping Columns'), ColorEnum.primary
    IMPORTING = 20, _('Importing Data'), ColorEnum.primary
    PROCESSING = 30, _('Processing Data'), ColorEnum.primary
    COMPLETE = 40, _('Complete'), ColorEnum.success
