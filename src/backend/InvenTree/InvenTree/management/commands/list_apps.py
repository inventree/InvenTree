"""Custom management command to list all installed apps.

This is used to determine which apps are installed,
including any apps which are defined for plugins.
"""

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """List all installed apps."""

    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            '--labels',
            action='store_true',
            help='Output app labels (e.g. "auth") instead of full app names (e.g. "django.contrib.auth")',
        )

    def handle(self, *args, **kwargs):
        """List all installed apps.

        Note that this function outputs in a particular format,
        which is expected by the calling code in tasks.py
        """
        from django.apps import apps

        labels = kwargs.get('labels', False)

        app_list = []

        for app in apps.get_app_configs():
            app_list.append(app.label if labels else app.name)

        app_list.sort()

        self.stdout.write(f'Installed Apps: {len(app_list)}')
        self.stdout.write('>>> ' + ','.join(app_list) + ' <<<')
