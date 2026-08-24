"""URL lookup for plugin app."""

from django.conf import settings
from django.http import JsonResponse
from django.urls import include, path, re_path
from django.urls.exceptions import Resolver404
from django.views.decorators.http import require_http_methods
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


@require_http_methods(['GET'])
def wellknownindexview(request):
    """Simple view that returns a list of all well-known URLs as JSON."""
    from plugin.registry import registry

    well_known_urls = {}
    if registry.is_ready:
        for plugin in registry.with_mixin(PluginMixinEnum.WELLKNOWN):
            try:
                if urls := plugin.get_well_known_urls(request):
                    for name, url in urls:
                        well_known_urls[name] = request.build_absolute_uri(url)
            except Exception:
                log_error('WellKnownView', plugin=plugin.slug)
                continue

    return JsonResponse({'well_known_urls': well_known_urls})


def get_wellknown_urls():
    """Returns a urlpattern that can be integrated into the global urls (as redirects)."""
    from plugin.registry import registry

    urls = []

    if registry.is_ready:
        for plugin in registry.with_mixin(PluginMixinEnum.WELLKNOWN):
            try:
                if well_known_urls := plugin.get_well_known_urls(request=None):
                    for name, url in well_known_urls:
                        urls.append(
                            path(
                                name,
                                RedirectView.as_view(url=url, permanent=False),
                                name=name,
                            )
                        )
                        urls.append(
                            re_path(
                                f'^{name}/.*$',
                                RedirectView.as_view(url=url, permanent=False),
                                name=name,
                            )
                        )
            except Exception:
                log_error('get_wellknown_urls', plugin=plugin.slug)
                continue

    # Add index page that lists all well-known URLs
    urls.append(path('', wellknownindexview, name='index'))

    return path('.well-known/', include((urls, 'well-known')))
