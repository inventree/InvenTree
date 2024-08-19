"""Data import operational functions."""

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

import tablib

import InvenTree.helpers


def load_data_file(data_file, file_format=None):
    """Load data file into a tablib dataset.

    Arguments:
        data_file: django file object containing data to import (should be already opened!)
        file_format: Format specifier for the data file
    """
    # Introspect the file format based on the provided file
    if not file_format:
        file_format = data_file.name.split('.')[-1]

    if file_format and file_format.startswith('.'):
        file_format = file_format[1:]

    file_format = file_format.strip().lower()

    if file_format not in InvenTree.helpers.GetExportFormats():
        raise ValidationError(_('Unsupported data file format'))

    file_object = data_file.file

    if hasattr(file_object, 'open'):
        file_object.open('r')

    file_object.seek(0)

    try:
        data = file_object.read()
    except (OSError, FileNotFoundError):
        raise ValidationError(_('Failed to open data file'))

    # Excel formats expect binary data
    if file_format not in ['xls', 'xlsx']:
        data = data.decode()

    try:
        data = tablib.Dataset().load(data, headers=True, format=file_format)
    except tablib.core.UnsupportedFormat:
        raise ValidationError(_('Unsupported data file format'))
    except tablib.core.InvalidDimensions:
        raise ValidationError(_('Invalid data file dimensions'))

    return data


def extract_column_names(data_file) -> list:
    """Extract column names from a data file.

    Uses the tablib library to extract column names from a data file.

    Args:
        data_file: File object containing data to import

    Returns:
        List of column names extracted from the file

    Raises:
        ValidationError: If the data file is not in a valid format
    """
    data = load_data_file(data_file)

    headers = []

    for idx, header in enumerate(data.headers):
        if header:
            headers.append(header)
        else:
            # If the header is empty, generate a default header
            headers.append(f'Column {idx + 1}')

    return headers


def extract_rows(data_file) -> list:
    """Extract rows from the data file.

    Each returned row is a dictionary of column_name: value pairs.
    """
    data = load_data_file(data_file)

    headers = data.headers

    rows = []

    for row in data:
        rows.append(dict(zip(headers, row)))

    return rows


def get_field_label(field) -> str:
    """Return the label for a field in a serializer class.

    Check for labels in the following order of descending priority:

    - The serializer class has a 'label' specified for the field
    - The underlying model has a 'verbose_name' specified
    - The field name is used as the label

    Arguments:
        field: Field instance from a serializer class

    Returns:
        str: Field label
    """
    if field and (label := getattr(field, 'label', None)):
        return label

    # TODO: Check if the field is a model field

    return None
