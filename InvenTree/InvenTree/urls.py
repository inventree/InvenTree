from django.conf.urls import url, include
from django.contrib import admin
from django.contrib.auth import views as auth_views

from company.urls import company_urls

from part.urls import part_urls
from part.urls import supplier_part_urls

from stock.urls import stock_urls

from build.urls import build_urls

from part.api import part_api_urls
from company.api import company_api_urls
from stock.api import stock_api_urls

from django.conf import settings
from django.conf.urls.static import static

from django.views.generic.base import RedirectView
from rest_framework.documentation import include_docs_urls

from users.urls import user_urls

admin.site.site_header = "InvenTree Admin"

apipatterns = [
    url(r'^part/', include(part_api_urls)),
    url(r'^company/', include(company_api_urls)),
    url(r'^stock/', include(stock_api_urls)),

    # User URLs
    url(r'^user/', include(user_urls)),
]

urlpatterns = [
    url(r'^part/', include(part_urls)),
    url(r'^supplier-part/', include(supplier_part_urls)),

    url(r'^stock/', include(stock_urls)),

    url(r'^company/', include(company_urls)),

    url(r'^build/', include(build_urls)),

    url(r'^auth/', include('rest_framework.urls', namespace='rest_framework')),

    url(r'^login/', auth_views.login, name='login'),
    url(r'^logout/', auth_views.logout, {'template_name': 'registration/logout.html'}, name='logout'),
    url(r'^admin/', admin.site.urls),

    url(r'^api/', include(apipatterns)),
    url(r'^api-doc/', include_docs_urls(title='InvenTree API')),
]

# Static file access
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    # Media file access
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Send any unknown URLs to the parts page
urlpatterns += [url(r'^.*$', RedirectView.as_view(url='/part/', permanent=False), name='part-index')]
