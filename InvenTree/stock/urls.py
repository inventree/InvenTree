from django.conf.urls import url

from . import views

urlpatterns = [
    # List all stock quantities for a given part
    url(r'^part/(?P<part>[0-9]+)$', views.PartStockDetail.as_view()),

    # List all stock items in a given location
    url(r'^location/(?P<pk>[0-9]+)$', views.LocationDetail.as_view()),

    # List all top-level locations
    url(r'^location/$', views.LocationList.as_view()),
    url(r'^$', views.LocationList.as_view())
]
