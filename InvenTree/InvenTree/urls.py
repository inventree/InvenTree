from django.conf.urls import url, include
from django.contrib import admin

admin.site.site_header = "InvenTree Admin"

urlpatterns = [
    url(r'^stock/', include('stock.urls')),
    url(r'^part/', include('part.urls')),
    url(r'^supplier/', include('supplier.urls')),
    url(r'^track/', include('track.urls')),
    url(r'^project/', include('project.urls')),
    url(r'^admin/', admin.site.urls),
    url(r'^auth/', include('rest_framework.urls', namespace='rest_framework'))
]
