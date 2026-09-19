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


# Cached introspection of the command line arguments
ARGV_COMMANDS: dict[str, tuple[str, ...]] = {
    # Running in test mode
    'test': ('test', 'pytest'),
    # The 'test' management command - not pytest
    'test_command': ('test',),
    # Collecting the available plugins
    'collect_plugins': ('collectplugins',),
    # Listing the installed apps
    'list_apps': ('list_apps',),
    # Running an interactive shell session
    'shell': ('shell',),
    # Running as a background worker
    'worker': ('qcluster',),
    # Running the django development server
    'runserver': ('runserver',),
    # Waiting for the database to become available
    'wait_for_db': ('wait_for_db',),
    # #### #
    # More complex groups
    # #### #
    # Importing (or exporting) database records
    'import_data': ('flush', 'loaddata', 'bulkloaddata', 'dumpdata'),
    # Running database migrations
    'migrations': ('migrate', 'makemigrations', 'showmigrations', 'runmigrations'),
    # Rebuilding database records
    'rebuild_data': (
        'rebuild',
        'rebuild_models',
        'rebuild_thumbnails',
        'remove_stale_contenttypes',
    ),
    # Running a backup / restore operation
    'backup': (
        'backup',
        'restore',
        'dbbackup',
        'dbrestore',
        'mediabackup',
        'mediarestore',
    ),
    # Read-only commands, which should not trigger any database writes
    'read_only': (
        'help',
        'check',
        'shell',
        'sqlflush',
        'list_apps',
        'wait_for_db',
        'spectactular',
        'makemessages',
        'collectstatic',
        'showmigrations',
        'compilemessages',
    ),
    # Commands which should *not* trigger schema generation
    'schema_excluded': (
        'compilemessages',
        'createsuperuser',
        'clean_settings',
        'collectstatic',
        'makemessages',
        'wait_for_db',
        'list_apps',
        'gunicorn',
        'sqlflush',
        'qcluster',
        'check',
        'shell',
        'help',
    ),
    # Commands which *do* trigger schema generation
    'schema_generation': (
        'schema',
        'spectactular',
        # schema adjacent calls
        'export_settings_definitions',
        'export_tags',
        'export_filters',
        'export_report_context',
    ),
    # Commands which must not touch the database during the app 'ready' phase
    'database_excluded': (
        'compilemessages',
        'createsuperuser',
        'collectstatic',
        'makemessages',
        'spectactular',
        'wait_for_db',
        'check',
    ),
}


def _introspectCommands(argv: list[str]):
    """Introspect the provided command line arguments."""
    args = set(argv)
    entrypoint = argv[0] if argv else ''

    _context = {
        key: not args.isdisjoint(commands) for key, commands in ARGV_COMMANDS.items()
    }

    # The entrypoint itself can indicate the context
    _context['pytest_entrypoint'] = entrypoint.endswith('pytest')
    _context['gunicorn_entrypoint'] = 'gunicorn' in entrypoint

    # The development server is running without the auto-reloader
    _context['noreload'] = '--noreload' in args

    return _context


cmd_context = _introspectCommands(sys.argv)


def isInTestMode():
    """Returns True if the database is in testing mode."""
    return cmd_context['test'] or cmd_context['pytest_entrypoint']


def isWaitingForDatabase():
    """Return True if we are currently waiting for the database to be ready."""
    return cmd_context['wait_for_db']


def isImportingData():
    """Returns True if the database is currently importing (or exporting) data, e.g. 'loaddata' command is performed."""
    return cmd_context['import_data']


def isRunningMigrations():
    """Return True if the database is currently running migrations."""
    return cmd_context['migrations']


def isRebuildingData():
    """Return true if any of the rebuilding commands are being executed."""
    return cmd_context['rebuild_data']


def isRunningBackup():
    """Return true if any of the backup commands are being executed."""
    return cmd_context['backup']


def isCollectingPlugins():
    """Return True if the 'collectplugins' command is being executed."""
    return cmd_context['collect_plugins']


