"""Top-level URL lookup for InvenTree application.

Passes URL lookup downstream to each app as required.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.base import RedirectView

from allauth.headless.urls import Client, build_urlpatterns
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView
from flags.urls import flagged_path
from oauth2_provider import urls as oauth2_urls
from sesame.views import LoginView

import build.api
import common.api
import company.api
import importer.api
import machine.api
import order.api
import part.api
import plugin.api
import report.api
import stock.api
import users.api
from plugin.urls import get_plugin_urls
from web.urls import cui_compatibility_urls
from web.urls import urlpatterns as platform_urls

from .api import (
    APISearchView,
    InfoView,
    LicenseView,
    NotFoundView,
    VersionTextView,
    VersionView,
)
from .config import get_setting
from .magic_login import GetSimpleLoginView
from .views import auth_request

# Set admin header from config or use default
admin.site.site_header = get_setting(
    'INVENTREE_SITE_HEADER', 'customize.site_header', 'InvenTree Admin'
)


apipatterns = [
    # Global search
    path('admin/', include(common.api.admin_api_urls)),
    path('bom/', include(part.api.bom_api_urls)),
    path('build/', include(build.api.build_api_urls)),
    path('company/', include(company.api.company_api_urls)),
    path('importer/', include(importer.api.importer_api_urls)),
    path('label/', include(report.api.label_api_urls)),
    path('machine/', include(machine.api.machine_api_urls)),
    path('order/', include(order.api.order_api_urls)),
    path('part/', include(part.api.part_api_urls)),
    path('report/', include(report.api.report_api_urls)),
    path('search/', APISearchView.as_view(), name='api-search'),
    path('settings/', include(common.api.settings_api_urls)),
    path('stock/', include(stock.api.stock_api_urls)),
    path(
        'generate/',
        include([
            path(
                'batch-code/',
                stock.api.GenerateBatchCode.as_view(),
                name='api-generate-batch-code',
            ),
            path(
                'serial-number/',
                stock.api.GenerateSerialNumber.as_view(),
                name='api-generate-serial-number',
            ),
        ]),
    ),
    path('user/', include(users.api.user_urls)),
    # Plugin endpoints
    path('', include(plugin.api.plugin_api_urls)),
    # Common endpoints endpoint
    path('', include(common.api.common_api_urls)),
    # OpenAPI Schema
    path(
        'schema/',
        SpectacularAPIView.as_view(custom_settings={'SCHEMA_PATH_PREFIX': '/api/'}),
        name='schema',
    ),
    # InvenTree information endpoints
    path('license/', LicenseView.as_view(), name='api-license'),  # license info
    path(
        'version-text', VersionTextView.as_view(), name='api-version-text'
    ),  # version text
    path('version/', VersionView.as_view(), name='api-version'),  # version info
    path('', InfoView.as_view(), name='api-inventree-info'),  # server info
    # Auth API endpoints
    path(
        'auth/',
        include([
            path(
                'login-redirect/',
                users.api.LoginRedirect.as_view(),
                name='api-login-redirect',
            ),
            path(
                '',
                include(
                    (build_urlpatterns(Client.BROWSER), 'headless'), namespace='browser'
                ),
            ),  # Allauth headless logic (only the browser client is included as we only use sessions based auth there)
        ]),
    ),
    # Magic login URLs
    path(
        'email/generate/',
        csrf_exempt(GetSimpleLoginView().as_view()),
        name='sesame-generate',
    ),
    path('email/login/', LoginView.as_view(), name='sesame-login'),
    # Unknown endpoint
    re_path(r'^.*$', NotFoundView.as_view(), name='api-404'),
]


backendpatterns = [
    path(
        'auth/', include('rest_framework.urls', namespace='rest_framework')
    ),  # Used for (DRF) browsable API auth
    path(
        'auth/', auth_request, name='auth-check'
    ),  # Used for proxies to check if user is authenticated
    path('accounts/', include('allauth.urls')),
    # OAuth2
    flagged_path('OIDC', 'o/', include(oauth2_urls)),
    path(
        'accounts/login/',
        RedirectView.as_view(url=f'/{settings.FRONTEND_URL_BASE}', permanent=False),
        name='account_login',
    ),  # Add a redirect for login views
    path('anymail/', include('anymail.urls')),  # Emails
]

urlpatterns = []

if settings.INVENTREE_ADMIN_ENABLED:
    admin_url = settings.INVENTREE_ADMIN_URL

    urlpatterns += [
        path(f'{admin_url}/error_log/', include('error_report.urls')),
        path(f'{admin_url}/doc/', include('django.contrib.admindocs.urls')),
        path(f'{admin_url}/', admin.site.urls, name='inventree-admin'),
    ]

urlpatterns += backendpatterns
urlpatterns += [  # API URLs
    path('api/', include(apipatterns)),
    path('api-doc/', SpectacularRedocView.as_view(url_name='schema'), name='api-doc'),
]
urlpatterns += platform_urls

# Append custom plugin URLs (if custom plugin support is enabled)
if settings.PLUGINS_ENABLED:
    urlpatterns.append(get_plugin_urls())

# Server running in "DEBUG" mode?
if settings.DEBUG:
    # Static file access
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

    # Media file access
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Redirect for favicon.ico
urlpatterns.append(
    path(
        'favicon.ico',
        RedirectView.as_view(url=f'{settings.STATIC_URL}img/favicon/favicon.ico'),
    )
)

# Compatibility layer for old (CUI) URLs
if settings.FRONTEND_SETTINGS.get('url_compatibility'):
    urlpatterns += cui_compatibility_urls(settings.FRONTEND_URL_BASE)

if settings.DJANGO_SILK_ENABLED:
    urlpatterns += [path('silk/', include('silk.urls', namespace='silk'))]

# Send any unknown URLs to the index page
urlpatterns += [
    re_path(
        r'^.*$',
        RedirectView.as_view(url=f'/{settings.FRONTEND_URL_BASE}', permanent=False),
        name='index',
    )
]
