"""API endpoints for social authentication with allauth."""
import logging
from importlib import import_module

from django.urls import include, path

from allauth.socialaccount import providers
from allauth.socialaccount.providers.oauth2.views import (OAuth2Adapter,
                                                          OAuth2LoginView)

logger = logging.getLogger('inventree')


class GenericOAuth2ApiLoginView(OAuth2LoginView):
    """Api view to login a user with a social account"""
    def dispatch(self, request, *args, **kwargs):
        """Dispatch the regular login view directly."""
        return self.login(request, *args, **kwargs)


class GenericOAuth2ApiConnectView(GenericOAuth2ApiLoginView):
    """Api view to connect a social account to the current user"""

    def dispatch(self, request, *args, **kwargs):
        """Dispatch the connect request directly."""

        # Override the request method be in connection mode
        request.GET = request.GET.copy()
        request.GET['process'] = 'connect'

        # Resume the dispatch
        return super().dispatch(request, *args, **kwargs)


def handle_oauth2():
    """Define urls for oauth2 endpoints."""
    return [
        path('login/', GenericOAuth2ApiLoginView.adapter_view(adapter), name=f'{provider.id}_api_login'),
        path('connect/', GenericOAuth2ApiConnectView.adapter_view(adapter), name=f'{provider.id}_api_connet'),
    ]


# Collect urls for all loaded providers
social_auth_urlpatterns = []

provider_urlpatterns = []
for provider in providers.registry.get_list():
    try:
        prov_mod = import_module(provider.get_package() + ".views")
    except ImportError:
        continue

    # Try to extract the adapter class
    adapters = [cls for cls in prov_mod.__dict__.values() if isinstance(cls, type) and not cls == OAuth2Adapter and issubclass(cls, OAuth2Adapter)]
    if len(adapters) != 1:
        logger.error(f'Found handler that is not yet ready for platform UI: `{provider.id}`. Open an feature request on GitHub if you need it implemented.')
        continue
    adapter = adapters[0]
    provider_urlpatterns += [path(f'{provider.id}/', include(handle_oauth2()))]


social_auth_urlpatterns += provider_urlpatterns
