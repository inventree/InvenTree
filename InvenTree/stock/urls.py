"""
URL lookup for Stock app
"""

from django.urls import include, re_path

from stock import views

location_urls = [

    re_path(r'^(?P<pk>\d+)/', include([
        re_path(r'^delete/?', views.StockLocationDelete.as_view(), name='stock-location-delete'),
        re_path(r'^qr_code/?', views.StockLocationQRCode.as_view(), name='stock-location-qr'),

        # Anything else
        re_path('^.*$', views.StockLocationDetail.as_view(), name='stock-location-detail'),
    ])),

]

stock_item_detail_urls = [
    re_path(r'^convert/', views.StockItemConvert.as_view(), name='stock-item-convert'),
    re_path(r'^delete/', views.StockItemDelete.as_view(), name='stock-item-delete'),
    re_path(r'^qr_code/', views.StockItemQRCode.as_view(), name='stock-item-qr'),
    re_path(r'^delete_test_data/', views.StockItemDeleteTestData.as_view(), name='stock-item-delete-test-data'),
    re_path(r'^return/', views.StockItemReturnToStock.as_view(), name='stock-item-return'),

    re_path(r'^add_tracking/', views.StockItemTrackingCreate.as_view(), name='stock-tracking-create'),

    re_path('^.*$', views.StockItemDetail.as_view(), name='stock-item-detail'),
]

stock_urls = [
    # Stock location
    re_path(r'^location/', include(location_urls)),

    # Individual stock items
    re_path(r'^item/(?P<pk>\d+)/', include(stock_item_detail_urls)),

    re_path(r'^sublocations/', views.StockIndex.as_view(template_name='stock/sublocation.html'), name='stock-sublocations'),

    re_path(r'^.*$', views.StockIndex.as_view(), name='stock-index'),
]
