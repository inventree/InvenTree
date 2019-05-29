"""
URL lookup for Stock app
"""

from django.conf.urls import url, include

from . import views

# URL list for web interface
stock_location_detail_urls = [
    url(r'^edit/?', views.StockLocationEdit.as_view(), name='stock-location-edit'),
    url(r'^delete/?', views.StockLocationDelete.as_view(), name='stock-location-delete'),
    url(r'^qr_code/?', views.StockLocationQRCode.as_view(), name='stock-location-qr'),

    # Anything else
    url('^.*$', views.StockLocationDetail.as_view(), name='stock-location-detail'),
]

stock_item_detail_urls = [
    url(r'^edit/?', views.StockItemEdit.as_view(), name='stock-item-edit'),
    url(r'^delete/?', views.StockItemDelete.as_view(), name='stock-item-delete'),
    url(r'^move/?', views.StockItemMove.as_view(), name='stock-item-move'),
    url(r'^stocktake/?', views.StockItemStocktake.as_view(), name='stock-item-stocktake'),
    url(r'^qr_code/?', views.StockItemQRCode.as_view(), name='stock-item-qr'),

    url('^.*$', views.StockItemDetail.as_view(), name='stock-item-detail'),
]

stock_urls = [
    # Stock location
    url(r'^location/(?P<pk>\d+)/', include(stock_location_detail_urls)),

    url(r'^location/new/', views.StockLocationCreate.as_view(), name='stock-location-create'),

    url(r'^item/new/?', views.StockItemCreate.as_view(), name='stock-item-create'),

    url(r'^track/?', views.StockTrackingIndex.as_view(), name='stock-tracking-list'),

    url(r'^move/', views.StockItemMoveMultiple.as_view(), name='stock-item-move-multiple'),

    # Individual stock items
    url(r'^item/(?P<pk>\d+)/', include(stock_item_detail_urls)),

    url(r'^.*$', views.StockIndex.as_view(), name='stock-index'),
]
