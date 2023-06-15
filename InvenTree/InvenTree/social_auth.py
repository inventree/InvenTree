"""API endpoints for social authentication with allauth."""
import logging
from importlib import import_module

from django.urls import include, path

from allauth.socialaccount import providers
from allauth.socialaccount.providers.keycloak.views import \
    KeycloakOAuth2Adapter
from allauth.socialaccount.providers.oauth2.views import (OAuth2Adapter,
                                                          OAuth2LoginView)
from allauth.socialaccount.providers.twitter.views import TwitterOAuthAdapter
from dj_rest_auth.registration.views import SocialConnectView, SocialLoginView
from dj_rest_auth.social_serializers import (TwitterConnectSerializer,
                                             TwitterLoginSerializer)

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


def handle_oauth2(adapter: OAuth2Adapter):
    """Define urls for oauth2 endpoints."""
    return [
        path('login/', GenericOAuth2ApiLoginView.adapter_view(adapter), name=f'{provider.id}_api_login'),
        path('connect/', GenericOAuth2ApiConnectView.adapter_view(adapter), name=f'{provider.id}_api_connet'),
    ]


def handle_keycloak():
    """Define urls for keycloak."""
    return [
        path('login/', GenericOAuth2ApiLoginView.adapter_view(KeycloakOAuth2Adapter), name='keycloak_api_login'),
        path('connect/', GenericOAuth2ApiConnectView.adapter_view(KeycloakOAuth2Adapter), name='keycloak_api_connet'),
    ]


def handle_twitter():
    """Define urls for twitter."""
    class TwitterLogin(SocialLoginView):
        serializer_class = TwitterLoginSerializer
        adapter_class = TwitterOAuthAdapter

    class TwitterConnect(SocialConnectView):
        serializer_class = TwitterConnectSerializer
        adapter_class = TwitterOAuthAdapter

    return [
        path('login/', TwitterLogin.as_view(), name='twitter_api_login'),
        path('twitter/connect/', TwitterConnect.as_view(), name='twitter_api_connet'),
    ]


legacy = {
    'twitter': 'twitter_oauth2',
    'bitbucket': 'bitbucket_oauth2',
    'linkedin': 'linkedin_oauth2',
    'vimeo': 'vimeo_oauth2',
    'openid': 'openid_connect',
}  # legacy connectors


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

    # Get urls
    urls = []
    if len(adapters) == 1:
        urls = handle_oauth2(adapter=adapters[0])
    else:
        if provider.id in legacy:
            logger.warning(f'`{provider.id}` is not supported on platform UI. Use `{legacy[provider.id]}` instead.')
            continue
        elif provider.id == 'keycloak':
            urls = handle_keycloak()
        else:
            logger.error(f'Found handler that is not yet ready for platform UI: `{provider.id}`. Open an feature request on GitHub if you need it implemented.')
            continue
    provider_urlpatterns += [path(f'{provider.id}/', include(urls))]


social_auth_urlpatterns += provider_urlpatterns
