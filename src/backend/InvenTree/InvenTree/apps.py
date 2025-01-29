"""AppConfig for InvenTree app."""

from importlib import import_module
from pathlib import Path

from django.apps import AppConfig, apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import AppRegistryNotReady
from django.db import transaction
from django.db.utils import IntegrityError, OperationalError

import structlog
from allauth.socialaccount.signals import social_account_updated

import InvenTree.conversion
import InvenTree.ready
import InvenTree.tasks
from common.settings import get_global_setting, set_global_setting
from InvenTree.config import get_setting

logger = structlog.get_logger('inventree')


class InvenTreeConfig(AppConfig):
    """AppConfig for inventree app."""

    name = 'InvenTree'

    def ready(self):
        """Run system wide setup init steps.

        Like:
        - Checking if migrations should be run
        - Cleaning up tasks
        - Starting regular tasks
        - Updating exchange rates
        - Collecting notification methods
        - Collecting state transition methods
        - Adding users set in the current environment
        """
        # skip loading if plugin registry is not loaded or we run in a background thread

        if not InvenTree.ready.isPluginRegistryLoaded():
            return

        # Skip if not in worker or main thread
        if (
            not InvenTree.ready.isInMainThread()
            and not InvenTree.ready.isInWorkerThread()
        ):
            return

        # Skip if running migrations
        if InvenTree.ready.isRunningMigrations():
            return

        if InvenTree.ready.canAppAccessDatabase() or settings.TESTING_ENV:
            self.remove_obsolete_tasks()
            self.collect_tasks()
            self.start_background_tasks()

            if not InvenTree.ready.isInTestMode():  # pragma: no cover
                self.update_exchange_rates()
                # Let the background worker check for migrations
                InvenTree.tasks.offload_task(InvenTree.tasks.check_for_migrations)

        self.update_site_url()
        self.collect_notification_methods()
        self.collect_state_transition_methods()

        # Ensure the unit registry is loaded
        InvenTree.conversion.get_unit_registry()

        if InvenTree.ready.canAppAccessDatabase() or settings.TESTING_ENV:
            self.add_user_on_startup()
            self.add_user_from_file()

        # register event receiver and connect signal for SSO group sync. The connected signal is
        # used for account updates whereas the receiver is used for the initial account creation.
        from InvenTree import sso

        social_account_updated.connect(sso.ensure_sso_groups)

    def remove_obsolete_tasks(self):
        """Delete any obsolete scheduled tasks in the database."""
        obsolete = [
            'InvenTree.tasks.delete_expired_sessions',
            'stock.tasks.delete_old_stock_items',
            'label.tasks.cleanup_old_label_outputs',
        ]

        try:
            from django_q.models import Schedule
        except AppRegistryNotReady:  # pragma: no cover
            return

        # Remove any existing obsolete tasks
        try:
            obsolete_tasks = Schedule.objects.filter(func__in=obsolete)

            if obsolete_tasks.exists():
                logger.info(
                    'Removing %s obsolete background tasks', obsolete_tasks.count()
                )
                obsolete_tasks.delete()

        except Exception:
            logger.exception('Failed to remove obsolete tasks - database not ready')

    def start_background_tasks(self):
        """Start all background tests for InvenTree."""
        logger.info('Starting background tasks...')

        from django_q.models import Schedule

        # List of existing scheduled tasks (in the database)
        existing_tasks = {}

        for existing_task in Schedule.objects.all():
            existing_tasks[existing_task.func] = existing_task

        tasks_to_create = []
        tasks_to_update = []

        # List of collected tasks found with the @scheduled_task decorator
        tasks = InvenTree.tasks.tasks.task_list

        for task in tasks:
            ref_name = f'{task.func.__module__}.{task.func.__name__}'

            if ref_name in existing_tasks:
                # This task already exists - update the details if required
                existing_task = existing_tasks[ref_name]

                if (
                    existing_task.schedule_type != task.interval
                    or existing_task.minutes != task.minutes
                ):
                    existing_task.schedule_type = task.interval
                    existing_task.minutes = task.minutes
                    tasks_to_update.append(existing_task)

            else:
                # This task does *not* already exist - create it
                tasks_to_create.append(
                    Schedule(
                        name=ref_name,
                        func=ref_name,
                        schedule_type=task.interval,
                        minutes=task.minutes,
                    )
                )

        if len(tasks_to_create) > 0:
            Schedule.objects.bulk_create(tasks_to_create)
            logger.info('Created %s new scheduled tasks', len(tasks_to_create))

        if len(tasks_to_update) > 0:
            Schedule.objects.bulk_update(tasks_to_update, ['schedule_type', 'minutes'])
            logger.info('Updated %s existing scheduled tasks', len(tasks_to_update))

        self.add_heartbeat()

        logger.info('Started %s scheduled background tasks...', len(tasks))

    def add_heartbeat(self):
        """Ensure there is at least one background task in the queue."""
        import django_q.models

        try:
            if django_q.models.OrmQ.objects.count() == 0:
                InvenTree.tasks.offload_task(
                    InvenTree.tasks.heartbeat, force_async=True
                )
        except Exception:
            pass

    def collect_tasks(self):
        """Collect all background tasks."""
        for app_name, app in apps.app_configs.items():
            if app_name == 'InvenTree':
                continue

            if Path(app.path).joinpath('tasks.py').exists():
                try:
                    import_module(f'{app.module.__package__}.tasks')
                except Exception as e:  # pragma: no cover
                    logger.exception('Error loading tasks for %s: %s', app_name, e)

    def update_exchange_rates(self):  # pragma: no cover
        """Update exchange rates each time the server is started.

        Only runs *if*:
        a) Have not been updated recently (one day or less)
        b) The base exchange rate has been altered
        """
        try:
            from djmoney.contrib.exchange.models import ExchangeBackend

            from common.currency import currency_code_default
            from InvenTree.tasks import update_exchange_rates
        except AppRegistryNotReady:  # pragma: no cover
            pass

        base_currency = currency_code_default()

        update = False

        try:
            backend = ExchangeBackend.objects.filter(name='InvenTreeExchange')

            if backend.exists():
                backend = backend.first()

                last_update = backend.last_update

                if last_update is None:
                    # Never been updated
                    logger.info('Exchange backend has never been updated')
                    update = True

                # Backend currency has changed?
                if base_currency != backend.base_currency:
                    logger.info(
                        'Base currency changed from %s to %s',
                        backend.base_currency,
                        base_currency,
                    )
                    update = True

        except ExchangeBackend.DoesNotExist:
            logger.info('Exchange backend not found - updating')
            update = True

        except Exception:
            # Some other error - potentially the tables are not ready yet
            return

        if update:
            try:
                update_exchange_rates()
            except OperationalError:
                logger.warning('Could not update exchange rates - database not ready')
            except Exception as e:
                logger.exception('Error updating exchange rates: %s (%s)', e, type(e))

    def update_site_url(self):
        """Update the site URL setting.

        - If a fixed SITE_URL is specified (via configuration), it should override the INVENTREE_BASE_URL setting
        - If multi-site support is enabled, update the site URL for the current site
        """
        if not InvenTree.ready.canAppAccessDatabase():
            return

        if InvenTree.ready.isImportingData() or InvenTree.ready.isRunningMigrations():
            return

        if settings.SITE_URL:
            try:
                if get_global_setting('INVENTREE_BASE_URL') != settings.SITE_URL:
                    set_global_setting('INVENTREE_BASE_URL', settings.SITE_URL)
                    logger.info('Updated INVENTREE_SITE_URL to %s', settings.SITE_URL)
            except Exception:
                pass

            # If multi-site support is enabled, update the site URL for the current site
            try:
                from django.contrib.sites.models import Site

                site = Site.objects.get_current()
                site.domain = settings.SITE_URL
                site.save()

                logger.info('Updated current site URL to %s', settings.SITE_URL)

            except Exception:
                pass

    def add_user_on_startup(self):
        """Add a user on startup."""
        # stop if checks were already created
        if hasattr(settings, 'USER_ADDED') and settings.USER_ADDED:
            return

        # get values
        add_user = get_setting('INVENTREE_ADMIN_USER', 'admin_user')
        add_email = get_setting('INVENTREE_ADMIN_EMAIL', 'admin_email')
        add_password = get_setting('INVENTREE_ADMIN_PASSWORD', 'admin_password')
        add_password_file = get_setting(
            'INVENTREE_ADMIN_PASSWORD_FILE', 'admin_password_file', None
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
            settings.USER_ADDED = True

            # if a password file is present, do not warn - will be handled later
            if add_password_file:
                return
            logger.warning(
                'Not all required settings for adding a user on startup are present:\nINVENTREE_ADMIN_USER, INVENTREE_ADMIN_EMAIL, INVENTREE_ADMIN_PASSWORD'
            )
            return

        # good to go -> create user
        self._create_admin_user(add_user, add_email, add_password)

        # do not try again
        settings.USER_ADDED = True

    def _create_admin_user(self, add_user, add_email, add_password):
        user = get_user_model()
        try:
            with transaction.atomic():
                if user.objects.filter(username=add_user).exists():
                    logger.info('User %s already exists - skipping creation', add_user)
                else:
                    new_user = user.objects.create_superuser(
                        add_user, add_email, add_password
                    )
                    logger.info('User %s was created!', str(new_user))
        except IntegrityError:
            logger.warning('The user "%s" could not be created', add_user)

    def add_user_from_file(self):
        """Add the superuser from a file."""
        # stop if checks were already created
        if hasattr(settings, 'USER_ADDED_FILE') and settings.USER_ADDED_FILE:
            return

        # get values
        add_password_file = get_setting(
            'INVENTREE_ADMIN_PASSWORD_FILE', 'admin_password_file', None
        )

        # no variable set -> do not try anything
        if not add_password_file:
            settings.USER_ADDED_FILE = True
            return

        # check if file exists
        add_password_file = Path(str(add_password_file))
        if not add_password_file.exists():
            logger.warning('The file "%s" does not exist', add_password_file)
            settings.USER_ADDED_FILE = True
            return

        # good to go -> create user
        self._create_admin_user(
            get_setting('INVENTREE_ADMIN_USER', 'admin_user', 'admin'),
            get_setting('INVENTREE_ADMIN_EMAIL', 'admin_email', ''),
            add_password_file.read_text(encoding='utf-8'),
        )

        # do not try again
        settings.USER_ADDED_FILE = True

    def collect_notification_methods(self):
        """Collect all notification methods."""
        from common.notifications import storage

        storage.collect()

    def collect_state_transition_methods(self):
        """Collect all state transition methods."""
        from generic.states import storage

        storage.collect()
