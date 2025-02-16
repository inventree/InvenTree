"""Config options for the exporter app."""

from django.apps import AppConfig


class ExporterConfig(AppConfig):
    """Configuration class for the 'exporter' app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'exporter'

    def ready(self):
        """Run any code that needs to be executed when the app is loaded."""
        super().ready()

        self.cleanup()

    def cleanup(self):
        """Cleanup any old export files."""
        try:
            from exporter.tasks import cleanup_old_export_outputs

            cleanup_old_export_outputs()
        except Exception:
            pass
