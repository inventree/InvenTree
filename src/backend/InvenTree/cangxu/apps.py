"""Django application configuration for Cangxu manufacturing extensions."""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CangxuConfig(AppConfig):
    """Register Cangxu's manufacturing and service traceability models."""

    default_auto_field = 'django.db.models.AutoField'
    name = 'cangxu'
    verbose_name = _('Cangxu manufacturing')

    def ready(self):
        """Register transactional business changes for the persistent partner."""
        from .assistant_events import register_receipt_events

        register_receipt_events()

        from django.db.models.signals import post_migrate

        from .assistant_tasks import ensure_schedules

        post_migrate.connect(
            ensure_schedules,
            sender=self,
            weak=False,
            dispatch_uid='cangxu.assistant.schedule',
        )
