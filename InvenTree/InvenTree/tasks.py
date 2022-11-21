"""Functions for tasks and a few general async tasks."""

import json
import logging
import re
import warnings
from dataclasses import dataclass
from datetime import timedelta
from typing import Callable, List

from django.conf import settings
from django.core import mail as django_mail
from django.core.exceptions import AppRegistryNotReady
from django.core.management import call_command
from django.db.utils import OperationalError, ProgrammingError
from django.utils import timezone

import requests

logger = logging.getLogger("inventree")


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
        logger.info("Could not start background tasks - App registry not ready")
        return

    try:
        # If this task is already scheduled, don't schedule it again
        # Instead, update the scheduling parameters
        if Schedule.objects.filter(func=taskname).exists():
            logger.debug(f"Scheduled task '{taskname}' already exists - updating!")

            Schedule.objects.filter(func=taskname).update(**kwargs)
        else:
            logger.info(f"Creating scheduled task '{taskname}'")

            Schedule.objects.create(
                name=taskname,
                func=taskname,
                **kwargs
            )
    except (OperationalError, ProgrammingError):  # pragma: no cover
        # Required if the DB is not ready yet
        pass


def raise_warning(msg):
    """Log and raise a warning."""
    logger.warning(msg)

    # If testing is running raise a warning that can be asserted
    if settings.TESTING:
        warnings.warn(msg)


def offload_task(taskname, *args, force_async=False, force_sync=False, **kwargs):
    """Create an AsyncTask if workers are running. This is different to a 'scheduled' task, in that it only runs once!

    If workers are not running or force_sync flag
    is set then the task is ran synchronously.
    """
    try:
        import importlib

        from django_q.tasks import AsyncTask

        from InvenTree.status import is_worker_running
    except AppRegistryNotReady:  # pragma: no cover
        logger.warning(f"Could not offload task '{taskname}' - app registry not ready")
        return
    except (OperationalError, ProgrammingError):  # pragma: no cover
        raise_warning(f"Could not offload task '{taskname}' - database not ready")

    if force_async or (is_worker_running() and not force_sync):
        # Running as asynchronous task
        try:
            task = AsyncTask(taskname, *args, **kwargs)
            task.run()
        except ImportError:
            raise_warning(f"WARNING: '{taskname}' not started - Function not found")
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
                raise_warning(f"WARNING: '{taskname}' not started - Malformed function path")
                return

            # Import module from app
            try:
                _mod = importlib.import_module(app_mod)
            except ModuleNotFoundError:
                raise_warning(f"WARNING: '{taskname}' not started - No module named '{app_mod}'")
                return

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
                raise_warning(f"WARNING: '{taskname}' not started - No function named '{func}'")
                return

        # Workers are not running: run it as synchronous task
        _func(*args, **kwargs)


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

    MINUTES = "I"
    HOURLY = "H"
    DAILY = "D"
    WEEKLY = "W"
    MONTHLY = "M"
    QUARTERLY = "Q"
    YEARLY = "Y"
    TYPE = [MINUTES, HOURLY, DAILY, WEEKLY, MONTHLY, QUARTERLY, YEARLY]


class TaskRegister:
    """Registery for periodicall tasks."""
    task_list: List[ScheduledTask] = []

    def register(self, task, schedule, minutes: int = None):
        """Register a task with the que."""
        self.task_list.append(ScheduledTask(task, schedule, minutes))


tasks = TaskRegister()


