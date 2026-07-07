"""Common functions for handling media files in InvenTree."""

from pathlib import Path
from typing import Optional

from django.core.exceptions import ValidationError


def common_file_upload_handler(
    filename: str,
    file_type: str,
    model_type: Optional[str] = None,
    model_id: Optional[int] = None,
) -> str:
    """A centralized function for handling file uploads in InvenTree.

    All uploaded files will be stored in a consistent directory structure,
    which allows for repeatable and predictable file storage.

    Additionally, with a consistent file storage structure,
    it is possible to implement a permissions system for accessing uploaded files.

    Arguments:
        filename: The name of the uploaded file.
        file_type: The type of the file (e.g., 'attachment', 'test_result').
        model_type: The type of the model associated with the file (optional).
        model_id: The ID of the model associated with the file (optional).
    """
    filename = str(filename).strip()

    if not filename:
        raise ValidationError('Filename cannot be empty.')

    if not file_type:
        raise ValidationError('File type must be specified.')

    # First, remove any illegal characters from the filename
    illegal_chars = '\'"\\`~#|!@#$%^&*()[]{}<>?;:+=,'

    for c in illegal_chars:
        filename = filename.replace(c, '')

    # Convert to a Path, ensure the filename is not attempting to traverse directories
    file_path = Path(filename)

    if (
        file_path.is_absolute()
        or file_path.parts.count() > 1
        or '..' in file_path.parts
    ):
        raise ValidationError('Invalid filename: cannot contain directory traversal.')

    # Construct an upload path based on the provided parts
    parts = []

    # If provided, include the file type in the path
    if model_type:
        parts.append(str(model_type))

    # If provided, include the model ID in the path
    if model_id:
        parts.append(str(model_id))

    # Include the file type in the path
    parts.append(str(file_type))

    # Finally, include the sanitized filename
    parts.append(file_path.name)

    # Join all parts to form the final upload path
    return str(Path(*parts))
