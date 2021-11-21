"""
URL lookup for plugin app
"""
from django.conf.urls import url, include

from plugin.helpers import get_plugin_error
from plugin import plugin_reg


PLUGIN_BASE = 'plugin'  # Constant for links


def get_plugin_urls():
    """returns a urlpattern that can be integrated into the global urls"""
    urls = []
    for plugin in plugin_reg.plugins.values():
        if plugin.mixin_enabled('urls'):
            urls.append(plugin.urlpatterns)
    # TODO wrap everything in plugin_url_wrapper
    return url(f'^{PLUGIN_BASE}/', include((urls, 'plugin')))
