"""API endpoints for social authentication with allauth."""
import logging
from importlib import import_module

from django.urls import include, path, reverse

from allauth.socialaccount import providers
from allauth.socialaccount.models import SocialApp
from allauth.socialaccount.providers.keycloak.views import \
    KeycloakOAuth2Adapter
from allauth.socialaccount.providers.oauth2.views import (OAuth2Adapter,
                                                          OAuth2LoginView)
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from common.models import InvenTreeSetting

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
        path('connect/', GenericOAuth2ApiConnectView.adapter_view(adapter), name=f'{provider.id}_api_connect'),
    ]


def handle_keycloak():
    """Define urls for keycloak."""
    return [
        path('login/', GenericOAuth2ApiLoginView.adapter_view(KeycloakOAuth2Adapter), name='keycloak_api_login'),
        path('connect/', GenericOAuth2ApiConnectView.adapter_view(KeycloakOAuth2Adapter), name='keycloak_api_connet'),
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


class SocialProvierListView(ListAPIView):
    """List of available social providers."""
    permission_classes = (AllowAny,)

    def get(self, request, *args, **kwargs):
        """Get the list of providers."""
        provider_list = []
        for provider in providers.registry.get_list():
            provider_data = {
                'id': provider.id,
                'name': provider.name,
                'login': request.build_absolute_uri(reverse(f'{provider.id}_api_login')),
                'connect': request.build_absolute_uri(reverse(f'{provider.id}_api_connect')),
            }
            try:
                provider_data['display_name'] = provider.get_app(request).name
            except SocialApp.DoesNotExist:
                provider_data['display_name'] = provider.name

            provider_list.append(provider_data)

        data = {
            'sso_enabled': InvenTreeSetting.get_setting('LOGIN_ENABLE_SSO'),
            'sso_registration': InvenTreeSetting.get_setting('LOGIN_ENABLE_SSO_REG'),
            'mfa_required': InvenTreeSetting.get_setting('LOGIN_ENFORCE_MFA'),
            'providers': provider_list
        }
        return Response(data)
