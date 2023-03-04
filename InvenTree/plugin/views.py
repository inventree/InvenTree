"""Views for plugin app."""

import logging

from django.conf import settings

from InvenTree.exceptions import log_error
from plugin.registry import registry

logger = logging.getLogger('inventree')


class InvenTreePluginViewMixin:
    """Custom view mixin which adds context data to the view, based on loaded plugins.

    This allows rendered pages to be augmented by loaded plugins.
    """

    def get_plugin_panels(self, ctx):
        """Return a list of extra 'plugin panels' associated with this view."""
        panels = []

        for plug in registry.with_mixin('panel', active=True):

            try:
                panels += plug.render_panels(self, self.request, ctx)
            except Exception:
                # Log the error to the database
                log_error(self.request.path)
                logger.error(f"Plugin '{plug.slug}' could not render custom panels at '{self.request.path}'")

        return panels

    def get_context_data(self, **kwargs):
        """Add plugin context data to the view."""
        ctx = super().get_context_data(**kwargs)

        if settings.PLUGINS_ENABLED:
            ctx['plugin_panels'] = self.get_plugin_panels(ctx)

        return ctx
