"""App configuration class for the 'users' app."""

from django.apps import AppConfig
from django.db.utils import OperationalError, ProgrammingError

import structlog

import InvenTree.ready

logger = structlog.get_logger('inventree')


class UsersConfig(AppConfig):
    """Config class for the 'users' app."""

    name = 'users'

    def ready(self):
        """Called when the 'users' app is loaded at runtime."""
        # skip loading if plugin registry is not loaded or we run in a background thread
        if (
            not InvenTree.ready.isPluginRegistryLoaded()
            or not InvenTree.ready.isInMainThread()
        ):
            return

        # Skip if running migrations
        if InvenTree.ready.isRunningMigrations():
            return  # pragma: no cover

        if InvenTree.ready.canAppAccessDatabase(allow_test=True):
            try:
                from users.tasks import rebuild_all_permissions

                rebuild_all_permissions()
            except (OperationalError, ProgrammingError):
                pass

            try:
                self.update_owners()
            except (OperationalError, ProgrammingError):
                pass

    def update_owners(self):
        """Create an 'owner' object for each user and group instance."""
        from django.contrib.auth import get_user_model
        from django.contrib.auth.models import Group

        from users.models import Owner

        # Create group owners
        for group in Group.objects.all():
            Owner.create(group)

        # Create user owners
        for user in get_user_model().objects.all():
            Owner.create(user)
