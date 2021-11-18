"""
URL lookup for plugin app
"""
from django.conf import settings


PLUGIN_BASE = 'plugin'  # Constant for links


def get_integration_urls():
    urls = []
    for plugin in settings.INTEGRATION_PLUGINS.values():
        if plugin.mixin_enabled('urls'):
            urls.append(plugin.urlpatterns)
    return urls


plugin_urls = [
]
