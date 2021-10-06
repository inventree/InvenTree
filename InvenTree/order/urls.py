"""
URL lookup for the Order app. Provides URL endpoints for:

- List view of Purchase Orders
- Detail view of Purchase Orders
"""

from django.conf.urls import url, include

from . import views

purchase_order_detail_urls = [

    url(r'^cancel/', views.PurchaseOrderCancel.as_view(), name='po-cancel'),
    url(r'^issue/', views.PurchaseOrderIssue.as_view(), name='po-issue'),
    url(r'^complete/', views.PurchaseOrderComplete.as_view(), name='po-complete'),

    url(r'^upload/', views.PurchaseOrderUpload.as_view(), name='po-upload'),
    url(r'^export/', views.PurchaseOrderExport.as_view(), name='po-export'),

    url(r'^.*$', views.PurchaseOrderDetail.as_view(), name='po-detail'),
]

purchase_order_urls = [

    url(r'^order-parts/', views.OrderParts.as_view(), name='order-parts'),
    url(r'^pricing/', views.LineItemPricing.as_view(), name='line-pricing'),

    # Display detail view for a single purchase order
    url(r'^(?P<pk>\d+)/', include(purchase_order_detail_urls)),

    # Display complete list of purchase orders
    url(r'^.*$', views.PurchaseOrderIndex.as_view(), name='po-index'),
]

sales_order_detail_urls = [
    url(r'^cancel/', views.SalesOrderCancel.as_view(), name='so-cancel'),
    url(r'^ship/', views.SalesOrderShip.as_view(), name='so-ship'),

    url(r'^.*$', views.SalesOrderDetail.as_view(), name='so-detail'),
]

sales_order_urls = [
    # URLs for sales order allocations
    url(r'^allocation/', include([
        url(r'^new/', views.SalesOrderAllocationCreate.as_view(), name='so-allocation-create'),
        url(r'^assign-serials/', views.SalesOrderAssignSerials.as_view(), name='so-assign-serials'),
    ])),

    # Display detail view for a single SalesOrder
    url(r'^(?P<pk>\d+)/', include(sales_order_detail_urls)),

    # Display list of all sales orders
    url(r'^.*$', views.SalesOrderIndex.as_view(), name='so-index'),
]

order_urls = [
    url(r'^purchase-order/', include(purchase_order_urls)),
    url(r'^sales-order/', include(sales_order_urls)),
]
