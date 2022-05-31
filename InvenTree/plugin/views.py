import logging
import sys
import traceback

from django.conf import settings
from django.views.debug import ExceptionReporter

from error_report.models import Error

from plugin.registry import registry

logger = logging.getLogger('inventree')


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

        for plug in registry.with_mixin('panel', active=True):

            try:
                panels += plug.render_panels(self, self.request, ctx)
            except Exception:
                # Prevent any plugin error from crashing the page render
                kind, info, data = sys.exc_info()

                # Log the error to the database
                Error.objects.create(
                    kind=kind.__name__,
                    info=info,
                    data='\n'.join(traceback.format_exception(kind, info, data)),
                    path=self.request.path,
                    html=ExceptionReporter(self.request, kind, info, data).get_traceback_html(),
                )

                logger.error(f"Plugin '{plug.slug}' could not render custom panels at '{self.request.path}'")

        return panels

    def get_context_data(self, **kwargs):
        """
        Add plugin context data to the view
        """

        ctx = super().get_context_data(**kwargs)

        if settings.PLUGINS_ENABLED:
            ctx['plugin_panels'] = self.get_plugin_panels(ctx)

        return ctx
