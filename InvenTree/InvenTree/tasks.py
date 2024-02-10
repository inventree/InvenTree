"""Functions for tasks and a few general async tasks."""

import json
import logging
import os
import random
import re
import time
import warnings
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Callable, List

from django.conf import settings
from django.core.exceptions import AppRegistryNotReady
from django.core.management import call_command
from django.db import DEFAULT_DB_ALIAS, connections
from django.db.migrations.executor import MigrationExecutor
from django.db.utils import NotSupportedError, OperationalError, ProgrammingError
from django.utils import timezone

import requests
from maintenance_mode.core import (
    get_maintenance_mode,
    maintenance_mode_on,
    set_maintenance_mode,
)

from InvenTree.config import get_setting
from plugin import registry

from .version import isInvenTreeUpToDate

logger = logging.getLogger('inventree')


def schedule_task(taskname, **kwargs):
    """Create a scheduled task.

    If the task has already been scheduled, ignore!
    """
    # If unspecified, repeat indefinitely
    repeats = kwargs.pop('repeats', -1)
    kwargs['repeats'] = repeats

    try:
        from django_q.models import Schedule
    except AppRegistryNotReady:  # pragma: no cover
        logger.info('Could not start background tasks - App registry not ready')
        return

    try:
        # If this task is already scheduled, don't schedule it again
        # Instead, update the scheduling parameters
        if Schedule.objects.filter(func=taskname).exists():
            logger.debug("Scheduled task '%s' already exists - updating!", taskname)

            Schedule.objects.filter(func=taskname).update(**kwargs)
        else:
            logger.info("Creating scheduled task '%s'", taskname)

            Schedule.objects.create(name=taskname, func=taskname, **kwargs)
    except (OperationalError, ProgrammingError):  # pragma: no cover
        # Required if the DB is not ready yet
        pass


def raise_warning(msg):
    """Log and raise a warning."""
    logger.warning(msg)

    # If testing is running raise a warning that can be asserted
    if settings.TESTING:
        warnings.warn(msg, stacklevel=2)


def check_daily_holdoff(task_name: str, n_days: int = 1) -> bool:
    """Check if a periodic task should be run, based on the provided setting name.

    Arguments:
        task_name (str): The name of the task being run, e.g. 'dummy_task'
        n_days (int): The number of days between task runs (default = 1)

    Returns:
        bool: If the task should be run *now*, or wait another day

    This function will determine if the task should be run *today*,
    based on when it was last run, or if we have a record of it running at all.

    Note that this function creates some *hidden* global settings (designated with the _ prefix),
    which are used to keep a running track of when the particular task was was last run.
    """
    from common.models import InvenTreeSetting
    from InvenTree.ready import isInTestMode

    if n_days <= 0:
        logger.info(
            "Specified interval for task '%s' < 1 - task will not run", task_name
        )
        return False

    # Sleep a random number of seconds to prevent worker conflict
    if not isInTestMode():
        time.sleep(random.randint(1, 5))

    attempt_key = f'_{task_name}_ATTEMPT'
    success_key = f'_{task_name}_SUCCESS'

    # Check for recent success information
    last_success = InvenTreeSetting.get_setting(success_key, '', cache=False)

    if last_success:
        try:
            last_success = datetime.fromisoformat(last_success)
        except ValueError:
            last_success = None

    if last_success:
        threshold = datetime.now() - timedelta(days=n_days)

        if last_success > threshold:
            logger.info(
                "Last successful run for '%s' was too recent - skipping task", task_name
            )
            return False

    # Check for any information we have about this task
    last_attempt = InvenTreeSetting.get_setting(attempt_key, '', cache=False)

    if last_attempt:
        try:
            last_attempt = datetime.fromisoformat(last_attempt)
        except ValueError:
            last_attempt = None

    if last_attempt:
        # Do not attempt if the most recent *attempt* was within 12 hours
        threshold = datetime.now() - timedelta(hours=12)

        if last_attempt > threshold:
            logger.info(
                "Last attempt for '%s' was too recent - skipping task", task_name
            )
            return False

    # Record this attempt
    record_task_attempt(task_name)

    # No reason *not* to run this task now
    return True


