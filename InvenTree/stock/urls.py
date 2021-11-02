"""
URL lookup for Stock app
"""

from django.conf.urls import url, include

from stock import views

location_urls = [

    url(r'^new/', views.StockLocationCreate.as_view(), name='stock-location-create'),

    url(r'^(?P<pk>\d+)/', include([
        url(r'^edit/?', views.StockLocationEdit.as_view(), name='stock-location-edit'),
        url(r'^delete/?', views.StockLocationDelete.as_view(), name='stock-location-delete'),
        url(r'^qr_code/?', views.StockLocationQRCode.as_view(), name='stock-location-qr'),
        
        # Anything else
        url('^.*$', views.StockLocationDetail.as_view(), name='stock-location-detail'),
    ])),

]

stock_item_detail_urls = [
    url(r'^convert/', views.StockItemConvert.as_view(), name='stock-item-convert'),
    url(r'^serialize/', views.StockItemSerialize.as_view(), name='stock-item-serialize'),
    url(r'^delete/', views.StockItemDelete.as_view(), name='stock-item-delete'),
    url(r'^qr_code/', views.StockItemQRCode.as_view(), name='stock-item-qr'),
    url(r'^delete_test_data/', views.StockItemDeleteTestData.as_view(), name='stock-item-delete-test-data'),
    url(r'^assign/', views.StockItemAssignToCustomer.as_view(), name='stock-item-assign'),
    url(r'^return/', views.StockItemReturnToStock.as_view(), name='stock-item-return'),
    url(r'^install/', views.StockItemInstall.as_view(), name='stock-item-install'),

    url(r'^add_tracking/', views.StockItemTrackingCreate.as_view(), name='stock-tracking-create'),

    url('^.*$', views.StockItemDetail.as_view(), name='stock-item-detail'),
]

stock_tracking_urls = [

    # edit
    url(r'^(?P<pk>\d+)/edit/', views.StockItemTrackingEdit.as_view(), name='stock-tracking-edit'),

    # delete
    url(r'^(?P<pk>\d+)/delete', views.StockItemTrackingDelete.as_view(), name='stock-tracking-delete'),
]

stock_urls = [
    # Stock location
    url(r'^location/', include(location_urls)),

    url(r'^item/new/?', views.StockItemCreate.as_view(), name='stock-item-create'),

    url(r'^item/uninstall/', views.StockItemUninstall.as_view(), name='stock-item-uninstall'),

    url(r'^track/', include(stock_tracking_urls)),

    url(r'^export/?', views.StockExport.as_view(), name='stock-export'),

    # Individual stock items
    url(r'^item/(?P<pk>\d+)/', include(stock_item_detail_urls)),

    url(r'^sublocations/', views.StockIndex.as_view(template_name='stock/sublocation.html'), name='stock-sublocations'),

    url(r'^.*$', views.StockIndex.as_view(), name='stock-index'),
]
