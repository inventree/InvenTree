"""Data import operational functions."""

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

import tablib


def load_data_file(data_file, format=None):
    """Load data file into a tablib dataset.

    Arguments:
        data_file: django file object containing data to import (should be already opened!)
        format: Format specifier for the data file
    """
    # Introspect the file format based on the provided file
    if not format:
        format = data_file.name.split('.')[-1]

    if format and format.startswith('.'):
        format = format[1:]

    file_object = data_file.file
    file_object.open('r')
    file_object.seek(0)

    try:
        data = file_object.read()
    except (IOError, FileNotFoundError):
        raise ValidationError(_('Failed to open data file'))

    if format not in ['xls', 'xlsx']:
        data = data.decode()

    try:
        data = tablib.Dataset().load(data, headers=True, format=format)
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
    return data.headers


def extract_rows(data_file) -> list:
    """Extract rows from the data file.

    Each returned row is a dictionary of column_name: value pairs.
    """
    data = load_data_file(data_file)

    rows = []

    for row in data:
        rows.append(row)

    return rows


def get_fields(serializer_class, read_only=None, required=None):
    """Extract the field names from a serializer class.

    - Returns a dict of (writeable) field names.
    - Read-Only fields are explicitly ignored
    """
    if not serializer_class:
        return {}

    serializer = serializer_class()

    fields = {}

    for field_name, field in serializer.fields.items():
        if read_only is not None and getattr(field, 'read_only', None) != read_only:
            continue

        if required is not None and getattr(field, 'required', None) != required:
            continue

        fields[field_name] = field

    return fields
