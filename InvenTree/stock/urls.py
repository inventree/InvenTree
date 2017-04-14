from django.conf.urls import url, include

from . import views

locpatterns = [
    url(r'^(?P<pk>[0-9]+)/?$', views.LocationDetail.as_view(), name='stocklocation-detail'),

    url(r'^\?.*/?$', views.LocationList.as_view()),

    url(r'^$', views.LocationList.as_view())
]

urlpatterns = [
    # Stock location urls
    url(r'^location/', include(locpatterns)),

    # Detail for a single stock item
    url(r'^(?P<pk>[0-9]+)/?$', views.StockDetail.as_view(), name='stockitem-detail'),

    # List all stock items, with optional filters
    url(r'^\?.*/?$', views.StockList.as_view()),
    url(r'^$', views.StockList.as_view()),
]
