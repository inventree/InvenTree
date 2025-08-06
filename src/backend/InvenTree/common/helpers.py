"""Various helper functions for common model."""

from pathlib import Path

from django.conf import settings

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
