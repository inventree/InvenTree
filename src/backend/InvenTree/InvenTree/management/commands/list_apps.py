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

        group = parser.add_mutually_exclusive_group()
        group.add_argument(
            '--plugins-only',
            action='store_true',
            help='Only list apps which are provided by plugins',
        )
        group.add_argument(
            '--exclude-plugins',
            action='store_true',
            help='Do not list apps which are provided by plugins',
        )

    def handle(self, *args, **kwargs):
        """List all installed apps.

        Note that this function outputs in a particular format,
        which is expected by the calling code in tasks.py
        """
        from django.apps import apps

        from plugin import registry

        labels = kwargs.get('labels', False)
        plugins_only = kwargs.get('plugins_only', False)
        exclude_plugins = kwargs.get('exclude_plugins', False)

        # Apps which have been added to INSTALLED_APPS by AppMixin plugins
        plugin_apps = set(registry.installed_apps)

        app_list = []

        for app in apps.get_app_configs():
            is_plugin = app.name in plugin_apps

            if (plugins_only and not is_plugin) or (exclude_plugins and is_plugin):
                continue

            app_list.append(app.label if labels else app.name)

        app_list.sort()

        self.stdout.write(f'Installed Apps: {len(app_list)}')
        self.stdout.write('>>> ' + ','.join(app_list) + ' <<<')
