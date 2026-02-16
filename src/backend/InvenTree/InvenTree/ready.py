"""Functions to check if certain parts of InvenTree are ready."""

import functools
import inspect
import os
import sys
import warnings

from django.conf import settings

import structlog

logger = structlog.get_logger('inventree')


# Keep track of loaded apps, to prevent multiple executions of ready functions
_loaded_apps = set()


def clearLoadedApps():
    """Clear the set of loaded apps."""
    global _loaded_apps
    _loaded_apps = set()


def setAppLoaded(app_name: str):
    """Mark an app as loaded."""
    global _loaded_apps
    _loaded_apps.add(app_name)


def isAppLoaded(app_name: str) -> bool:
    """Return True if the app has been marked as loaded."""
    global _loaded_apps
    return app_name in _loaded_apps


def isInTestMode():
    """Returns True if the database is in testing mode."""
    return 'test' in sys.argv or sys.argv[0].endswith('pytest')


def isWaitingForDatabase():
    """Return True if we are currently waiting for the database to be ready."""
    return 'wait_for_db' in sys.argv


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
        x in sys.argv
        for x in [
            'rebuild',
            'rebuild_models',
            'rebuild_thumbnails',
            'remove_stale_contenttypes',
        ]
    )


def isRunningBackup():
    """Return true if any of the backup commands are being executed."""
    return any(
        x in sys.argv
        for x in [
            'backup',
            'restore',
            'dbbackup',
            'dbrestore',
            'mediabackup',
            'mediarestore',
        ]
    )


def isGeneratingSchema():
    """Return true if schema generation is being executed."""
    if isInServerThread() or isInWorkerThread():
        return False

    if isRunningMigrations() or isRunningBackup() or isRebuildingData():
        return False

    if isImportingData():
        return False

    if isInTestMode():
        return False

    if isWaitingForDatabase():
        return False

    if 'schema' in sys.argv:
        return True

    # This is a very inefficient call - so we only use it as a last resort
    result = any('drf_spectacular' in frame.filename for frame in inspect.stack())

    if not result:
        # We should only get here if we *are* generating schema
        # Any other time this is called, it should be from a server thread, worker thread, or test mode

        if settings.DEBUG:
            logger.warning(
                'isGeneratingSchema called outside of expected contexts - this may be a sign of a problem with the ready() function'
            )
            logger.warning('sys.argv: %s', sys.argv)

    return result


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


def ignore_ready_warning(func):
    """Decorator to ignore 'AppRegistryNotReady' warnings in functions called during app ready phase.

    Ref: https://github.com/inventree/InvenTree/issues/10806
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        with warnings.catch_warnings():
            warnings.filterwarnings(
                'ignore',
                message='Accessing the database during app initialization is discouraged',
                category=RuntimeWarning,
            )
            return func(*args, **kwargs)

    return wrapper
