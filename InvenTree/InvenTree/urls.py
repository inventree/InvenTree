"""Top-level URL lookup for InvenTree application.

Passes URL lookup downstream to each app as required.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path

from rest_framework.documentation import include_docs_urls

from build.api import build_api_urls
from common.api import common_api_urls, settings_api_urls
from company.api import company_api_urls
from label.api import label_api_urls
from order.api import order_api_urls
from part.api import bom_api_urls, part_api_urls
from plugin.api import plugin_api_urls
from plugin.urls import get_plugin_urls
from report.api import report_api_urls
from stock.api import stock_api_urls
from users.api import user_urls

from .api import InfoView, NotFoundView
from .views import (AboutView, AppearanceSelectView, CurrencyRefreshView,
                    CustomLoginView, CustomPasswordResetFromKeyView,
                    DatabaseStatsView, EditUserView, SetPasswordView,
                    auth_request)

admin.site.site_header = "InvenTree Admin"


apipatterns = [
    re_path(r'^settings/', include(settings_api_urls)),
    re_path(r'^part/', include(part_api_urls)),
    re_path(r'^bom/', include(bom_api_urls)),
    re_path(r'^company/', include(company_api_urls)),
    re_path(r'^stock/', include(stock_api_urls)),
    re_path(r'^build/', include(build_api_urls)),
    re_path(r'^order/', include(order_api_urls)),
    re_path(r'^label/', include(label_api_urls)),
    re_path(r'^report/', include(report_api_urls)),
    re_path(r'^user/', include(user_urls)),

    # Plugin endpoints
    path('', include(plugin_api_urls)),

    # Webhook enpoint
    path('', include(common_api_urls)),

    # InvenTree information endpoint
    path('', InfoView.as_view(), name='api-inventree-info'),

    # Unknown endpoint
    re_path(r'^.*$', NotFoundView.as_view(), name='api-404'),
]

settings_urls = [

    re_path(r'^i18n/?', include('django.conf.urls.i18n')),

    re_path(r'^appearance/?', AppearanceSelectView.as_view(), name='settings-appearance'),
    re_path(r'^currencies-refresh/', CurrencyRefreshView.as_view(), name='settings-currencies-refresh'),

]

backendpatterns = [
    re_path(r'^auth/', include('rest_framework.urls', namespace='rest_framework')),
    re_path(r'^auth/?', auth_request),

    re_path(r'^api/', include(apipatterns)),
    re_path(r'^api-doc/', include_docs_urls(title='InvenTree API')),
]

frontendpatterns = [
    re_path(r'^edit-user/', EditUserView.as_view(), name='edit-user'),
    re_path(r'^set-password/', SetPasswordView.as_view(), name='set-password'),

    re_path(r'^settings/', include(settings_urls)),
    re_path(r'^about/', AboutView.as_view(), name='about'),
    re_path(r'^stats/', DatabaseStatsView.as_view(), name='stats'),

    # admin sites
    re_path(f'^{settings.INVENTREE_ADMIN_URL}/error_log/', include('error_report.urls')),
    re_path(f'^{settings.INVENTREE_ADMIN_URL}/', admin.site.urls, name='inventree-admin'),

    # Single Sign On / allauth
    # Overrides of urlpatterns
    re_path(r"^accounts/password/reset/key/(?P<uidb36>[0-9A-Za-z]+)-(?P<key>.+)/$", CustomPasswordResetFromKeyView.as_view(), name="account_reset_password_from_key"),
    re_path(r"^accounts/login/", CustomLoginView.as_view(), name='account_login'),    # Override login page
    re_path(r'^accounts/', include('allauth_2fa.urls')),    # MFA support
    re_path(r'^accounts/', include('allauth.urls')),        # included urlpatterns
]

# Append custom plugin URLs (if plugin support is enabled)
if settings.PLUGINS_ENABLED:
    frontendpatterns.append(get_plugin_urls())

urlpatterns = [
    re_path('', include(frontendpatterns)),
    re_path('', include(backendpatterns)),
]

# Server running in "DEBUG" mode?
if settings.DEBUG:
    # Static file access
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

    # Media file access
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    # Debug toolbar access (only allowed in DEBUG mode)
    if settings.DEBUG_TOOLBAR_ENABLED:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
