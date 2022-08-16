"""AppConfig for inventree app."""

import logging

from django.apps import AppConfig
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import AppRegistryNotReady
from django.core.management import call_command
from django.db import DEFAULT_DB_ALIAS, connections, transaction
from django.db.migrations.executor import MigrationExecutor
from django.db.utils import IntegrityError

from maintenance_mode.core import (get_maintenance_mode, maintenance_mode_on,
                                   set_maintenance_mode)

import InvenTree.tasks
from InvenTree.ready import canAppAccessDatabase, isInTestMode

from .config import get_setting

logger = logging.getLogger("inventree")


class InvenTreeConfig(AppConfig):
    """AppConfig for inventree app."""
    name = 'InvenTree'

    def ready(self):
        """Run system wide setup init steps.

        Like:
        - Checking if migrations should be run
        - Cleaning up tasks
        - Starting regular tasks
        - Updateing exchange rates
        - Collecting notification mehods
        - Adding users set in the current enviroment
        """
        # Check for migrations.
        self.check_for_migrations()

        if canAppAccessDatabase():

            self.remove_obsolete_tasks()

            self.start_background_tasks()

            if not isInTestMode():  # pragma: no cover
                self.update_exchange_rates()

        self.collect_notification_methods()

        if canAppAccessDatabase() or settings.TESTING_ENV:
            self.add_user_on_startup()

    def remove_obsolete_tasks(self):
        """Delete any obsolete scheduled tasks in the database."""
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
        """Start all background tests for InvenTree."""
        try:
            from django_q.models import Schedule
        except AppRegistryNotReady:  # pragma: no cover
            logger.warning("Cannot start background tasks - app registry not ready")
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

        # Check for overdue purchase orders
        InvenTree.tasks.schedule_task(
            'order.tasks.check_overdue_purchase_orders',
            schedule_type=Schedule.DAILY
        )

        # Check for overdue sales orders
        InvenTree.tasks.schedule_task(
            'order.tasks.check_overdue_sales_orders',
            schedule_type=Schedule.DAILY,
        )

        # Check for overdue build orders
        InvenTree.tasks.schedule_task(
            'build.tasks.check_overdue_build_orders',
            schedule_type=Schedule.DAILY
        )

    def update_exchange_rates(self):  # pragma: no cover
        """Update exchange rates each time the server is started.

        Only runs *if*:
        a) Have not been updated recently (one day or less)
        b) The base exchange rate has been altered
        """
        try:
            from djmoney.contrib.exchange.models import ExchangeBackend

            from common.settings import currency_code_default
            from InvenTree.tasks import update_exchange_rates
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
            if base_currency != backend.base_currency:
                logger.info(f"Base currency changed from {backend.base_currency} to {base_currency}")
                update = True

        except (ExchangeBackend.DoesNotExist):
            logger.info("Exchange backend not found - updating")
            update = True

        except Exception:
            # Some other error - potentially the tables are not ready yet
            return

        if update:
            try:
                update_exchange_rates()
            except Exception as e:
                logger.error(f"Error updating exchange rates: {e}")

    def add_user_on_startup(self):
        """Add a user on startup."""
        # stop if checks were already created
        if hasattr(settings, 'USER_ADDED') and settings.USER_ADDED:
            return

        # get values
        add_user = get_setting('INVENTREE_ADMIN_USER', 'admin_user')
        add_email = get_setting('INVENTREE_ADMIN_EMAIL', 'admin_email')
        add_password = get_setting('INVENTREE_ADMIN_PASSWORD', 'admin_password')

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

        # do not try again
        settings.USER_ADDED = True

    def collect_notification_methods(self):
        """Collect all notification methods."""
        from common.notifications import storage

        storage.collect()

    def check_for_migrations(self):
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
            call_command('migrate', interactive=False)

        # Make sure we are out of maintenance again
        logger.info('Checking InvenTree left maintenance mode')
        if get_maintenance_mode():

            logger.warning('Mainentance was still on - releasing now')
            set_maintenance_mode(False)
            logger.info('Released out of maintenance')

        # We should be current now - triggering full reload to make sure all models
        # are loaded fully in their new state.
        registry.reload_plugins(full_reload=True)
