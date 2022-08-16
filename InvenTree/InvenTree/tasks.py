"""Functions for tasks and a few general async tasks."""

import json
import logging
import re
import warnings
from datetime import timedelta

from django.conf import settings
from django.core import mail as django_mail
from django.core.exceptions import AppRegistryNotReady
from django.core.management import call_command
from django.db import DEFAULT_DB_ALIAS, connections
from django.db.migrations.executor import MigrationExecutor
from django.db.utils import OperationalError, ProgrammingError
from django.utils import timezone

import requests
from maintenance_mode.core import (get_maintenance_mode, maintenance_mode_on,
                                   set_maintenance_mode)

from InvenTree.config import get_setting

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


def delete_successful_tasks():
    """Delete successful task logs which are more than a month old."""
    try:
        from django_q.models import Success
    except AppRegistryNotReady:  # pragma: no cover
        logger.info("Could not perform 'delete_successful_tasks' - App registry not ready")
        return

    threshold = timezone.now() - timedelta(days=30)

    results = Success.objects.filter(
        started__lte=threshold
    )

    if results.count() > 0:
        logger.info(f"Deleting {results.count()} successful task records")
        results.delete()


def delete_old_error_logs():
    """Delete old error logs from the server."""
    try:
        from error_report.models import Error

        # Delete any error logs more than 30 days old
        threshold = timezone.now() - timedelta(days=30)

        errors = Error.objects.filter(
            when__lte=threshold,
        )

        if errors.count() > 0:
            logger.info(f"Deleting {errors.count()} old error logs")
            errors.delete()

    except AppRegistryNotReady:  # pragma: no cover
        # Apps not yet loaded
        logger.info("Could not perform 'delete_old_error_logs' - App registry not ready")
        return


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


def check_for_migrations():
    """Checks if migrations are needed.

    If the setting auto_update is enabled we will start updateing.
    """
    # Test if auto-updates are enabled
    if not get_setting('INVENTREE_AUTO_UPDATE', 'auto_update'):
        return

    from plugin import registry

    executor = MigrationExecutor(connections[DEFAULT_DB_ALIAS])
    plan = executor.migration_plan(executor.loader.graph.leaf_nodes())

    # Check if there are any open migrations
    if not plan:
        logger.info('There are no open migrations')
        return

    logger.info('There are open migrations')

    # Log open migrations
    for migration in plan:
        logger.info(migration[0])

    # Set the application to maintenance mode - no access from now on.
    logger.info('Going into maintenance')
    set_maintenance_mode(True)
    logger.info('Mainentance mode is on now')

    # Check if we are worker - go kill all other workers then.
    # Only the frontend workers run updates.

    # TODO
    if True:
        logger.info('Current process is a worker - shutting down cluster')

    # Ok now we are ready to go ahead!
    # To be sure we are in maintenance this is wrapped
    with maintenance_mode_on():
        logger.info('Starting migrations')
        call_command('migrate', interactive=False)
        logger.info('Ran migrations')

    # Make sure we are out of maintenance again
    logger.info('Checking InvenTree left maintenance mode')
    if get_maintenance_mode():

        logger.warning('Mainentance was still on - releasing now')
        set_maintenance_mode(False)
        logger.info('Released out of maintenance')

    # We should be current now - triggering full reload to make sure all models
    # are loaded fully in their new state.
    registry.reload_plugins(full_reload=True, force_reload=True)
