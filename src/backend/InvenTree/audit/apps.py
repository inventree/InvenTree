"""AppConfig for the 'audit' app."""

from django.apps import AppConfig


class AuditConfig(AppConfig):
    """AppConfig class for the 'audit' app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'audit'

    def ready(self):
        """Register audited models with django-auditlog.

        Registration only connects model signals (no database access),
        and must run in every process which can save models (server, worker, shell).
        """
        import audit.signals  # noqa: F401 - connect signal receivers
        from audit.registry import register_audited_models

        register_audited_models()
