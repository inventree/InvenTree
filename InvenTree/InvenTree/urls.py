from django.conf.urls import url, include
from django.contrib import admin

from rest_framework.documentation import include_docs_urls

admin.site.site_header = "InvenTree Admin"

apipatterns = [
    url(r'^stock/', include('stock.urls')),
    url(r'^stock-location/', include('stock.location_urls')),
    url(r'^part/', include('part.urls')),
    url(r'^supplier/', include('supplier.urls')),
    url(r'^supplier-part/', include('supplier.part_urls')),
    url(r'^price-break/', include('supplier.price_urls')),
    url(r'^manufacturer/', include('supplier.manufacturer_urls')),
    url(r'^customer/', include('supplier.customer_urls')),
    url(r'^track/', include('track.urls')),
    url(r'^project/', include('project.urls')),
]

urlpatterns = [
    # API URL
    url(r'^api/', include(apipatterns)),

    url(r'^api-doc/', include_docs_urls(title='InvenTree API')),

    url(r'^admin/', admin.site.urls),
    url(r'^auth/', include('rest_framework.urls', namespace='rest_framework')),
]
