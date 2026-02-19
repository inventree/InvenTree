"""Various helper functions for common model."""

import io

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


# Subdirectory for storing images
UPLOADED_IMAGE_DIR = 'images'
