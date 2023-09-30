"""Helper functions for managing database migration"""

import logging

from django.core.management import call_command
from django.db import DEFAULT_DB_ALIAS, connections, transaction
from django.db.migrations.executor import MigrationExecutor

from maintenance_mode.core import set_maintenance_mode

from InvenTree.config import get_setting

logger = logging.getLogger('inventree')


def set_pending_migration_flag(pending: bool) -> None:
    """Update the pending migration flag in the database"""

    import common.models

    common.models.InvenTreeSetting.set_setting('PENDING_DB_MIGRATIONS', pending, None)


def get_migration_plan():
    """Returns a list of migrations which are needed to be run."""
    executor = MigrationExecutor(connections[DEFAULT_DB_ALIAS])
    plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
    return plan


def run_pending_migrations():
    """Run any pending database migrations.

    Note that if the auto-update configuration flag is set to False,
    then the migrations will *not* be run (but the pending migration flag will be set)
    """

    from plugin import registry

    logger.info("Checking for pending database migrations")

    # Check if plugins need to be reloaded first
    registry.check_reload()

    plan = get_migration_plan()

    if not plan:
        logger.info("No pending migrations!")
        set_pending_migration_flag(False)
        return

    # There are some migrations to run
    logger.info("There are %d pending migrations:", len(plan))

    set_pending_migration_flag(True)

    auto_reload = get_setting('INVENTREE_AUTO_UPDATE', 'auto_update', default_value=True)

    if not auto_reload:
        logger.info("Auto-update is disabled - skipping migrations")
        return

    for migration in plan:
        logger.info(" - %s", migration[0])

    set_maintenance_mode(True)

    reload = False

    with transaction.atomic():
        try:
            call_command('migrate', interactive=False)
            reload = True

        except Exception as exc:
            logger.exception("Error running migrations: %s", str(exc))

        # Clear flag for pending migrations
        set_pending_migration_flag(False)

    # Ensure maintenance mode is *off*
    set_maintenance_mode(False)

    if reload:
        registry.reload_plugins(full_reload=True, force_reload=True)
