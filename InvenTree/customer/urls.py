from django.conf.urls import url, include

from . import views

customer_detail_urls = [
    # url(r'^edit/?', views.CustomerEdit.as_view(), name='customer-edit'),
    # url(r'^delete/?', views.CustomerDelete.as_view(), name='customer-delete'),

    # Everything else
    url(r'^.*$', views.CustomerDetail.as_view(), name='customer-detail'),
]

customer_order_detail_urls = [
    # url(r'^edit/?', views.CustomerOrderEdit.as_view(), name='customer-order-edit'),
    # url(r'^delete/?', views.CustomerOrderDelete.as_view(), name='customer-order-delete'),

    # Everything else
    url(r'^.*$', views.CustomerOrderDetail.as_view(), name='customer-order-detail'),
]

customer_orders_urls = [
    # Details of a specific order
    # Details of an individual customer
    url(r'^(?P<pk>[0-9]+)/', include(customer_order_detail_urls)),

    # Create a new customer order
    # url(r'new/?', views.CustomerOrderCreate.as_view(), name='customer-order-create'),

    # Everything else
    url(r'^.*$', views.CustomerOrderIndex.as_view(), name='customer-order-index'),
]

# URL list for customer orders web interface
customer_urls = [

    # Customer orders (CSO)
    url(r'^order/', include(customer_orders_urls)),

    # Details of an individual customer
    url(r'^(?P<pk>[0-9]+)/', include(customer_detail_urls)),

    # url(r'new/?', views.CustomerCreate.as_view(), name='customer-create'),

    # Top level order list
    url(r'^.*$', views.CustomerIndex.as_view(), name='customer-index'),
]
