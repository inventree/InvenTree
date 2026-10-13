"""Django application configuration for Cangxu manufacturing extensions."""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CangxuConfig(AppConfig):
    """Register Cangxu's manufacturing and service traceability models."""

    default_auto_field = 'django.db.models.AutoField'
    name = 'cangxu'
    verbose_name = _('Cangxu manufacturing')
