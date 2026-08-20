"""Custom management command to list all installed apps.

This is used to determine which apps are installed,
including any apps which are defined for plugins.
"""

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """List all installed apps."""

    def handle(self, *args, **kwargs):
        """List all installed apps.

        Note that this function outputs in a particular format,
        which is expected by the calling code in tasks.py
        """
        from django.apps import apps

        app_list = []

        for app in apps.get_app_configs():
            app_list.append(app.name)

        app_list.sort()

        self.stdout.write(f'Installed Apps: {len(app_list)}')
        self.stdout.write('>>> ' + ','.join(app_list) + ' <<<')
