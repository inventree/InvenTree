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
        if not InvenTree.ready.canAppAccessDatabase():  # pragma: no cover
            return
        from web.models import collect_guides  # pragma: no cover

        collect_guides(create=True)  # Preload guide definitions  # pragma: no cover