def record_task_attempt(task_name: str):
    """Record that a multi-day task has been attempted *now*."""
    from common.models import InvenTreeSetting

    logger.info("Logging task attempt for '%s'", task_name)

    InvenTreeSetting.set_setting(
        f'_{task_name}_ATTEMPT', datetime.now().isoformat(), None
    )


def record_task_success(task_name: str):
    """Record that a multi-day task was successful *now*."""
    from common.models import InvenTreeSetting

    InvenTreeSetting.set_setting(
        f'_{task_name}_SUCCESS', datetime.now().isoformat(), None
    )


def offload_task(
    taskname, *args, force_async=False, force_sync=False, **kwargs
) -> bool:
    """Create an AsyncTask if workers are running. This is different to a 'scheduled' task, in that it only runs once!

    If workers are not running or force_sync flag, is set then the task is ran synchronously.

    Returns:
        bool: True if the task was offloaded (or ran), False otherwise
    """
    try:
        import importlib

        from django_q.tasks import AsyncTask

        from InvenTree.status import is_worker_running
    except AppRegistryNotReady:  # pragma: no cover
        logger.warning("Could not offload task '%s' - app registry not ready", taskname)

        if force_async:
            # Cannot async the task, so return False
            return False
        else:
            force_sync = True
    except (OperationalError, ProgrammingError):  # pragma: no cover
        raise_warning(f"Could not offload task '{taskname}' - database not ready")

        if force_async:
            # Cannot async the task, so return False
            return False
        else:
            force_sync = True

    if force_async or (is_worker_running() and not force_sync):
        # Running as asynchronous task
        try:
            task = AsyncTask(taskname, *args, **kwargs)
            task.run()
        except ImportError:
            raise_warning(f"WARNING: '{taskname}' not offloaded - Function not found")
            return False
        except Exception as exc:
            raise_warning(f"WARNING: '{taskname}' not offloaded due to {str(exc)}")
            return False
    else:
        if callable(taskname):
            # function was passed - use that
            _func = taskname
        else:
            # Split path
            try:
                app, mod, func = taskname.split('.')
                app_mod = app + '.' + mod
            except ValueError:
                raise_warning(
                    f"WARNING: '{taskname}' not started - Malformed function path"
                )
                return False

            # Import module from app
            try:
                _mod = importlib.import_module(app_mod)
            except ModuleNotFoundError:
                raise_warning(
                    f"WARNING: '{taskname}' not started - No module named '{app_mod}'"
                )
                return False

            # Retrieve function
            try:
                _func = getattr(_mod, func)
            except AttributeError:  # pragma: no cover
                # getattr does not work for local import
                _func = None

            try:
                if not _func:
                    _func = eval(func)  # pragma: no cover
            except NameError:
                raise_warning(
                    f"WARNING: '{taskname}' not started - No function named '{func}'"
                )
                return False

        # Workers are not running: run it as synchronous task
        try:
            _func(*args, **kwargs)
        except Exception as exc:
            raise_warning(f"WARNING: '{taskname}' not started due to {str(exc)}")
            return False

    # Finally, task either completed successfully or was offloaded
    return True


@dataclass()
class ScheduledTask:
    """A scheduled task.

    - interval: The interval at which the task should be run
    - minutes: The number of minutes between task runs
    - func: The function to be run
    """

    func: Callable
    interval: str
    minutes: int = None

    MINUTES = 'I'
    HOURLY = 'H'
    DAILY = 'D'
    WEEKLY = 'W'
    MONTHLY = 'M'
    QUARTERLY = 'Q'
    YEARLY = 'Y'
    TYPE = [MINUTES, HOURLY, DAILY, WEEKLY, MONTHLY, QUARTERLY, YEARLY]


class TaskRegister:
    """Registry for periodic tasks."""

    task_list: List[ScheduledTask] = []

    def register(self, task, schedule, minutes: int = None):
        """Register a task with the que."""
        self.task_list.append(ScheduledTask(task, schedule, minutes))


tasks = TaskRegister()


