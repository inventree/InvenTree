from django.conf.urls import url

from . import views
from . import api

cust_urls = [
    # Customer detail
    url(r'^(?P<pk>[0-9]+)/?$', api.CustomerDetail.as_view(), name='customer-detail'),

    # List customers
    url(r'^\?.*/?$', api.CustomerList.as_view()),
    url(r'^$', api.CustomerList.as_view())
]

manu_urls = [
    # Manufacturer detail
    url(r'^(?P<pk>[0-9]+)/?$', api.ManufacturerDetail.as_view(), name='manufacturer-detail'),

    # List manufacturers
    url(r'^\?.*/?$', api.ManufacturerList.as_view()),
    url(r'^$', api.ManufacturerList.as_view())
]

supplier_part_urls = [
    url(r'^(?P<pk>[0-9]+)/?$', api.SupplierPartDetail.as_view(), name='supplierpart-detail'),

    url(r'^\?.*/?$', api.SupplierPartList.as_view()),
    url(r'^$', api.SupplierPartList.as_view())
]

price_break_urls = [
    url(r'^(?P<pk>[0-9]+)/?$', api.SupplierPriceBreakDetail.as_view(), name='supplierpricebreak-detail'),

    url(r'^\?.*/?$', api.SupplierPriceBreakList.as_view()),
    url(r'^$', api.SupplierPriceBreakList.as_view())
]

supplier_urls = [

    # Display details of a supplier
    url(r'^(?P<pk>[0-9]+)/$', api.SupplierDetail.as_view(), name='supplier-detail'),

    # List suppliers
    url(r'^\?.*/?$', api.SupplierList.as_view()),
    url(r'^$', api.SupplierList.as_view())
]
