"""URL lookup for Stock app."""

from django.urls import include, re_path

from stock import views

location_urls = [

    re_path(r'^(?P<pk>\d+)/', include([
        re_path(r'^qr_code/?', views.StockLocationQRCode.as_view(), name='stock-location-qr'),

        # Anything else - direct to the location detail view
        re_path('^.*$', views.StockLocationDetail.as_view(), name='stock-location-detail'),
    ])),

]

stock_item_detail_urls = [
    re_path(r'^qr_code/', views.StockItemQRCode.as_view(), name='stock-item-qr'),

    # Anything else - direct to the item detail view
    re_path('^.*$', views.StockItemDetail.as_view(), name='stock-item-detail'),
]

stock_urls = [
    # Stock location
    re_path(r'^location/', include(location_urls)),

    # Individual stock items
    re_path(r'^item/(?P<pk>\d+)/', include(stock_item_detail_urls)),

    # Default to the stock index page
    re_path(r'^.*$', views.StockIndex.as_view(), name='stock-index'),
]
