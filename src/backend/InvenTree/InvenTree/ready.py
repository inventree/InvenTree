"""Functions to check if certain parts of InvenTree are ready."""

import os
import sys


def isInTestMode():
    """Returns True if the database is in testing mode."""
    return 'test' in sys.argv


def isImportingData():
    """Returns True if the database is currently importing (or exporting) data, e.g. 'loaddata' command is performed."""
    return any(x in sys.argv for x in ['flush', 'loaddata', 'dumpdata'])


def isRunningMigrations():
    """Return True if the database is currently running migrations."""
    return any(
        x in sys.argv
        for x in ['migrate', 'makemigrations', 'showmigrations', 'runmigrations']
    )


def isRebuildingData():
    """Return true if any of the rebuilding commands are being executed."""
    return any(
        x in sys.argv for x in ['rebuild_models', 'rebuild_thumbnails', 'rebuild']
    )


def isRunningBackup():
    """Return true if any of the backup commands are being executed."""
    return any(
        x in sys.argv
        for x in [
            'backup',
            'restore',
            'dbbackup',
            'dbresotore',
            'mediabackup',
            'mediarestore',
        ]
    )


def isInWorkerThread():
    """Returns True if the current thread is a background worker thread."""
    return 'qcluster' in sys.argv


def isInServerThread():
    """Returns True if the current thread is a server thread."""
    if isInWorkerThread():
        return False

    if 'runserver' in sys.argv:
        return True

    return 'gunicorn' in sys.argv[0]


def isInMainThread():
    """Django runserver starts two processes, one for the actual dev server and the other to reload the application.

    - The RUN_MAIN env is set in that case. However if --noreload is applied, this variable
    is not set because there are no different threads.
    """
    if 'runserver' in sys.argv and '--noreload' not in sys.argv:
        return os.environ.get('RUN_MAIN', None) == 'true'

    return not isInWorkerThread()


def canAppAccessDatabase(
    allow_test: bool = False, allow_plugins: bool = False, allow_shell: bool = False
):
    """Returns True if the apps.py file can access database records.

    There are some circumstances where we don't want the ready function in apps.py
    to touch the database
    """
    # Prevent database access if we are running backups
    if isRunningBackup():
        return False

    # Prevent database access if we are importing data
    if isImportingData():
        return False

    # Prevent database access if we are rebuilding data
    if isRebuildingData():
        return False

    # Prevent database access if we are running migrations
    if not allow_plugins and isRunningMigrations():
        return False

    # If any of the following management commands are being executed,
    # prevent custom "on load" code from running!
    excluded_commands = [
        'check',
        'createsuperuser',
        'wait_for_db',
        'makemessages',
        'compilemessages',
        'spectactular',
        'collectstatic',
    ]

    if not allow_shell:
        excluded_commands.append('shell')

    if not allow_test:
        # Override for testing mode?
        excluded_commands.append('test')

    if not allow_plugins:
        excluded_commands.extend(['collectplugins'])

    return all(cmd not in sys.argv for cmd in excluded_commands)


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
