"""Task definitions for the 'importer' app."""

import logging

from django.db import transaction

logger = logging.getLogger('inventree')


@transaction.atomic
def load_data(session_id: int):
    """Load data from the provided file.

    Attempt to load data from the provided file, and potentially handle any errors.
    """
    import importer.models
    import importer.operations
    import importer.status_codes

    try:
        session = importer.models.DataImportSession.objects.get(pk=session_id)
        logger.info("Loading data from session ID '%s'", session_id)
    except (ValueError, importer.models.DataImportSession.DoesNotExist):
        logger.error("Data import session with ID '%s' does not exist", session_id)
        return

    # Clear any existing data rows
    session.rows.all().delete()

    df = importer.operations.load_data_file(session.data_file)

    if df is None:
        # TODO: Log an error message against the import session
        logger.error('Failed to load data file')
        return

    headers = df.headers

    # TODO: Mark the session as "importing"
    # session.status = importer.status_codes.DataImportStatusCode.IMPORTING.value
    # session.save()

    row_objects = []

    # Iterate through each "row" in the data file, and create a new DataImportRow object
    for idx, row in enumerate(df):
        row_data = dict(zip(headers, row))

        row_objects.append(
            importer.models.DataImportRow(
                session=session, row_data=row_data, row_index=idx
            )
        )

    # Finally, create the DataImportRow objects
    importer.models.DataImportRow.objects.bulk_create(row_objects)

    # TODO: Mark the import task as "completed"
