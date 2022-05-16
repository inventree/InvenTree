# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re
import json
import requests
import logging

from datetime import timedelta
from django.utils import timezone

from django.core.exceptions import AppRegistryNotReady
from django.db.utils import OperationalError, ProgrammingError
from django.core import mail as django_mail


logger = logging.getLogger("inventree")


def schedule_task(taskname, **kwargs):
    """
    Create a scheduled task.
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


def offload_task(taskname, *args, force_sync=False, **kwargs):
    """
        Create an AsyncTask if workers are running.
        This is different to a 'scheduled' task,
        in that it only runs once!

        If workers are not running or force_sync flag
        is set then the task is ran synchronously.
    """

    try:
        from django_q.tasks import AsyncTask

        import importlib
        from InvenTree.status import is_worker_running

        # make sure the taskname is a string
        if not isinstance(taskname, str):
            taskname = str(taskname)

        if is_worker_running() and not force_sync:  # pragma: no cover
            # Running as asynchronous task
            try:
                task = AsyncTask(taskname, *args, **kwargs)
                task.run()
            except ImportError:
                logger.warning(f"WARNING: '{taskname}' not started - Function not found")
        else:
            # Split path
            try:
                app, mod, func = taskname.split('.')
                app_mod = app + '.' + mod
            except ValueError:
                logger.warning(f"WARNING: '{taskname}' not started - Malformed function path")
                return

            # Import module from app
            try:
                _mod = importlib.import_module(app_mod)
            except ModuleNotFoundError:
                logger.warning(f"WARNING: '{taskname}' not started - No module named '{app_mod}'")
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
                logger.warning(f"WARNING: '{taskname}' not started - No function named '{func}'")
                return

            # Workers are not running: run it as synchronous task
            _func(*args, **kwargs)

    except AppRegistryNotReady:  # pragma: no cover
        logger.warning(f"Could not offload task '{taskname}' - app registry not ready")
        return
    except (OperationalError, ProgrammingError):  # pragma: no cover
        logger.warning(f"Could not offload task '{taskname}' - database not ready")


def heartbeat():
    """
    Simple task which runs at 5 minute intervals,
    so we can determine that the background worker
    is actually running.

    (There is probably a less "hacky" way of achieving this)?
    """

    try:
        from django_q.models import Success
        logger.info("Could not perform heartbeat task - App registry not ready")
    except AppRegistryNotReady:  # pragma: no cover
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
    """
    Delete successful task logs
    which are more than a month old.
    """

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
    """
    Delete old error logs from the server
    """

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
    """
    Check if there is an update for InvenTree
    """

    try:
        import common.models
    except AppRegistryNotReady:  # pragma: no cover
        # Apps not yet loaded!
        logger.info("Could not perform 'check_for_updates' - App registry not ready")
        return

    response = requests.get('https://api.github.com/repos/inventree/inventree/releases/latest')

    if not response.status_code == 200:
        raise ValueError(f'Unexpected status code from GitHub API: {response.status_code}')

    data = json.loads(response.text)

    tag = data.get('tag_name', None)

    if not tag:
        raise ValueError("'tag_name' missing from GitHub response")

    match = re.match(r"^.*(\d+)\.(\d+)\.(\d+).*$", tag)

    if not len(match.groups()) == 3:
        logger.warning(f"Version '{tag}' did not match expected pattern")
        return

    latest_version = [int(x) for x in match.groups()]

    if not len(latest_version) == 3:
        raise ValueError(f"Version '{tag}' is not correct format")

    logger.info(f"Latest InvenTree version: '{tag}'")

    # Save the version to the database
    common.models.InvenTreeSetting.set_setting(
        'INVENTREE_LATEST_VERSION',
        tag,
        None
    )


def update_exchange_rates():
    """
    Update currency exchange rates
    """

    try:
        from InvenTree.exchange import InvenTreeExchange
        from djmoney.contrib.exchange.models import ExchangeBackend, Rate
        from common.settings import currency_code_default, currency_codes
    except AppRegistryNotReady:  # pragma: no cover
        # Apps not yet loaded!
        logger.info("Could not perform 'update_exchange_rates' - App registry not ready")
        return
    except:  # pragma: no cover
        # Other error?
        return

    # Test to see if the database is ready yet
    try:
        backend = ExchangeBackend.objects.get(name='InvenTreeExchange')
    except ExchangeBackend.DoesNotExist:
        pass
    except:  # pragma: no cover
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
    """
    Send an email with the specified subject and body,
    to the specified recipients list.
    """

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
