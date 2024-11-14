"""Management command to collect plugin static files."""

from django.core.management import BaseCommand


class Command(BaseCommand):
    """Collect static files for all installed plugins."""

    def handle(self, *args, **kwargs):
        """Run the management command."""
        import plugin.staticfiles

        plugin.staticfiles.collect_plugins_static_files()
        plugin.staticfiles.clear_plugins_static_files()
