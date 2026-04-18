"""Configuration settings for the InvenTree background worker process."""

import sys

from InvenTree.config import get_setting


def get_worker_config(
    db_engine: str,
    global_cache: bool = False,
    sentry_dsn: str = '',
    debug: bool = False,
) -> dict:
    """Return a dictionary of configuration settings for the background worker.

    Arguments:
        db_engine: The database engine being used (e.g. 'sqlite', 'postgresql', 'mysql')
        global_cache: Whether a global redis cache is enabled
        sentry_dsn: The DSN for sentry.io integration (if enabled)
        debug: Whether the application is running in debug mode

    Ref: https://django-q2.readthedocs.io/en/master/configure.html
    """
    BACKGROUND_WORKER_TIMEOUT = int(
        get_setting('INVENTREE_BACKGROUND_TIMEOUT', 'background.timeout', 90)
    )

    # Set the retry time for background workers to be slightly longer than the worker timeout, to ensure that workers have time to timeout before being retried
    BACKGROUND_WORKER_RETRY = max(
        int(get_setting('INVENTREE_BACKGROUND_RETRY', 'background.retry', 300)),
        BACKGROUND_WORKER_TIMEOUT + 120,
    )

    BACKGROUND_WORKER_ATTEMPTS = int(
        get_setting('INVENTREE_BACKGROUND_MAX_ATTEMPTS', 'background.max_attempts', 5)
    )

    # Prevent running multiple background workers if global cache is disabled
    # This is to prevent scheduling conflicts due to the lack of a shared cache
    BACKGROUND_WORKER_COUNT = int(
        get_setting('INVENTREE_BACKGROUND_WORKERS', 'background.workers', 4)
    )

    # If global cache is disabled, we cannot run multiple background workers
    if not global_cache:
        BACKGROUND_WORKER_COUNT = 1

    # If running with SQLite, limit background worker threads to 1 to prevent database locking issues
    if 'sqlite' in db_engine:
        BACKGROUND_WORKER_COUNT = 1

    # Check if '--sync' was passed in the command line
    if '--sync' in sys.argv and '--noreload' in sys.argv and debug:
        SYNC_TASKS = True
    else:
        SYNC_TASKS = False

    # Clean up sys.argv so Django doesn't complain about an unknown argument
    if SYNC_TASKS:
        sys.argv.remove('--sync')

    # django-q background worker configuration
    config = {
        'name': 'InvenTree',
        'label': 'Background Tasks',
        'workers': BACKGROUND_WORKER_COUNT,
        'timeout': BACKGROUND_WORKER_TIMEOUT,
        'retry': BACKGROUND_WORKER_RETRY,
        'max_attempts': BACKGROUND_WORKER_ATTEMPTS,
        'save_limit': 1000,
        'queue_limit': 50,
        'catch_up': False,
        'bulk': 10,
        'orm': 'default',
        'cache': 'default',
        'sync': SYNC_TASKS,
        'poll': 1.5,
    }

    if global_cache:
        # If using external redis cache, make the cache the broker for Django Q
        config['django_redis'] = 'worker'

    if sentry_dsn:
        # If sentry is enabled, configure django-q to report errors to sentry
        config['error_reporter'] = {'sentry': {'dsn': sentry_dsn}}

    return config
