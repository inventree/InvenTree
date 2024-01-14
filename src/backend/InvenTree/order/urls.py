"""URL lookup for the Order app.

Provides URL endpoints for:
- List view of Purchase Orders
- Detail view of Purchase Orders
"""

from django.urls import include, path, re_path

from . import views

purchase_order_detail_urls = [
    re_path(r'^upload/', views.PurchaseOrderUpload.as_view(), name='po-upload'),
    re_path(r'^export/', views.PurchaseOrderExport.as_view(), name='po-export'),
    re_path(r'^.*$', views.PurchaseOrderDetail.as_view(), name='po-detail'),
]

purchase_order_urls = [
    re_path(r'^pricing/', views.LineItemPricing.as_view(), name='line-pricing'),
    # Display detail view for a single purchase order
    path(r'<int:pk>/', include(purchase_order_detail_urls)),
    # Display complete list of purchase orders
    re_path(r'^.*$', views.PurchaseOrderIndex.as_view(), name='purchase-order-index'),
]

sales_order_detail_urls = [
    re_path(r'^export/', views.SalesOrderExport.as_view(), name='so-export'),
    re_path(r'^.*$', views.SalesOrderDetail.as_view(), name='so-detail'),
]

sales_order_urls = [
    # Display detail view for a single SalesOrder
    path(r'<int:pk>/', include(sales_order_detail_urls)),
    # Display list of all sales orders
    re_path(r'^.*$', views.SalesOrderIndex.as_view(), name='sales-order-index'),
]


return_order_urls = [
    path(r'<int:pk>/', views.ReturnOrderDetail.as_view(), name='return-order-detail'),
    # Display list of all return orders
    re_path(r'^.*$', views.ReturnOrderIndex.as_view(), name='return-order-index'),
]


order_urls = [
    re_path(r'^purchase-order/', include(purchase_order_urls)),
    re_path(r'^sales-order/', include(sales_order_urls)),
    re_path(r'^return-order/', include(return_order_urls)),
]
