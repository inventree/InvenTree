"""Functions to check if certain parts of InvenTree are ready."""

import os
import sys


def isInTestMode():
    """Returns True if the database is in testing mode."""
    return 'test' in sys.argv


def isImportingData():
    """Returns True if the database is currently importing data, e.g. 'loaddata' command is performed."""
    return 'loaddata' in sys.argv


def isRunningMigrations():
    """Return True if the database is currently running migrations."""
    return any((x in sys.argv for x in [
        'migrate',
        'makemigrations',
        'showmigrations'
    ]))


def isInMainThread():
    """Django runserver starts two processes, one for the actual dev server and the other to reload the application.

    - The RUN_MAIN env is set in that case. However if --noreload is applied, this variable
    is not set because there are no different threads.
    """
    if "runserver" in sys.argv and "--noreload" not in sys.argv:
        return os.environ.get('RUN_MAIN', None) == "true"

    return True


def canAppAccessDatabase(allow_test: bool = False, allow_plugins: bool = False, allow_shell: bool = False):
    """Returns True if the apps.py file can access database records.

    There are some circumstances where we don't want the ready function in apps.py
    to touch the database
    """
    # If any of the following management commands are being executed,
    # prevent custom "on load" code from running!
    excluded_commands = [
        'flush',
        'loaddata',
        'dumpdata',
        'check',
        'createsuperuser',
        'wait_for_db',
        'prerender',
        'rebuild_models',
        'rebuild_thumbnails',
        'makemessages',
        'compilemessages',
        'backup',
        'dbbackup',
        'mediabackup',
        'restore',
        'dbrestore',
        'mediarestore',
    ]

    if not allow_shell:
        excluded_commands.append('shell')

    if not allow_test:
        # Override for testing mode?
        excluded_commands.append('test')

    if not allow_plugins:
        excluded_commands.extend([
            'makemigrations',
            'showmigrations',
            'migrate',
            'collectstatic',
        ])

    for cmd in excluded_commands:
        if cmd in sys.argv:
            return False

    return True


def isPluginRegistryLoaded():
    """Ensures that the plugin registry is already loaded.

    The plugin registry reloads all apps onetime after starting if there are AppMixin plugins,
    so that the discovered AppConfigs are added to Django. This triggers the ready function of
    AppConfig to execute twice. Add this check to prevent from running two times.

    Note: All apps using this check need to be registered after the plugins app in settings.py

    Returns: 'False' if the registry has not fully loaded the plugins yet.
    """
    from plugin import registry

    return registry.plugins_loaded
