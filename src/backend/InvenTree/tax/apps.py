"""Tax app configuration."""

from django.apps import AppConfig


class TaxConfig(AppConfig):
    """Tax app configuration."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tax'
    verbose_name = 'Tax Management'
