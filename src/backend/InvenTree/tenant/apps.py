"""Config for the 'tenant' app."""

from django.apps import AppConfig


class TenantConfig(AppConfig):
    """Config class for the 'tenant' app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tenant'
    verbose_name = 'Tenant Management'

    def ready(self):
        """This function is called whenever the Tenant app is loaded."""
