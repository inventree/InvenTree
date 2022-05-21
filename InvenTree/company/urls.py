"""
URL lookup for Company app
"""

from django.urls import include, re_path

from . import views

company_detail_urls = [

    re_path(r'^thumb-download/', views.CompanyImageDownloadFromURL.as_view(), name='company-image-download'),

    # Any other URL
    re_path(r'^.*$', views.CompanyDetail.as_view(), name='company-detail'),
]


company_urls = [

    re_path(r'^(?P<pk>\d+)/', include(company_detail_urls)),

    re_path(r'suppliers/', views.CompanyIndex.as_view(), name='supplier-index'),
    re_path(r'manufacturers/', views.CompanyIndex.as_view(), name='manufacturer-index'),
    re_path(r'customers/', views.CompanyIndex.as_view(), name='customer-index'),

    # Redirect any other patterns to the 'company' index which displays all companies
    re_path(r'^.*$', views.CompanyIndex.as_view(), name='company-index'),
]

manufacturer_part_urls = [

    re_path(r'^(?P<pk>\d+)/', views.ManufacturerPartDetail.as_view(template_name='company/manufacturer_part.html'), name='manufacturer-part-detail'),
]

supplier_part_urls = [
    re_path(r'^(?P<pk>\d+)/', views.SupplierPartDetail.as_view(template_name='company/supplier_part.html'), name='supplier-part-detail'),
]
