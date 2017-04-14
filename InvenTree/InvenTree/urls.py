from django.conf.urls import url, include
from django.contrib import admin

from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view

admin.site.site_header = "InvenTree Admin"


@api_view()
def Inventree404(self):
    """ Supplied URL is invalid
    """
    content = {'detail': 'Malformed API URL'}
    return Response(content, status=status.HTTP_404_NOT_FOUND)


apipatterns = [
    url(r'^stock/', include('stock.urls')),
    url(r'^part/', include('part.urls')),
    url(r'^supplier/', include('supplier.urls')),
    url(r'^track/', include('track.urls')),
    url(r'^project/', include('project.urls')),

    # Any other URL
    url(r'', Inventree404)
]

urlpatterns = [
    # API URL
    url(r'^api/', include(apipatterns)),

    url(r'^admin/', admin.site.urls),
    url(r'^auth/', include('rest_framework.urls', namespace='rest_framework')),
]
