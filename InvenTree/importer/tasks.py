"""Task definitions for the 'importer' app."""

import logging

from django.db import transaction

logger = logging.getLogger('inventree')


@transaction.atomic
def import_data(session_id: int):
    """Load data from the provided file.

    Attempt to load data from the provided file, and potentially handle any errors.
    """
    import importer.models
    import importer.operations
    import importer.status_codes

    try:
        session = importer.models.DataImportSession.objects.get(pk=session_id)
        logger.info("Loading data from session ID '%s'", session_id)
        session.import_data()
    except (ValueError, importer.models.DataImportSession.DoesNotExist):
        logger.error("Data import session with ID '%s' does not exist", session_id)
        return
