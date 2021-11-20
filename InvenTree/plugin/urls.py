"""
URL lookup for plugin app
"""
from django.conf import settings
from django.conf.urls import url, include


PLUGIN_BASE = 'plugin'  # Constant for links


def get_integration_urls():
    """returns a urlpattern that can be integrated into the global urls"""
    urls = []
    for plugin in settings.INTEGRATION_PLUGINS.values():
        if plugin.mixin_enabled('urls'):
            urls.append(plugin.urlpatterns)
    return url(f'^{PLUGIN_BASE}/', include((urls, 'plugin')))


plugin_urls = [
]
