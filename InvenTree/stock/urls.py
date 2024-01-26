"""URL lookup for Stock app."""

from django.urls import include, path

from stock import views

location_urls = [
    path(
        '<int:pk>/',
        include([
            # Anything else - direct to the location detail view
            path('', views.StockLocationDetail.as_view(), name='stock-location-detail')
        ]),
    )
]

stock_item_detail_urls = [
    # Anything else - direct to the item detail view
    path('', views.StockItemDetail.as_view(), name='stock-item-detail')
]

stock_urls = [
    # Stock location
    path('location/', include(location_urls)),
    # Individual stock items
    path('item/<int:pk>/', include(stock_item_detail_urls)),
    # Default to the stock index page
    path('', views.StockIndex.as_view(), name='stock-index'),
]
