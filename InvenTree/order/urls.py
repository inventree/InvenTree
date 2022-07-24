"""URL lookup for the Order app. Provides URL endpoints for:

- List view of Purchase Orders
- Detail view of Purchase Orders
"""

from django.urls import include, re_path

from . import views

purchase_order_detail_urls = [

    re_path(r'^upload/', views.PurchaseOrderUpload.as_view(), name='po-upload'),
    re_path(r'^export/', views.PurchaseOrderExport.as_view(), name='po-export'),

    re_path(r'^.*$', views.PurchaseOrderDetail.as_view(), name='po-detail'),
]

purchase_order_urls = [

    # Export calendar in ICS format
    re_path(r'^calendar.ics', views.PurchaseOrderCalendarExport(), name='po-calendar'),

    re_path(r'^pricing/', views.LineItemPricing.as_view(), name='line-pricing'),

    # Display detail view for a single purchase order
    re_path(r'^(?P<pk>\d+)/', include(purchase_order_detail_urls)),

    # Display complete list of purchase orders
    re_path(r'^.*$', views.PurchaseOrderIndex.as_view(), name='po-index'),
]

sales_order_detail_urls = [
    re_path(r'^export/', views.SalesOrderExport.as_view(), name='so-export'),

    re_path(r'^.*$', views.SalesOrderDetail.as_view(), name='so-detail'),
]

sales_order_urls = [
    # Display detail view for a single SalesOrder
    re_path(r'^(?P<pk>\d+)/', include(sales_order_detail_urls)),

    # Display list of all sales orders
    re_path(r'^.*$', views.SalesOrderIndex.as_view(), name='so-index'),
]

order_urls = [
    re_path(r'^purchase-order/', include(purchase_order_urls)),
    re_path(r'^sales-order/', include(sales_order_urls)),
]
