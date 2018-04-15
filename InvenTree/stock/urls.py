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
stock_location_detail_urls = [
    url(r'^edit/?', views.StockLocationEdit.as_view(), name='stock-location-edit'),
    url(r'^delete/?', views.StockLocationDelete.as_view(), name='stock-location-delete'),

    # Anything else
    url('^.*$', views.StockLocationDetail.as_view(), name='stock-location-detail'),
]

stock_item_detail_urls = [
    url(r'^edit/?', views.StockItemEdit.as_view(), name='stock-item-edit'),
    url(r'^delete/?', views.StockItemDelete.as_view(), name='stock-item-delete'),

    url('^.*$', views.StockItemDetail.as_view(), name='stock-item-detail'),
]

stock_urls = [
    # Stock location
    url(r'^location/(?P<pk>\d+)/', include(stock_location_detail_urls)),

    url(r'^location/new/', views.StockLocationCreate.as_view(), name='stock-location-create'),

    url(r'^item/new/?', views.StockItemCreate.as_view(), name='stock-item-create'),

    # Individual stock items
    url(r'^item/(?P<pk>\d+)/', include(stock_item_detail_urls)),

    url(r'^.*$', views.StockIndex.as_view(), name='stock-index'),
]