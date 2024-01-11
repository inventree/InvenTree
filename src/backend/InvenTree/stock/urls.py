"""URL lookup for Stock app."""

from django.urls import include, path, re_path

from stock import views

location_urls = [
    path(
        r'<int:pk>/',
        include([
            # Anything else - direct to the location detail view
            re_path(
                '^.*$',
                views.StockLocationDetail.as_view(),
                name='stock-location-detail',
            )
        ]),
    )
]

stock_item_detail_urls = [
    # Anything else - direct to the item detail view
    re_path('^.*$', views.StockItemDetail.as_view(), name='stock-item-detail')
]

stock_urls = [
    # Stock location
    re_path(r'^location/', include(location_urls)),
    # Individual stock items
    re_path(r'^item/(?P<pk>\d+)/', include(stock_item_detail_urls)),
    # Default to the stock index page
    re_path(r'^.*$', views.StockIndex.as_view(), name='stock-index'),
]
