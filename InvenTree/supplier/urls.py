from django.conf.urls import url

from . import views

cust_urls = [
    # Customer detail
    url(r'^(?P<pk>[0-9]+)/?$', views.CustomerDetail.as_view(), name='customer-detail'),

    # List customers
    url(r'^\?.*/?$', views.CustomerList.as_view()),
    url(r'^$', views.CustomerList.as_view())
]

manu_urls = [
    # Manufacturer detail
    url(r'^(?P<pk>[0-9]+)/?$', views.ManufacturerDetail.as_view(), name='manufacturer-detail'),

    # List manufacturers
    url(r'^\?.*/?$', views.ManufacturerList.as_view()),
    url(r'^$', views.ManufacturerList.as_view())
]

supplier_part_urls = [
    url(r'^(?P<pk>[0-9]+)/?$', views.SupplierPartDetail.as_view(), name='supplierpart-detail'),

    url(r'^\?.*/?$', views.SupplierPartList.as_view()),
    url(r'^$', views.SupplierPartList.as_view())
]

price_break_urls = [
    url(r'^(?P<pk>[0-9]+)/?$', views.SupplierPriceBreakDetail.as_view(), name='supplierpricebreak-detail'),

    url(r'^\?.*/?$', views.SupplierPriceBreakList.as_view()),
    url(r'^$', views.SupplierPriceBreakList.as_view())
]

supplier_urls = [

    # Display details of a supplier
    url(r'^(?P<pk>[0-9]+)/$', views.SupplierDetail.as_view(), name='supplier-detail'),

    # List suppliers
    url(r'^\?.*/?$', views.SupplierList.as_view()),
    url(r'^$', views.SupplierList.as_view())
]
