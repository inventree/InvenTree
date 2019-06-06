"""
URL lookup for the Order app. Provides URL endpoints for:

- List view of Purchase Orders
- Detail view of Purchase Orders
"""

from django.conf.urls import url, include

from . import views

purchase_order_detail_urls = [

    url(r'^edit/?', views.PurchaseOrderEdit.as_view(), name='purchase-order-edit'),
    url(r'^issue/?', views.PurchaseOrderIssue.as_view(), name='purchase-order-issue'),

    url(r'^.*$', views.PurchaseOrderDetail.as_view(), name='purchase-order-detail'),
]

po_line_urls = [

    url(r'^new/', views.POLineItemCreate.as_view(), name='po-line-item-create'),
]

purchase_order_urls = [

    url(r'^new/', views.PurchaseOrderCreate.as_view(), name='purchase-order-create'),

    # Display detail view for a single purchase order
    url(r'^(?P<pk>\d+)/', include(purchase_order_detail_urls)),

    url(r'^line/', include(po_line_urls)),

    # Display complete list of purchase orders
    url(r'^.*$', views.PurchaseOrderIndex.as_view(), name='purchase-order-index'),
]

order_urls = [
    url(r'^purchase-order/', include(purchase_order_urls)),
]
