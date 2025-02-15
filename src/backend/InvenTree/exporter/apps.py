"""Config options for the exporter app."""

from django.apps import AppConfig


class ExporterConfig(AppConfig):
    """Configuration class for the 'exporter' app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'exporter'
