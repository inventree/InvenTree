"""
URL lookup for the Order app. Provides URL endpoints for:

- List view of Purchase Orders
- Detail view of Purchase Orders
"""

from django.conf.urls import url, include

from . import views

purchase_order_detail_urls = [

    url(r'^cancel/?', views.PurchaseOrderCancel.as_view(), name='purchase-order-cancel'),
    url(r'^edit/?', views.PurchaseOrderEdit.as_view(), name='purchase-order-edit'),
    url(r'^issue/?', views.PurchaseOrderIssue.as_view(), name='purchase-order-issue'),
    url(r'^receive/?', views.PurchaseOrderReceive.as_view(), name='purchase-order-receive'),

    url(r'^export/?', views.PurchaseOrderExport.as_view(), name='purchase-order-export'),

    url(r'^.*$', views.PurchaseOrderDetail.as_view(), name='purchase-order-detail'),
]

po_line_item_detail_urls = [
    
    url(r'^edit/', views.POLineItemEdit.as_view(), name='po-line-item-edit'),
    url(r'^delete/', views.POLineItemDelete.as_view(), name='po-line-item-delete'),
]

po_line_urls = [

    url(r'^new/', views.POLineItemCreate.as_view(), name='po-line-item-create'),

    url(r'^(?P<pk>\d+)/', include(po_line_item_detail_urls)),
]

purchase_order_urls = [

    url(r'^new/', views.PurchaseOrderCreate.as_view(), name='purchase-order-create'),

    url(r'^order-parts/', views.OrderParts.as_view(), name='order-parts'),

    # Display detail view for a single purchase order
    url(r'^(?P<pk>\d+)/', include(purchase_order_detail_urls)),

    url(r'^line/', include(po_line_urls)),

    # Display complete list of purchase orders
    url(r'^.*$', views.PurchaseOrderIndex.as_view(), name='purchase-order-index'),
]

order_urls = [
    url(r'^purchase-order/', include(purchase_order_urls)),
]
