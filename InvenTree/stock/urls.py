from django.conf.urls import url, include

from . import views

stock_endpoints = [
    url(r'^$', views.StockDetail.as_view(), name='stockitem-detail'),

    url(r'^stocktake/?$', views.StockStocktakeEndpoint.as_view(), name='stockitem-stocktake'),

    url(r'^add-stock/?$', views.AddStockEndpoint.as_view(), name='stockitem-add-stock'),
]

stock_urls = [
    # Detail for a single stock item
    url(r'^(?P<pk>[0-9]+)/', include(stock_endpoints)),

    # List all stock items, with optional filters
    url(r'^\?.*/?$', views.StockList.as_view()),
    url(r'^$', views.StockList.as_view()),
]

stock_loc_urls = [
    url(r'^(?P<pk>[0-9]+)/?$', views.LocationDetail.as_view(), name='stocklocation-detail'),

    url(r'^\?.*/?$', views.LocationList.as_view()),

    url(r'^$', views.LocationList.as_view())
]
