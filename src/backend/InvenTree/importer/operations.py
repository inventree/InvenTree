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
    except (IOError, FileNotFoundError):
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
    return data.headers


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


def get_fields(
    serializer_class,
    write_only=None,
    read_only=None,
    required=None,
    exporting=False,
    importing=True,
):
    """Extract the field names from a serializer class.

    Arguments:
        serializer_class: Serializer
        write_only: Filter fields based on write_only attribute
        read_only: Filter fields based on read_only attribute
        required: Filter fields based on required attribute
    """
    if not serializer_class:
        return {}

    serializer = serializer_class(exporting=exporting, importing=importing)

    fields = {}

    for field_name, field in serializer.fields.items():
        if read_only is not None and getattr(field, 'read_only', None) != read_only:
            continue

        if write_only is not None and getattr(field, 'write_only', None) != write_only:
            continue

        if required is not None and getattr(field, 'required', None) != required:
            continue

        fields[field_name] = field

    return fields


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
    if field:
        if label := getattr(field, 'label', None):
            return label

    # TODO: Check if the field is a model field

    return None