def scheduled_task(interval: str, minutes: int = None, tasklist: TaskRegister = None):
    """Register the given task as a scheduled task.

    Example:
    ```python
    @scheduled_task(ScheduledTask.DAILY)
    def my_custom_function():
        # Perform a custom function once per day
        ...
    ```

    Args:
        interval (str): The interval at which the task should be run
        minutes (int, optional): The number of minutes between task runs. Defaults to None.
        tasklist (TaskRegister, optional): The list the tasks should be registered to. Defaults to None.

    Raises:
        ValueError: If decorated object is not callable
        ValueError: If interval is not valid

    Returns:
        _type_: _description_
    """

    def _task_wrapper(admin_class):
        if not isinstance(admin_class, Callable):
            raise ValueError('Wrapped object must be a function')

        if interval not in ScheduledTask.TYPE:
            raise ValueError(f'Invalid interval. Must be one of {ScheduledTask.TYPE}')

        _tasks = tasklist if tasklist else tasks
        _tasks.register(admin_class, interval, minutes=minutes)

        return admin_class

    return _task_wrapper


@scheduled_task(ScheduledTask.MINUTES, 5)
def heartbeat():
    """Simple task which runs at 5 minute intervals, so we can determine that the background worker is actually running.

    (There is probably a less "hacky" way of achieving this)?
    """
    try:
        from django_q.models import OrmQ, Success
    except AppRegistryNotReady:  # pragma: no cover
        logger.info('Could not perform heartbeat task - App registry not ready')
        return

    threshold = timezone.now() - timedelta(minutes=30)

    # Delete heartbeat results more than half an hour old,
    # otherwise they just create extra noise
    heartbeats = Success.objects.filter(
        func='InvenTree.tasks.heartbeat', started__lte=threshold
    )

    heartbeats.delete()

    # Clear out any other pending heartbeat tasks
    for task in OrmQ.objects.all():
        if task.func() == 'InvenTree.tasks.heartbeat':
            task.delete()


@scheduled_task(ScheduledTask.DAILY)
def delete_successful_tasks():
    """Delete successful task logs which are older than a specified period."""
    try:
        from django_q.models import Success

        from common.models import InvenTreeSetting

        days = InvenTreeSetting.get_setting('INVENTREE_DELETE_TASKS_DAYS', 30)
        threshold = timezone.now() - timedelta(days=days)

        # Delete successful tasks
        results = Success.objects.filter(started__lte=threshold)

        if results.count() > 0:
            logger.info('Deleting %s successful task records', results.count())
            results.delete()

    except AppRegistryNotReady:  # pragma: no cover
        logger.info(
            "Could not perform 'delete_successful_tasks' - App registry not ready"
        )


@scheduled_task(ScheduledTask.DAILY)
def delete_failed_tasks():
    """Delete failed task logs which are older than a specified period."""
    try:
        from django_q.models import Failure

        from common.models import InvenTreeSetting

        days = InvenTreeSetting.get_setting('INVENTREE_DELETE_TASKS_DAYS', 30)
        threshold = timezone.now() - timedelta(days=days)

        # Delete failed tasks
        results = Failure.objects.filter(started__lte=threshold)

        if results.count() > 0:
            logger.info('Deleting %s failed task records', results.count())
            results.delete()

    except AppRegistryNotReady:  # pragma: no cover
        logger.info("Could not perform 'delete_failed_tasks' - App registry not ready")


@scheduled_task(ScheduledTask.DAILY)
def delete_old_error_logs():
    """Delete old error logs from the server."""
    try:
        from error_report.models import Error

        from common.models import InvenTreeSetting

        days = InvenTreeSetting.get_setting('INVENTREE_DELETE_ERRORS_DAYS', 30)
        threshold = timezone.now() - timedelta(days=days)

        errors = Error.objects.filter(when__lte=threshold)

        if errors.count() > 0:
            logger.info('Deleting %s old error logs', errors.count())
            errors.delete()

    except AppRegistryNotReady:  # pragma: no cover
        # Apps not yet loaded
        logger.info(
            "Could not perform 'delete_old_error_logs' - App registry not ready"
        )


