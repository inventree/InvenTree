"""Sample implementations for SampleAppIntegrationPlugin."""

from django.urls import include, path

from plugin import InvenTreePlugin
from plugin.mixins import AppMixin, UrlsMixin

from .api import api_patterns


class SampleAppIntegrationPlugin(AppMixin, UrlsMixin, InvenTreePlugin):
    """A app plugin example."""

    NAME = 'SampleAppIntegrationPlugin'
    SLUG = 'app_sample_plugin'
    TITLE = 'Sample App Plugin'

    def setup_urls(self):
        """Urls that are exposed by this plugin."""
        # from .api import api_patterns

        urls = [path('api/', include(api_patterns))]
        return urls
