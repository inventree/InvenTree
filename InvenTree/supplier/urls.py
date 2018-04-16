from django.conf.urls import url, include
from django.views.generic.base import RedirectView

from . import views

"""
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

supplier_api_part_urls = [
    url(r'^(?P<pk>[0-9]+)/?$', api.SupplierPartDetail.as_view(), name='supplierpart-detail'),

    url(r'^\?.*/?$', api.SupplierPartList.as_view()),
    url(r'^$', api.SupplierPartList.as_view())
]

price_break_urls = [
    url(r'^(?P<pk>[0-9]+)/?$', api.SupplierPriceBreakDetail.as_view(), name='supplierpricebreak-detail'),

    url(r'^\?.*/?$', api.SupplierPriceBreakList.as_view()),
    url(r'^$', api.SupplierPriceBreakList.as_view())
]

supplier_api_urls = [

    # Display details of a supplier
    url(r'^(?P<pk>[0-9]+)/$', api.SupplierDetail.as_view(), name='supplier-detail'),

    # List suppliers
    url(r'^\?.*/?$', api.SupplierList.as_view()),
    url(r'^$', api.SupplierList.as_view())
]
"""

supplier_detail_urls = [
    url(r'edit/?', views.SupplierEdit.as_view(), name='supplier-edit'),
    url(r'delete/?', views.SupplierDelete.as_view(), name='supplier-delete'),

    url(r'^.*$', views.SupplierDetail.as_view(), name='supplier-detail'),
]

supplier_part_detail_urls = [
    url(r'edit/?', views.SupplierPartEdit.as_view(), name='supplier-part-edit'),
    url(r'delete/?', views.SupplierPartDelete.as_view(), name='supplier-part-delete'),

    url('^.*$', views.SupplierPartDetail.as_view(), name='supplier-part-detail'),
]

supplier_urls = [
    url(r'part/(?P<pk>\d+)/', include(supplier_part_detail_urls)),

    url(r'part/new/?', views.SupplierPartCreate.as_view(), name='supplier-part-create'),

    url(r'new/?', views.SupplierCreate.as_view(), name='supplier-create'),

    url(r'^(?P<pk>\d+)/', include(supplier_detail_urls)),

    url(r'', views.SupplierIndex.as_view(), name='supplier-index'),

    # Redirect any other patterns
    url(r'^.*$', RedirectView.as_view(url='', permanent=False), name='supplier-index'),
]
