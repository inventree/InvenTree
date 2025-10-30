"""App config for "web" app."""

from django.apps import AppConfig

import structlog

import InvenTree.ready

logger = structlog.get_logger('inventree')


class WebConfig(AppConfig):
    """AppConfig for web app."""

    name = 'web'

    def ready(self):
        """Initialize restart flag clearance on startup."""
        if InvenTree.ready.isRunningMigrations():  # pragma: no cover
            return
        from web.models import collect_guides

        collect_guides(create=True)  # Preload guide definitions
