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
    url(r'^edit/', views.StockItemEdit.as_view(), name='stock-item-edit'),
    url(r'^convert/', views.StockItemConvert.as_view(), name='stock-item-convert'),
    url(r'^serialize/', views.StockItemSerialize.as_view(), name='stock-item-serialize'),
    url(r'^delete/', views.StockItemDelete.as_view(), name='stock-item-delete'),
    url(r'^qr_code/', views.StockItemQRCode.as_view(), name='stock-item-qr'),
    url(r'^delete_test_data/', views.StockItemDeleteTestData.as_view(), name='stock-item-delete-test-data'),
    url(r'^assign/', views.StockItemAssignToCustomer.as_view(), name='stock-item-assign'),
    url(r'^return/', views.StockItemReturnToStock.as_view(), name='stock-item-return'),
    url(r'^install/', views.StockItemInstall.as_view(), name='stock-item-install'),

    url(r'^add_tracking/', views.StockItemTrackingCreate.as_view(), name='stock-tracking-create'),

    url(r'^test-report-select/', views.StockItemTestReportSelect.as_view(), name='stock-item-test-report-select'),
    url(r'^label-select/', views.StockItemSelectLabels.as_view(), name='stock-item-label-select'),

    url(r'^test/', views.StockItemDetail.as_view(template_name='stock/item_tests.html'), name='stock-item-test-results'),
    url(r'^children/', views.StockItemDetail.as_view(template_name='stock/item_childs.html'), name='stock-item-children'),
    url(r'^attachments/', views.StockItemDetail.as_view(template_name='stock/item_attachments.html'), name='stock-item-attachments'),
    url(r'^installed/', views.StockItemDetail.as_view(template_name='stock/item_installed.html'), name='stock-item-installed'),
    url(r'^notes/', views.StockItemNotes.as_view(), name='stock-item-notes'),

    url('^.*$', views.StockItemDetail.as_view(), name='stock-item-detail'),
]

stock_tracking_urls = [

    # edit
    url(r'^(?P<pk>\d+)/edit/', views.StockItemTrackingEdit.as_view(), name='stock-tracking-edit'),

    # delete
    url(r'^(?P<pk>\d+)/delete', views.StockItemTrackingDelete.as_view(), name='stock-tracking-delete'),

    # list
    url('^.*$', views.StockTrackingIndex.as_view(), name='stock-tracking-list')
]

stock_urls = [
    # Stock location
    url(r'^location/(?P<pk>\d+)/', include(stock_location_detail_urls)),

    url(r'^location/new/', views.StockLocationCreate.as_view(), name='stock-location-create'),

    url(r'^item/new/?', views.StockItemCreate.as_view(), name='stock-item-create'),

    url(r'^item/uninstall/', views.StockItemUninstall.as_view(), name='stock-item-uninstall'),

    url(r'^item/test-report-download/', views.StockItemTestReportDownload.as_view(), name='stock-item-test-report-download'),
    url(r'^item/print-stock-labels/', views.StockItemPrintLabels.as_view(), name='stock-item-print-labels'),

    # URLs for StockItem attachments
    url(r'^item/attachment/', include([
        url(r'^new/', views.StockItemAttachmentCreate.as_view(), name='stock-item-attachment-create'),
        url(r'^(?P<pk>\d+)/edit/', views.StockItemAttachmentEdit.as_view(), name='stock-item-attachment-edit'),
        url(r'^(?P<pk>\d+)/delete/', views.StockItemAttachmentDelete.as_view(), name='stock-item-attachment-delete'),
    ])),

    # URLs for StockItem tests
    url(r'^item/test/', include([
        url(r'^new/', views.StockItemTestResultCreate.as_view(), name='stock-item-test-create'),
        url(r'^(?P<pk>\d+)/edit/', views.StockItemTestResultEdit.as_view(), name='stock-item-test-edit'),
        url(r'^(?P<pk>\d+)/delete/', views.StockItemTestResultDelete.as_view(), name='stock-item-test-delete'),
    ])),

    url(r'^track/', include(stock_tracking_urls)),

    url(r'^adjust/?', views.StockAdjust.as_view(), name='stock-adjust'),

    url(r'^export-options/?', views.StockExportOptions.as_view(), name='stock-export-options'),
    url(r'^export/?', views.StockExport.as_view(), name='stock-export'),

    # Individual stock items
    url(r'^item/(?P<pk>\d+)/', include(stock_item_detail_urls)),

    url(r'^.*$', views.StockIndex.as_view(), name='stock-index'),
]
