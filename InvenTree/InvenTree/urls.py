"""Top-level URL lookup for InvenTree application.

Passes URL lookup downstream to each app as required.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.base import RedirectView

from dj_rest_auth.registration.views import (
    ConfirmEmailView,
    SocialAccountDisconnectView,
    SocialAccountListView,
)
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView
from sesame.views import LoginView

import build.api
import common.api
import company.api
import label.api
import machine.api
import order.api
import part.api
import plugin.api
import report.api
import stock.api
import users.api
from build.urls import build_urls
from common.urls import common_urls
from company.urls import company_urls, manufacturer_part_urls, supplier_part_urls
from order.urls import order_urls
from part.urls import part_urls
from plugin.urls import get_plugin_urls
from stock.urls import stock_urls
from web.urls import api_urls as web_api_urls
from web.urls import urlpatterns as platform_urls

from .api import APISearchView, InfoView, NotFoundView, VersionTextView, VersionView
from .magic_login import GetSimpleLoginView
from .social_auth_urls import (
    EmailListView,
    EmailPrimaryView,
    EmailRemoveView,
    EmailVerifyView,
    SocialProviderListView,
    social_auth_urlpatterns,
)
from .views import (
    AboutView,
    AppearanceSelectView,
    CustomConnectionsView,
    CustomEmailView,
    CustomLoginView,
    CustomPasswordResetFromKeyView,
    CustomSessionDeleteOtherView,
    CustomSessionDeleteView,
    DatabaseStatsView,
    DynamicJsView,
    EditUserView,
    IndexView,
    NotificationsView,
    SearchView,
    SetPasswordView,
    SettingsView,
    auth_request,
)

admin.site.site_header = 'InvenTree Admin'


apipatterns = [
    # Global search
    path('search/', APISearchView.as_view(), name='api-search'),
    path('settings/', include(common.api.settings_api_urls)),
    path('part/', include(part.api.part_api_urls)),
    path('bom/', include(part.api.bom_api_urls)),
    path('company/', include(company.api.company_api_urls)),
    path('stock/', include(stock.api.stock_api_urls)),
    path('build/', include(build.api.build_api_urls)),
    path('order/', include(order.api.order_api_urls)),
    path('label/', include(label.api.label_api_urls)),
    path('report/', include(report.api.report_api_urls)),
    path('machine/', include(machine.api.machine_api_urls)),
    path('user/', include(users.api.user_urls)),
    path('admin/', include(common.api.admin_api_urls)),
    path('web/', include(web_api_urls)),
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
    path(
        'version-text', VersionTextView.as_view(), name='api-version-text'
    ),  # version text
    path('version/', VersionView.as_view(), name='api-version'),  # version info
    path('', InfoView.as_view(), name='api-inventree-info'),  # server info
    # Auth API endpoints
    path(
        'auth/',
        include([
            re_path(
                r'^registration/account-confirm-email/(?P<key>[-:\w]+)/$',
                ConfirmEmailView.as_view(),
                name='account_confirm_email',
            ),
            path('registration/', include('dj_rest_auth.registration.urls')),
            path(
                'providers/', SocialProviderListView.as_view(), name='social_providers'
            ),
            path(
                'emails/',
                include([
                    path(
                        '<int:pk>/',
                        include([
                            path(
                                'primary/',
                                EmailPrimaryView.as_view(),
                                name='email-primary',
                            ),
                            path(
                                'verify/',
                                EmailVerifyView.as_view(),
                                name='email-verify',
                            ),
                            path(
                                'remove/',
                                EmailRemoveView().as_view(),
                                name='email-remove',
                            ),
                        ]),
                    ),
                    path('', EmailListView.as_view(), name='email-list'),
                ]),
            ),
            path('social/', include(social_auth_urlpatterns)),
            path(
                'social/', SocialAccountListView.as_view(), name='social_account_list'
            ),
            path(
                'social/<int:pk>/disconnect/',
                SocialAccountDisconnectView.as_view(),
                name='social_account_disconnect',
            ),
            path('logout/', users.api.Logout.as_view(), name='api-logout'),
            path(
                'login-redirect/',
                users.api.LoginRedirect.as_view(),
                name='api-login-redirect',
            ),
            path('', include('dj_rest_auth.urls')),
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

settings_urls = [
    path('i18n/', include('django.conf.urls.i18n')),
    path('appearance/', AppearanceSelectView.as_view(), name='settings-appearance'),
    # Catch any other urls
    path(
        '',
        SettingsView.as_view(template_name='InvenTree/settings/settings.html'),
        name='settings',
    ),
]

notifications_urls = [
    # Catch any other urls
    path('', NotificationsView.as_view(), name='notifications')
]

# These javascript files are served "dynamically" - i.e. rendered on demand
dynamic_javascript_urls = [
    path(
        'calendar.js',
        DynamicJsView.as_view(template_name='js/dynamic/calendar.js'),
        name='calendar.js',
    ),
    path(
        'nav.js',
        DynamicJsView.as_view(template_name='js/dynamic/nav.js'),
        name='nav.js',
    ),
    path(
        'permissions.js',
        DynamicJsView.as_view(template_name='js/dynamic/permissions.js'),
        name='permissions.js',
    ),
    path(
        'settings.js',
        DynamicJsView.as_view(template_name='js/dynamic/settings.js'),
        name='settings.js',
    ),
]

# These javascript files are passed through the Django translation layer
translated_javascript_urls = [
    path(
        'api.js',
        DynamicJsView.as_view(template_name='js/translated/api.js'),
        name='api.js',
    ),
    path(
        'attachment.js',
        DynamicJsView.as_view(template_name='js/translated/attachment.js'),
        name='attachment.js',
    ),
    path(
        'barcode.js',
        DynamicJsView.as_view(template_name='js/translated/barcode.js'),
        name='barcode.js',
    ),
    path(
        'bom.js',
        DynamicJsView.as_view(template_name='js/translated/bom.js'),
        name='bom.js',
    ),
    path(
        'build.js',
        DynamicJsView.as_view(template_name='js/translated/build.js'),
        name='build.js',
    ),
    path(
        'charts.js',
        DynamicJsView.as_view(template_name='js/translated/charts.js'),
        name='charts.js',
    ),
    path(
        'company.js',
        DynamicJsView.as_view(template_name='js/translated/company.js'),
        name='company.js',
    ),
    path(
        'filters.js',
        DynamicJsView.as_view(template_name='js/translated/filters.js'),
        name='filters.js',
    ),
    path(
        'forms.js',
        DynamicJsView.as_view(template_name='js/translated/forms.js'),
        name='forms.js',
    ),
    path(
        'helpers.js',
        DynamicJsView.as_view(template_name='js/translated/helpers.js'),
        name='helpers.js',
    ),
    path(
        'index.js',
        DynamicJsView.as_view(template_name='js/translated/index.js'),
        name='index.js',
    ),
    path(
        'label.js',
        DynamicJsView.as_view(template_name='js/translated/label.js'),
        name='label.js',
    ),
    path(
        'model_renderers.js',
        DynamicJsView.as_view(template_name='js/translated/model_renderers.js'),
        name='model_renderers.js',
    ),
    path(
        'modals.js',
        DynamicJsView.as_view(template_name='js/translated/modals.js'),
        name='modals.js',
    ),
    path(
        'order.js',
        DynamicJsView.as_view(template_name='js/translated/order.js'),
        name='order.js',
    ),
    path(
        'part.js',
        DynamicJsView.as_view(template_name='js/translated/part.js'),
        name='part.js',
    ),
    path(
        'purchase_order.js',
        DynamicJsView.as_view(template_name='js/translated/purchase_order.js'),
        name='purchase_order.js',
    ),
    path(
        'return_order.js',
        DynamicJsView.as_view(template_name='js/translated/return_order.js'),
        name='return_order.js',
    ),
    path(
        'report.js',
        DynamicJsView.as_view(template_name='js/translated/report.js'),
        name='report.js',
    ),
    path(
        'sales_order.js',
        DynamicJsView.as_view(template_name='js/translated/sales_order.js'),
        name='sales_order.js',
    ),
    path(
        'search.js',
        DynamicJsView.as_view(template_name='js/translated/search.js'),
        name='search.js',
    ),
    path(
        'stock.js',
        DynamicJsView.as_view(template_name='js/translated/stock.js'),
        name='stock.js',
    ),
    path(
        'status_codes.js',
        DynamicJsView.as_view(template_name='js/translated/status_codes.js'),
        name='status_codes.js',
    ),
    path(
        'plugin.js',
        DynamicJsView.as_view(template_name='js/translated/plugin.js'),
        name='plugin.js',
    ),
    path(
        'pricing.js',
        DynamicJsView.as_view(template_name='js/translated/pricing.js'),
        name='pricing.js',
    ),
    path(
        'news.js',
        DynamicJsView.as_view(template_name='js/translated/news.js'),
        name='news.js',
    ),
    path(
        'tables.js',
        DynamicJsView.as_view(template_name='js/translated/tables.js'),
        name='tables.js',
    ),
    path(
        'table_filters.js',
        DynamicJsView.as_view(template_name='js/translated/table_filters.js'),
        name='table_filters.js',
    ),
    path(
        'notification.js',
        DynamicJsView.as_view(template_name='js/translated/notification.js'),
        name='notification.js',
    ),
]

backendpatterns = [
    # "Dynamic" javascript files which are rendered using InvenTree templating.
    path('js/dynamic/', include(dynamic_javascript_urls)),
    path('js/i18n/', include(translated_javascript_urls)),
    path('auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('auth/', auth_request),
    path('api/', include(apipatterns)),
    path('api-doc/', SpectacularRedocView.as_view(url_name='schema'), name='api-doc'),
]

classic_frontendpatterns = [
    # Apps
    path('build/', include(build_urls)),
    path('common/', include(common_urls)),
    path('company/', include(company_urls)),
    path('order/', include(order_urls)),
    path('manufacturer-part/', include(manufacturer_part_urls)),
    path('part/', include(part_urls)),
    path('stock/', include(stock_urls)),
    path('supplier-part/', include(supplier_part_urls)),
    path('edit-user/', EditUserView.as_view(), name='edit-user'),
    path('set-password/', SetPasswordView.as_view(), name='set-password'),
    path('index/', IndexView.as_view(), name='index'),
    path('notifications/', include(notifications_urls)),
    path('search/', SearchView.as_view(), name='search'),
    path('settings/', include(settings_urls)),
    path('about/', AboutView.as_view(), name='about'),
    path('stats/', DatabaseStatsView.as_view(), name='stats'),
    # DB user sessions
    path(
        'accounts/sessions/other/delete/',
        view=CustomSessionDeleteOtherView.as_view(),
        name='session_delete_other',
    ),
    re_path(
        r'^accounts/sessions/(?P<pk>\w+)/delete/$',
        view=CustomSessionDeleteView.as_view(),
        name='session_delete',
    ),
    # Single Sign On / allauth
    # overrides of urlpatterns
    path('accounts/email/', CustomEmailView.as_view(), name='account_email'),
    path(
        'accounts/social/connections/',
        CustomConnectionsView.as_view(),
        name='socialaccount_connections',
    ),
    re_path(
        r'^accounts/password/reset/key/(?P<uidb36>[0-9A-Za-z]+)-(?P<key>.+)/$',
        CustomPasswordResetFromKeyView.as_view(),
        name='account_reset_password_from_key',
    ),
    # Override login page
    path('accounts/login/', CustomLoginView.as_view(), name='account_login'),
    path('accounts/', include('allauth_2fa.urls')),  # MFA support
    path('accounts/', include('allauth.urls')),  # included urlpatterns
]

urlpatterns = []

if settings.INVENTREE_ADMIN_ENABLED:
    admin_url = (settings.INVENTREE_ADMIN_URL,)
    urlpatterns += [
        path(f'{admin_url}/error_log/', include('error_report.urls')),
        path(f'{admin_url}/', admin.site.urls, name='inventree-admin'),
    ]

urlpatterns += backendpatterns

frontendpatterns = []

if settings.ENABLE_CLASSIC_FRONTEND:
    frontendpatterns += classic_frontendpatterns
if settings.ENABLE_PLATFORM_FRONTEND:
    frontendpatterns += platform_urls

urlpatterns += frontendpatterns

# Append custom plugin URLs (if plugin support is enabled)
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

# Send any unknown URLs to the parts page
urlpatterns += [
    re_path(r'^.*$', RedirectView.as_view(url='/index/', permanent=False), name='index')
]
