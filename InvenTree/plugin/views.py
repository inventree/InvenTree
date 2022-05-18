
from django.conf import settings

from plugin.registry import registry


class InvenTreePluginViewMixin:
    """
    Custom view mixin which adds context data to the view,
    based on loaded plugins.

    This allows rendered pages to be augmented by loaded plugins.

    """

    def get_plugin_panels(self, ctx):
        """
        Return a list of extra 'plugin panels' associated with this view
        """

        panels = []

        for plug in registry.with_mixin('panel'):
            panels += plug.render_panels(self, self.request, ctx)

        return panels

    def get_context_data(self, **kwargs):
        """
        Add plugin context data to the view
        """

        ctx = super().get_context_data(**kwargs)

        if settings.PLUGINS_ENABLED:
            ctx['plugin_panels'] = self.get_plugin_panels(ctx)

        return ctx
