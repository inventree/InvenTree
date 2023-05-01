"""URL lookup for plugin app."""

from django.urls import include, re_path

PLUGIN_BASE = 'plugin'  # Constant for links


def get_plugin_urls():
    """Returns a urlpattern that can be integrated into the global urls."""
    from plugin import registry

    urls = []

    for plugin in registry.plugins.values():
        if plugin.mixin_enabled('urls'):
            urls.append(plugin.urlpatterns)

    return re_path(f'^{PLUGIN_BASE}/', include((urls, 'plugin')))
