"""URL lookup for plugin app."""

from django.conf import settings
from django.urls import include, re_path
from django.urls.exceptions import Resolver404
from django.views.generic.base import RedirectView

from common.validators import get_global_setting
from InvenTree.exceptions import log_error
from plugin import PluginMixinEnum

PLUGIN_BASE = 'plugin'  # Constant for links


def get_plugin_urls():
    """Returns a urlpattern that can be integrated into the global urls."""
    from plugin.registry import registry

    urls = []

    if registry.is_ready:
        if (
            get_global_setting('ENABLE_PLUGINS_URL', False)
            or settings.PLUGIN_TESTING_SETUP
        ):
            for plugin in registry.with_mixin(PluginMixinEnum.URLS):
                try:
                    if plugin_urls := plugin.urlpatterns:
                        # Check if the plugin has a custom URL pattern
                        for url in plugin_urls:
                            # Attempt to resolve against the URL pattern as a validation check
                            try:
                                url.resolve('')
                            except Resolver404:
                                pass

                        urls.append(
                            re_path(
                                f'^{plugin.slug}/',
                                include((plugin_urls, plugin.slug)),
                                name=plugin.slug,
                            )
                        )
                except Exception:
                    log_error('get_plugin_urls', plugin=plugin.slug)
                    continue

    # Redirect anything else to the root index
    urls.append(
        re_path(
            r'^.*$',
            RedirectView.as_view(url=f'/{settings.FRONTEND_URL_BASE}', permanent=False),
            name='index',
        )
    )

    return re_path(f'^{PLUGIN_BASE}/', include((urls, 'plugin')))
