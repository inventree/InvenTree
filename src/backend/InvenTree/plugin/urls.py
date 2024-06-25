"""URL lookup for plugin app."""

from django.conf import settings
from django.urls import include, re_path

from common.validators import get_global_setting

PLUGIN_BASE = 'plugin'  # Constant for links


def get_plugin_urls():
    """Returns a urlpattern that can be integrated into the global urls."""
    from plugin.registry import registry

    urls = []

    if get_global_setting('ENABLE_PLUGINS_URL', False) or settings.PLUGIN_TESTING_SETUP:
        for plugin in registry.plugins.values():
            if plugin.mixin_enabled('urls'):
                urls.append(plugin.urlpatterns)

    return re_path(f'^{PLUGIN_BASE}/', include((urls, 'plugin')))
