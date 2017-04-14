from django.conf.urls import url, include

from . import views

locpatterns = [
    url(r'^(?P<pk>[0-9]+)/?$', views.LocationDetail.as_view(), name='location-detail'),

    url(r'^\?.*/?$', views.LocationList.as_view(), name='location-list'),

    url(r'^$', views.LocationList.as_view(), name='location-list')
]

urlpatterns = [
    # Stock location urls
    url(r'^location/', include(locpatterns)),

    # Detail for a single stock item
    url(r'^(?P<pk>[0-9]+)/?$', views.StockDetail.as_view(), name='stock-detail'),

    # List all stock items, with optional filters
    url(r'^\?.*/?$', views.StockList.as_view(), name='stock-list'),
    url(r'^$', views.StockList.as_view(), name='stock-list'),
]
