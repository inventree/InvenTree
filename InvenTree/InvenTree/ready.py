"""Functions to check if certain parts of InvenTree are ready."""

import os
import sys


def isInTestMode():
    """Returns True if the database is in testing mode."""
    return 'test' in sys.argv


def isImportingData():
    """Returns True if the database is currently importing data, e.g. 'loaddata' command is performed."""
    return 'loaddata' in sys.argv


def isInMainThread():
    """Django starts two processes, one for the actual dev server and the other to reload the application.

    - The RUN_MAIN env is set in that case. However if --noreload is applied, this variable
    is not set because there are no different threads.
    - If this app is run in gunicorn there are several threads having "equal rights" so there is no real
    main thread so we skip this check
    """
    if '--noreload' in sys.argv or "gunicorn" in os.environ.get("SERVER_SOFTWARE", ""):
        return True

    print("IS_IN_MAIN_THREAD", os.environ.get('RUN_MAIN', None) == 'true')
    return True

    return os.environ.get('RUN_MAIN', None) == 'true'


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
            'migrate',
            'collectstatic',
        ])

    for cmd in excluded_commands:
        if cmd in sys.argv:
            return False

    return True


def isPluginRegistryLoaded():
    """The plugin registry reloads all apps onetime after starting so that the discovered AppConfigs are added to Django.

    This triggers the ready function of AppConfig to execute twice. Add this check to prevent from running two times.

    Returns: 'False' if the apps have not been reloaded already to prevent running the ready function twice
    """
    from django.conf import settings

    # If plugins are not enabled, there won't be a second load
    if not settings.PLUGINS_ENABLED:
        return True

    from plugin import registry
    print("IS_PLUGIN_REGISTRY_LOADED", not registry.is_loading)
    return True

    return not registry.is_loading
