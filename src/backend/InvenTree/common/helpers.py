"""Various helper functions for the part app."""

import os

from django.conf import settings

# Subdirectory for storing part images
UPLOAD_IMAGE_DIR = 'upload_images'


def get_part_image_directory() -> str:
    """Return the directory where part images are stored.

    Returns:
        str: Directory where part images are stored

    TODO: Future work may be needed here to support other storage backends, such as S3
    """
    part_image_directory = os.path.abspath(
        os.path.join(settings.MEDIA_ROOT, UPLOAD_IMAGE_DIR)
    )

    # Create the directory if it does not exist
    if not os.path.exists(part_image_directory):
        os.makedirs(part_image_directory)

    return part_image_directory
