"""URL lookup for the Order app.

Provides URL endpoints for:
- List view of Purchase Orders
- Detail view of Purchase Orders
"""

from django.urls import include, path

from . import views

purchase_order_detail_urls = [
    path('upload/', views.PurchaseOrderUpload.as_view(), name='po-upload'),
    path('export/', views.PurchaseOrderExport.as_view(), name='po-export'),
    path('', views.PurchaseOrderDetail.as_view(), name='po-detail'),
]

purchase_order_urls = [
    path('pricing/', views.LineItemPricing.as_view(), name='line-pricing'),
    # Display detail view for a single purchase order
    path('<int:pk>/', include(purchase_order_detail_urls)),
    # Display complete list of purchase orders
    path('', views.PurchaseOrderIndex.as_view(), name='purchase-order-index'),
]

sales_order_detail_urls = [
    path('export/', views.SalesOrderExport.as_view(), name='so-export'),
    path('', views.SalesOrderDetail.as_view(), name='so-detail'),
]

sales_order_urls = [
    # Display detail view for a single SalesOrder
    path('<int:pk>/', include(sales_order_detail_urls)),
    # Display list of all sales orders
    path('', views.SalesOrderIndex.as_view(), name='sales-order-index'),
]


return_order_urls = [
    path('<int:pk>/', views.ReturnOrderDetail.as_view(), name='return-order-detail'),
    # Display list of all return orders
    path('', views.ReturnOrderIndex.as_view(), name='return-order-index'),
]


order_urls = [
    path('purchase-order/', include(purchase_order_urls)),
    path('sales-order/', include(sales_order_urls)),
    path('return-order/', include(return_order_urls)),
]