# This variable is used to cache the result of the isGeneratingSchema function, to prevent multiple executions of the same checks
_IS_GENERATING_SCHEMA: bool | None = None


def _setGeneratingSchema(value: bool):
    """Set the value of the isGeneratingSchema variable."""
    global _IS_GENERATING_SCHEMA
    _IS_GENERATING_SCHEMA = value
    return value


def isGeneratingSchema():
    """Return true if schema generation is being executed."""
    global _IS_GENERATING_SCHEMA

    if _IS_GENERATING_SCHEMA is not None:
        return _IS_GENERATING_SCHEMA

    if isInServerThread() or isInWorkerThread():
        return _setGeneratingSchema(False)

    if isRunningMigrations() or isRunningBackup() or isRebuildingData():
        return _setGeneratingSchema(False)

    if isImportingData():
        return _setGeneratingSchema(False)

    if isInTestMode():
        return _setGeneratingSchema(False)

    if isWaitingForDatabase():
        return _setGeneratingSchema(False)

    if isCollectingPlugins():
        return _setGeneratingSchema(False)

    # Additional set of commands which should not trigger schema generation
    if cmd_context['schema_excluded']:
        return _setGeneratingSchema(False)

    if cmd_context['schema_generation']:
        return _setGeneratingSchema(True)

    # This is a very inefficient call - so we only use it as a last resort
    result = any('drf_spectacular' in frame.filename for frame in inspect.stack())

    if not result:
        # We should only get here if we *are* generating schema
        # Raise a warning, so that developers can add extra checks above

        if settings.DEBUG:
            logger.warning(
                'isGeneratingSchema called outside of expected contexts - this may be a sign of a problem with the ready() function'
            )
            logger.warning('sys.argv: %s', sys.argv)

    return _setGeneratingSchema(result)


def isInWorkerThread():
    """Returns True if the current thread is a background worker thread."""
    return cmd_context['worker']


def isInServerThread():
    """Returns True if the current thread is a server thread."""
    if isInWorkerThread():
        return False

    if cmd_context['runserver']:
        return True

    return cmd_context['gunicorn_entrypoint']


def isInMainThread():
    """Django runserver starts two processes, one for the actual dev server and the other to reload the application.

    - The RUN_MAIN env is set in that case. However if --noreload is applied, this variable
    is not set because there are no different threads.
    """
    if cmd_context['runserver'] and not cmd_context['noreload']:
        return os.environ.get('RUN_MAIN', None) == 'true'

    return not isInWorkerThread()


def isReadOnlyCommand():
    """Return True if the current command is a read-only command, which should not trigger any database writes."""
    if (
        isImportingData()
        or isRunningMigrations()
        or isRebuildingData()
        or isRunningBackup()
    ):
        return True

    return cmd_context['read_only']


def canAppAccessDatabase(
    allow_test: bool = False, allow_plugins: bool = False, allow_shell: bool = False
):
    """Returns True if the apps.py file can access database records.

    Arguments:
        allow_test: If True, override checks and allow database access during testing mode
        allow_plugins: If True, override checks and allow database access during plugin loading
        allow_shell: If True, override checks and allow database access during shell sessions

    There are some circumstances where we don't want the ready function in apps.py
    to touch the database
    """
    # Prevent database access if we are running backups
    if isRunningBackup():
        return False

    # Prevent database access if we are importing data
    if not allow_plugins and isImportingData():
        return False

    # Prevent database access if we are rebuilding data
    if isRebuildingData():
        return False

    # Prevent database access if we are running migrations
    if not allow_plugins and isRunningMigrations():
        return False

    # If any of the following management commands are being executed,
    # prevent custom "on load" code from running!
    if cmd_context['database_excluded']:
        return False

    if not allow_shell and cmd_context['shell']:
        return False

    if not allow_plugins and (
        cmd_context['collect_plugins'] or cmd_context['list_apps']
    ):
        return False

    # Override for testing mode?
    return allow_test or not cmd_context['test_command']


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