@scheduled_task(ScheduledTask.DAILY)
def delete_old_notifications():
    """Delete old notification logs."""
    try:
        from common.models import (
            InvenTreeSetting,
            NotificationEntry,
            NotificationMessage,
        )

        days = InvenTreeSetting.get_setting('INVENTREE_DELETE_NOTIFICATIONS_DAYS', 30)
        threshold = timezone.now() - timedelta(days=days)

        items = NotificationEntry.objects.filter(updated__lte=threshold)

        if items.count() > 0:
            logger.info('Deleted %s old notification entries', items.count())
            items.delete()

        items = NotificationMessage.objects.filter(creation__lte=threshold)

        if items.count() > 0:
            logger.info('Deleted %s old notification messages', items.count())
            items.delete()

    except AppRegistryNotReady:
        logger.info(
            "Could not perform 'delete_old_notifications' - App registry not ready"
        )


@scheduled_task(ScheduledTask.DAILY)
def check_for_updates():
    """Check if there is an update for InvenTree."""
    try:
        import common.models
        from common.notifications import trigger_superuser_notification
    except AppRegistryNotReady:  # pragma: no cover
        # Apps not yet loaded!
        logger.info("Could not perform 'check_for_updates' - App registry not ready")
        return

    interval = int(
        common.models.InvenTreeSetting.get_setting(
            'INVENTREE_UPDATE_CHECK_INTERVAL', 7, cache=False
        )
    )

    # Check if we should check for updates *today*
    if not check_daily_holdoff('check_for_updates', interval):
        return

    logger.info('Checking for InvenTree software updates')

    headers = {}

    # If running within github actions, use authentication token
    if settings.TESTING:
        token = os.getenv('GITHUB_TOKEN', None)

        if token:
            headers['Authorization'] = f'Bearer {token}'

    response = requests.get(
        'https://api.github.com/repos/inventree/inventree/releases/latest',
        headers=headers,
    )

    if response.status_code != 200:
        raise ValueError(
            f'Unexpected status code from GitHub API: {response.status_code}'
        )  # pragma: no cover

    data = json.loads(response.text)

    tag = data.get('tag_name', None)

    if not tag:
        raise ValueError("'tag_name' missing from GitHub response")  # pragma: no cover

    match = re.match(r'^.*(\d+)\.(\d+)\.(\d+).*$', tag)

    if len(match.groups()) != 3:  # pragma: no cover
        logger.warning("Version '%s' did not match expected pattern", tag)
        return

    latest_version = [int(x) for x in match.groups()]

    if len(latest_version) != 3:
        raise ValueError(f"Version '{tag}' is not correct format")  # pragma: no cover

    logger.info("Latest InvenTree version: '%s'", tag)

    # Save the version to the database
    common.models.InvenTreeSetting.set_setting('_INVENTREE_LATEST_VERSION', tag, None)

    # Record that this task was successful
    record_task_success('check_for_updates')

    # Send notification if there is a new version
    if not isInvenTreeUpToDate():
        logger.warning('InvenTree is not up-to-date, sending notification')

        plg = registry.get_plugin('InvenTreeCoreNotificationsPlugin')
        if not plg:
            logger.warning('Cannot send notification - plugin not found')
            return
        plg = plg.plugin_config()
        if not plg:
            logger.warning('Cannot send notification - plugin config not found')
            return
        # Send notification
        trigger_superuser_notification(
            plg, f'An update for InvenTree to version {tag} is available'
        )


