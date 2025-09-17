"""Config options for the exporter app."""

from django.apps import AppConfig


class DataExporterConfig(AppConfig):
    """Configuration class for the 'exporter' app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'data_exporter'

    def ready(self):
        """Run any code that needs to be executed when the app is loaded."""
        super().ready()

        self.cleanup()

    def cleanup(self):
        """Cleanup any old export files."""
        try:
            from data_exporter.tasks import cleanup_old_export_outputs  # type: ignore

            cleanup_old_export_outputs()
        except Exception:
            pass