def scheduled_task(interval: str, minutes: int = None, tasklist: TaskRegister = None):
    """Register the given task as a scheduled task.

    Example:
    ```python
    @register(ScheduledTask.DAILY)
    def my_custom_funciton():
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
        from django_q.models import Success
    except AppRegistryNotReady:  # pragma: no cover
        logger.info("Could not perform heartbeat task - App registry not ready")
        return

    threshold = timezone.now() - timedelta(minutes=30)

    # Delete heartbeat results more than half an hour old,
    # otherwise they just create extra noise
    heartbeats = Success.objects.filter(
        func='InvenTree.tasks.heartbeat',
        started__lte=threshold
    )

    heartbeats.delete()


@scheduled_task(ScheduledTask.DAILY)
def delete_successful_tasks():
    """Delete successful task logs which are older than a specified period"""
    try:
        from django_q.models import Success

        from common.models import InvenTreeSetting

        days = InvenTreeSetting.get_setting('INVENTREE_DELETE_TASKS_DAYS', 30)
        threshold = timezone.now() - timedelta(days=days)

        # Delete successful tasks
        results = Success.objects.filter(
            started__lte=threshold
        )

        if results.count() > 0:
            logger.info(f"Deleting {results.count()} successful task records")
            results.delete()

    except AppRegistryNotReady:  # pragma: no cover
        logger.info("Could not perform 'delete_successful_tasks' - App registry not ready")


@scheduled_task(ScheduledTask.DAILY)
def delete_failed_tasks():
    """Delete failed task logs which are older than a specified period"""

    try:
        from django_q.models import Failure

        from common.models import InvenTreeSetting

        days = InvenTreeSetting.get_setting('INVENTREE_DELETE_TASKS_DAYS', 30)
        threshold = timezone.now() - timedelta(days=days)

        # Delete failed tasks
        results = Failure.objects.filter(
            started__lte=threshold
        )

        if results.count() > 0:
            logger.info(f"Deleting {results.count()} failed task records")
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

        errors = Error.objects.filter(
            when__lte=threshold,
        )

        if errors.count() > 0:
            logger.info(f"Deleting {errors.count()} old error logs")
            errors.delete()

    except AppRegistryNotReady:  # pragma: no cover
        # Apps not yet loaded
        logger.info("Could not perform 'delete_old_error_logs' - App registry not ready")


@scheduled_task(ScheduledTask.DAILY)
def delete_old_notifications():
    """Delete old notification logs"""

    try:
        from common.models import (InvenTreeSetting, NotificationEntry,
                                   NotificationMessage)

        days = InvenTreeSetting.get_setting('INVENTREE_DELETE_NOTIFICATIONS_DAYS', 30)
        threshold = timezone.now() - timedelta(days=days)

        items = NotificationEntry.objects.filter(
            updated__lte=threshold
        )

        if items.count() > 0:
            logger.info(f"Deleted {items.count()} old notification entries")
            items.delete()

        items = NotificationMessage.objects.filter(
            creation__lte=threshold
        )

        if items.count() > 0:
            logger.info(f"Deleted {items.count()} old notification messages")
            items.delete()

    except AppRegistryNotReady:
        logger.info("Could not perform 'delete_old_notifications' - App registry not ready")


@scheduled_task(ScheduledTask.DAILY)
def check_for_updates():
    """Check if there is an update for InvenTree."""
    try:
        import common.models
    except AppRegistryNotReady:  # pragma: no cover
        # Apps not yet loaded!
        logger.info("Could not perform 'check_for_updates' - App registry not ready")
        return

    response = requests.get('https://api.github.com/repos/inventree/inventree/releases/latest')

    if response.status_code != 200:
        raise ValueError(f'Unexpected status code from GitHub API: {response.status_code}')  # pragma: no cover

    data = json.loads(response.text)

    tag = data.get('tag_name', None)

    if not tag:
        raise ValueError("'tag_name' missing from GitHub response")  # pragma: no cover

    match = re.match(r"^.*(\d+)\.(\d+)\.(\d+).*$", tag)

    if len(match.groups()) != 3:  # pragma: no cover
        logger.warning(f"Version '{tag}' did not match expected pattern")
        return

    latest_version = [int(x) for x in match.groups()]

    if len(latest_version) != 3:
        raise ValueError(f"Version '{tag}' is not correct format")  # pragma: no cover

    logger.info(f"Latest InvenTree version: '{tag}'")

    # Save the version to the database
    common.models.InvenTreeSetting.set_setting(
        'INVENTREE_LATEST_VERSION',
        tag,
        None
    )


@scheduled_task(ScheduledTask.DAILY)
def update_exchange_rates():
    """Update currency exchange rates."""
    try:
        from djmoney.contrib.exchange.models import ExchangeBackend, Rate

        from common.settings import currency_code_default, currency_codes
        from InvenTree.exchange import InvenTreeExchange
    except AppRegistryNotReady:  # pragma: no cover
        # Apps not yet loaded!
        logger.info("Could not perform 'update_exchange_rates' - App registry not ready")
        return
    except Exception:  # pragma: no cover
        # Other error?
        return

    # Test to see if the database is ready yet
    try:
        backend = ExchangeBackend.objects.get(name='InvenTreeExchange')
    except ExchangeBackend.DoesNotExist:
        pass
    except Exception:  # pragma: no cover
        # Some other error
        logger.warning("update_exchange_rates: Database not ready")
        return

    backend = InvenTreeExchange()
    logger.info(f"Updating exchange rates from {backend.url}")

    base = currency_code_default()

    logger.info(f"Using base currency '{base}'")

    try:
        backend.update_rates(base_currency=base)

        # Remove any exchange rates which are not in the provided currencies
        Rate.objects.filter(backend="InvenTreeExchange").exclude(currency__in=currency_codes()).delete()
    except Exception as e:  # pragma: no cover
        logger.error(f"Error updating exchange rates: {e}")


@scheduled_task(ScheduledTask.DAILY)
def run_backup():
    """Run the backup command."""
    from common.models import InvenTreeSetting

    if InvenTreeSetting.get_setting('INVENTREE_BACKUP_ENABLE'):
        call_command("dbbackup", noinput=True, clean=True, compress=True, interactive=False)
        call_command("mediabackup", noinput=True, clean=True, compress=True, interactive=False)


def send_email(subject, body, recipients, from_email=None, html_message=None):
    """Send an email with the specified subject and body, to the specified recipients list."""
    if type(recipients) == str:
        recipients = [recipients]

    offload_task(
        django_mail.send_mail,
        subject,
        body,
        from_email,
        recipients,
        fail_silently=False,
        html_message=html_message
    )
