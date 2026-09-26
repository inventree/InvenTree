"""AppConfig for the 'scim' app."""

from django.apps import AppConfig


class ScimConfig(AppConfig):
    """AppConfig class for the 'scim' app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'scim'
    verbose_name = 'SCIM'
