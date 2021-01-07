"""
Top-level URL lookup for InvenTree application.

Passes URL lookup downstream to each app as required.
"""


from django.conf.urls import url, include
from django.urls import path
from django.contrib import admin
from django.contrib.auth import views as auth_views
from qr_code import urls as qr_code_urls

from company.urls import company_urls
from company.urls import supplier_part_urls
from company.urls import price_break_urls

from common.urls import common_urls
from part.urls import part_urls
from stock.urls import stock_urls
from build.urls import build_urls
from order.urls import order_urls

from barcode.api import barcode_api_urls
from common.api import common_api_urls
from part.api import part_api_urls, bom_api_urls
from company.api import company_api_urls
from stock.api import stock_api_urls
from build.api import build_api_urls
from order.api import order_api_urls

from django.conf import settings
from django.conf.urls.static import static

from django.views.generic.base import RedirectView
from rest_framework.documentation import include_docs_urls

from .views import IndexView, SearchView, DatabaseStatsView
from .views import SettingsView, EditUserView, SetPasswordView
from .views import ColorThemeSelectView, SettingCategorySelectView
from .views import DynamicJsView

from common.views import SettingEdit

from .api import InfoView
from .api import ActionPluginView

from users.urls import user_urls

admin.site.site_header = "InvenTree Admin"

apipatterns = [
    url(r'^barcode/', include(barcode_api_urls)),
    url(r'^common/', include(common_api_urls)),
    url(r'^part/', include(part_api_urls)),
    url(r'^bom/', include(bom_api_urls)),
    url(r'^company/', include(company_api_urls)),
    url(r'^stock/', include(stock_api_urls)),
    url(r'^build/', include(build_api_urls)),
    url(r'^order/', include(order_api_urls)),

    # User URLs
    url(r'^user/', include(user_urls)),

    # Plugin endpoints
    url(r'^action/', ActionPluginView.as_view(), name='api-action-plugin'),

    # InvenTree information endpoint
    url(r'^$', InfoView.as_view(), name='api-inventree-info'),
]

settings_urls = [

    url(r'^user/?', SettingsView.as_view(template_name='InvenTree/settings/user.html'), name='settings-user'),
    url(r'^theme/?', ColorThemeSelectView.as_view(), name='settings-theme'),
   
    url(r'^global/?', SettingsView.as_view(template_name='InvenTree/settings/global.html'), name='settings-global'),
    url(r'^category/?', SettingCategorySelectView.as_view(), name='settings-category'),
    url(r'^part/?', SettingsView.as_view(template_name='InvenTree/settings/part.html'), name='settings-part'),
    url(r'^stock/?', SettingsView.as_view(template_name='InvenTree/settings/stock.html'), name='settings-stock'),
    url(r'^build/?', SettingsView.as_view(template_name='InvenTree/settings/build.html'), name='settings-build'),
    url(r'^purchase-order/?', SettingsView.as_view(template_name='InvenTree/settings/po.html'), name='settings-po'),
    url(r'^sales-order/?', SettingsView.as_view(template_name='InvenTree/settings/so.html'), name='settings-so'),

    url(r'^(?P<pk>\d+)/edit/', SettingEdit.as_view(), name='setting-edit'),

    # Catch any other urls
    url(r'^.*$', SettingsView.as_view(template_name='InvenTree/settings/user.html'), name='settings'),
]

# Some javascript files are served 'dynamically', allowing them to pass through the Django translation layer
dynamic_javascript_urls = [
    url(r'^barcode.js', DynamicJsView.as_view(template_name='js/barcode.js'), name='barcode.js'),
    url(r'^bom.js', DynamicJsView.as_view(template_name='js/bom.js'), name='bom.js'),
    url(r'^build.js', DynamicJsView.as_view(template_name='js/build.js'), name='build.js'),
    url(r'^calendar.js', DynamicJsView.as_view(template_name='js/calendar.js'), name='calendar.js'),
    url(r'^company.js', DynamicJsView.as_view(template_name='js/company.js'), name='company.js'),
    url(r'^order.js', DynamicJsView.as_view(template_name='js/order.js'), name='order.js'),
    url(r'^part.js', DynamicJsView.as_view(template_name='js/part.js'), name='part.js'),
    url(r'^stock.js', DynamicJsView.as_view(template_name='js/stock.js'), name='stock.js'),
    url(r'^table_filters.js', DynamicJsView.as_view(template_name='js/table_filters.js'), name='table_filters.js'),
]

urlpatterns = [
    url(r'^part/', include(part_urls)),
    url(r'^supplier-part/', include(supplier_part_urls)),
    url(r'^price-break/', include(price_break_urls)),

    # "Dynamic" javascript files which are rendered using InvenTree templating.
    url(r'^dynamic/', include(dynamic_javascript_urls)),

    url(r'^common/', include(common_urls)),

    url(r'^stock/', include(stock_urls)),

    url(r'^company/', include(company_urls)),
    url(r'^order/', include(order_urls)),

    url(r'^build/', include(build_urls)),

    url(r'^auth/', include('rest_framework.urls', namespace='rest_framework')),

    url(r'^login/?', auth_views.LoginView.as_view(), name='login'),
    url(r'^logout/', auth_views.LogoutView.as_view(template_name='registration/logout.html'), name='logout'),
    
    url(r'^settings/', include(settings_urls)),

    url(r'^edit-user/', EditUserView.as_view(), name='edit-user'),
    url(r'^set-password/', SetPasswordView.as_view(), name='set-password'),

    url(r'^admin/error_log/', include('error_report.urls')),
    url(r'^admin/shell/', include('django_admin_shell.urls')),
    url(r'^admin/', admin.site.urls, name='inventree-admin'),

    url(r'^qr_code/', include(qr_code_urls, namespace='qr_code')),

    url(r'^index/', IndexView.as_view(), name='index'),
    url(r'^search/', SearchView.as_view(), name='search'),
    url(r'^stats/', DatabaseStatsView.as_view(), name='stats'),

    url(r'^api/', include(apipatterns)),
    url(r'^api-doc/', include_docs_urls(title='InvenTree API')),

    url(r'^markdownx/', include('markdownx.urls')),
]

# Static file access
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Media file access
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Debug toolbar access (if in DEBUG mode)
if settings.DEBUG and 'debug_toolbar' in settings.INSTALLED_APPS:
    import debug_toolbar
    urlpatterns = [
        path('__debug/', include(debug_toolbar.urls)),
    ] + urlpatterns

# Send any unknown URLs to the parts page
urlpatterns += [url(r'^.*$', RedirectView.as_view(url='/index/', permanent=False), name='index')]
