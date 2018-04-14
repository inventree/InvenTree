from django.conf.urls import url, include
from django.views.generic.base import RedirectView

from . import views
from . import api

stock_endpoints = [
    url(r'^$', api.StockDetail.as_view(), name='stockitem-detail'),

    url(r'^stocktake/?$', api.StockStocktakeEndpoint.as_view(), name='stockitem-stocktake'),

    url(r'^add-stock/?$', api.AddStockEndpoint.as_view(), name='stockitem-add-stock'),
]

stock_api_urls = [
    # Detail for a single stock item
    url(r'^(?P<pk>[0-9]+)/', include(stock_endpoints)),

    # List all stock items, with optional filters
    url(r'^\?.*/?$', api.StockList.as_view()),
    url(r'^$', api.StockList.as_view()),
]

stock_api_loc_urls = [
    url(r'^(?P<pk>[0-9]+)/?$', api.LocationDetail.as_view(), name='stocklocation-detail'),

    url(r'^\?.*/?$', api.LocationList.as_view()),

    url(r'^$', api.LocationList.as_view())
]


# URL list for web interface
stock_detail_urls = [
    url('', views.detail, name='stock-detail'),
]
stock_urls = [
    # Individual stock items
    url(r'^(?P<pk>\d+)/', include(stock_detail_urls)),

    url('list', views.index, name='stock=index'),

    # Redirect any other patterns
    url(r'^.*$', RedirectView.as_view(url='list', permanent=False), name='stock-index'),
]