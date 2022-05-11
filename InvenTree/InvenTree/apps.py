# -*- coding: utf-8 -*-

import logging

from django.apps import AppConfig
from django.core.exceptions import AppRegistryNotReady
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.utils import IntegrityError

from InvenTree.ready import isInTestMode, canAppAccessDatabase
from .config import get_setting
import InvenTree.tasks


logger = logging.getLogger("inventree")


class InvenTreeConfig(AppConfig):
    name = 'InvenTree'

    def ready(self):

        if canAppAccessDatabase():

            self.remove_obsolete_tasks()

            self.start_background_tasks()

            if not isInTestMode():  # pragma: no cover
                self.update_exchange_rates()

        self.collect_notification_methods()

        if canAppAccessDatabase() or settings.TESTING_ENV:
            self.add_user_on_startup()

    def remove_obsolete_tasks(self):
        """
        Delete any obsolete scheduled tasks in the database
        """

        obsolete = [
            'InvenTree.tasks.delete_expired_sessions',
            'stock.tasks.delete_old_stock_items',
        ]

        try:
            from django_q.models import Schedule
        except AppRegistryNotReady:  # pragma: no cover
            return

        # Remove any existing obsolete tasks
        Schedule.objects.filter(func__in=obsolete).delete()

    def start_background_tasks(self):

        try:
            from django_q.models import Schedule
        except AppRegistryNotReady:  # pragma: no cover
            return

        logger.info("Starting background tasks...")

        # Remove successful task results from the database
        InvenTree.tasks.schedule_task(
            'InvenTree.tasks.delete_successful_tasks',
            schedule_type=Schedule.DAILY,
        )

        # Check for InvenTree updates
        InvenTree.tasks.schedule_task(
            'InvenTree.tasks.check_for_updates',
            schedule_type=Schedule.DAILY
        )

        # Heartbeat to let the server know the background worker is running
        InvenTree.tasks.schedule_task(
            'InvenTree.tasks.heartbeat',
            schedule_type=Schedule.MINUTES,
            minutes=15
        )

        # Keep exchange rates up to date
        InvenTree.tasks.schedule_task(
            'InvenTree.tasks.update_exchange_rates',
            schedule_type=Schedule.DAILY,
        )

        # Delete old error messages
        InvenTree.tasks.schedule_task(
            'InvenTree.tasks.delete_old_error_logs',
            schedule_type=Schedule.DAILY,
        )

        # Delete old notification records
        InvenTree.tasks.schedule_task(
            'common.tasks.delete_old_notifications',
            schedule_type=Schedule.DAILY,
        )

    def update_exchange_rates(self):  # pragma: no cover
        """
        Update exchange rates each time the server is started, *if*:

        a) Have not been updated recently (one day or less)
        b) The base exchange rate has been altered
        """

        try:
            from djmoney.contrib.exchange.models import ExchangeBackend

            from InvenTree.tasks import update_exchange_rates
            from common.settings import currency_code_default
        except AppRegistryNotReady:  # pragma: no cover
            pass

        base_currency = currency_code_default()

        update = False

        try:
            backend = ExchangeBackend.objects.get(name='InvenTreeExchange')

            last_update = backend.last_update

            if last_update is None:
                # Never been updated
                logger.info("Exchange backend has never been updated")
                update = True

            # Backend currency has changed?
            if not base_currency == backend.base_currency:
                logger.info(f"Base currency changed from {backend.base_currency} to {base_currency}")
                update = True

        except (ExchangeBackend.DoesNotExist):
            logger.info("Exchange backend not found - updating")
            update = True

        except:
            # Some other error - potentially the tables are not ready yet
            return

        if update:
            try:
                update_exchange_rates()
            except Exception as e:
                logger.error(f"Error updating exchange rates: {e}")

    def add_user_on_startup(self):
        """Add a user on startup"""
        # stop if checks were already created
        if hasattr(settings, 'USER_ADDED') and settings.USER_ADDED:
            return

        # get values
        add_user = get_setting(
            'INVENTREE_ADMIN_USER',
            settings.CONFIG.get('admin_user', False)
        )
        add_email = get_setting(
            'INVENTREE_ADMIN_EMAIL',
            settings.CONFIG.get('admin_email', False)
        )
        add_password = get_setting(
            'INVENTREE_ADMIN_PASSWORD',
            settings.CONFIG.get('admin_password', False)
        )

        # check if all values are present
        set_variables = 0
        for tested_var in [add_user, add_email, add_password]:
            if tested_var:
                set_variables += 1

        # no variable set -> do not try anything
        if set_variables == 0:
            settings.USER_ADDED = True
            return

        # not all needed variables set
        if set_variables < 3:
            logger.warn('Not all required settings for adding a user on startup are present:\nINVENTREE_ADMIN_USER, INVENTREE_ADMIN_EMAIL, INVENTREE_ADMIN_PASSWORD')
            settings.USER_ADDED = True
            return

        # good to go -> create user
        user = get_user_model()
        try:
            with transaction.atomic():
                if user.objects.filter(username=add_user).exists():
                    logger.info(f"User {add_user} already exists - skipping creation")
                else:
                    new_user = user.objects.create_superuser(add_user, add_email, add_password)
                    logger.info(f'User {str(new_user)} was created!')
        except IntegrityError as _e:
            logger.warning(f'The user "{add_user}" could not be created due to the following error:\n{str(_e)}')
            if settings.TESTING_ENV:
                raise _e

        # do not try again
        settings.USER_ADDED = True

    def collect_notification_methods(self):
        """
        Collect all notification methods
        """
        from common.notifications import storage

        storage.collect()
