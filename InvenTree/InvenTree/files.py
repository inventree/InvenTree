"""Helpers for file handling in InvenTree."""

from pathlib import Path

from django.conf import settings

TEMPLATES_DIR = Path(__file__).parent.parent.joinpath('templates')
MEDIA_STORAGE_DIR = settings.MEDIA_ROOT
