"""Various helper functions for common model."""

import io
from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile

from PIL import Image


def generate_image(filename: str = 'test.png', fmt: str = 'PNG') -> ContentFile:
    """Generate a Django dummy image for test inventreeimage."""
    color = (255, 0, 0)

    img = Image.new(mode='RGB', size=(100, 100), color=color)

    buffer = io.BytesIO()
    img.save(buffer, format=fmt)
    buffer.seek(0)

    return ContentFile(buffer.read(), name=filename)


# Subdirectory for storing part images
UPLOADED_IMAGE_DIR = 'images'


def get_part_image_directory() -> str:
    """Return the directory where part images are stored.

    Returns:
        str: Directory where part images are stored

    TODO: Future work may be needed here to support other storage backends, such as S3
    """
    part_image_directory = (Path(settings.MEDIA_ROOT) / UPLOADED_IMAGE_DIR).resolve()
    part_image_directory.mkdir(parents=True, exist_ok=True)
    return str(part_image_directory)
