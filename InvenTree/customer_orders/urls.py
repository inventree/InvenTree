from django.conf.urls import url, include

from . import views

# URL list for customer orders web interface
customer_orders_urls = [
    # Top level order list
    url(r'^.*$', views.CustomerOrderIndex.as_view(), name='customer-order-index'),
]