@scheduled_task(ScheduledTask.DAILY)
def update_exchange_rates(force: bool = False):
    """Update currency exchange rates.

    Arguments:
        force: If True, force the update to run regardless of the last update time
    """
    try:
        from djmoney.contrib.exchange.models import Rate

        from common.models import InvenTreeSetting
        from common.settings import currency_code_default, currency_codes
        from InvenTree.exchange import InvenTreeExchange
    except AppRegistryNotReady:  # pragma: no cover
        # Apps not yet loaded!
        logger.info(
            "Could not perform 'update_exchange_rates' - App registry not ready"
        )
        return
    except Exception as exc:  # pragma: no cover
        logger.info("Could not perform 'update_exchange_rates' - %s", exc)
        return

    if not force:
        interval = int(
            InvenTreeSetting.get_setting('CURRENCY_UPDATE_INTERVAL', 1, cache=False)
        )

        if not check_daily_holdoff('update_exchange_rates', interval):
            logger.info('Skipping exchange rate update (interval not reached)')
            return

    backend = InvenTreeExchange()
    base = currency_code_default()
    logger.info("Updating exchange rates using base currency '%s'", base)

    try:
        backend.update_rates(base_currency=base)

        # Remove any exchange rates which are not in the provided currencies
        Rate.objects.filter(backend='InvenTreeExchange').exclude(
            currency__in=currency_codes()
        ).delete()

        # Record successful task execution
        record_task_success('update_exchange_rates')

    except (AppRegistryNotReady, OperationalError, ProgrammingError):
        logger.warning('Could not update exchange rates - database not ready')
    except Exception as e:  # pragma: no cover
        logger.exception('Error updating exchange rates: %s', str(type(e)))


@scheduled_task(ScheduledTask.DAILY)
def run_backup():
    """Run the backup command."""
    from common.models import InvenTreeSetting

    if not InvenTreeSetting.get_setting('INVENTREE_BACKUP_ENABLE', False, cache=False):
        # Backups are not enabled - exit early
        return

    interval = int(
        InvenTreeSetting.get_setting('INVENTREE_BACKUP_DAYS', 1, cache=False)
    )

    # Check if should run this task *today*
    if not check_daily_holdoff('run_backup', interval):
        return

    logger.info('Performing automated database backup task')

    call_command('dbbackup', noinput=True, clean=True, compress=True, interactive=False)
    call_command(
        'mediabackup', noinput=True, clean=True, compress=True, interactive=False
    )

    # Record that this task was successful
    record_task_success('run_backup')


def get_migration_plan():
    """Returns a list of migrations which are needed to be run."""
    executor = MigrationExecutor(connections[DEFAULT_DB_ALIAS])
    plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
    return plan


@scheduled_task(ScheduledTask.DAILY)
def check_for_migrations(force: bool = False, reload_registry: bool = True):
    """Checks if migrations are needed.

    If the setting auto_update is enabled we will start updating.
    """
    from common.models import InvenTreeSetting
    from plugin import registry

    def set_pending_migrations(n: int):
        """Helper function to inform the user about pending migrations."""
        logger.info('There are %s pending migrations', n)
        InvenTreeSetting.set_setting('_PENDING_MIGRATIONS', n, None)

    logger.info('Checking for pending database migrations')

    if reload_registry:
        # Force plugin registry reload
        registry.check_reload()

    plan = get_migration_plan()

    n = len(plan)

    # Check if there are any open migrations
    if not plan:
        set_pending_migrations(0)
        return

    set_pending_migrations(n)

    # Test if auto-updates are enabled
    if not force and not get_setting('INVENTREE_AUTO_UPDATE', 'auto_update'):
        logger.info('Auto-update is disabled - skipping migrations')
        return

    # Log open migrations
    for migration in plan:
        logger.info('- %s', str(migration[0]))

    # Set the application to maintenance mode - no access from now on.
    set_maintenance_mode(True)

    # To be sure we are in maintenance this is wrapped
    with maintenance_mode_on():
        logger.info('Starting migration process...')

        try:
            call_command('migrate', interactive=False)
        except NotSupportedError as e:  # pragma: no cover
            if settings.DATABASES['default']['ENGINE'] != 'django.db.backends.sqlite3':
                raise e
            logger.exception('Error during migrations: %s', e)
        else:
            set_pending_migrations(0)

            logger.info('Completed %s migrations', n)

    # Make sure we are out of maintenance mode
    if get_maintenance_mode():
        logger.warning('Maintenance mode was not disabled - forcing it now')
        set_maintenance_mode(False)
        logger.info('Manually released maintenance mode')

    if reload_registry:
        # We should be current now - triggering full reload to make sure all models
        # are loaded fully in their new state.
        registry.reload_plugins(full_reload=True, force_reload=True, collect=True)
