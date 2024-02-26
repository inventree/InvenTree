"""Helpers for file handling in InvenTree."""

from pathlib import Path

from django.conf import settings
from django.core.files.storage import get_storage_class

TEMPLATES_DIR = Path(__file__).parent.parent
MEDIA_STORAGE_DIR = Path(settings.MEDIA_ROOT)
static_storage = get_storage_class(settings.STATICFILES_STORAGE)()
default_storage = get_storage_class(settings.DEFAULT_FILE_STORAGE)()
