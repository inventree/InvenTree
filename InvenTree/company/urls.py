"""
URL lookup for Company app
"""

from django.conf.urls import url, include

from . import views


company_detail_urls = [
    url(r'edit/?', views.CompanyEdit.as_view(), name='company-edit'),
    url(r'delete/?', views.CompanyDelete.as_view(), name='company-delete'),

    # url(r'orders/?', views.CompanyDetail.as_view(template_name='company/orders.html'), name='company-detail-orders'),

    url(r'^supplier-parts/', views.CompanyDetail.as_view(template_name='company/detail_supplier_part.html'), name='company-detail-supplier-parts'),
    url(r'^manufacturer-parts/', views.CompanyDetail.as_view(template_name='company/detail_manufacturer_part.html'), name='company-detail-manufacturer-parts'),
    url(r'^stock/', views.CompanyDetail.as_view(template_name='company/detail_stock.html'), name='company-detail-stock'),
    url(r'^purchase-orders/', views.CompanyDetail.as_view(template_name='company/purchase_orders.html'), name='company-detail-purchase-orders'),
    url(r'^assigned-stock/', views.CompanyDetail.as_view(template_name='company/assigned_stock.html'), name='company-detail-assigned-stock'),
    url(r'^sales-orders/', views.CompanyDetail.as_view(template_name='company/sales_orders.html'), name='company-detail-sales-orders'),
    url(r'^notes/', views.CompanyNotes.as_view(), name='company-notes'),

    url(r'^thumbnail/', views.CompanyImage.as_view(), name='company-image'),
    url(r'^thumb-download/', views.CompanyImageDownloadFromURL.as_view(), name='company-image-download'),

    # Any other URL
    url(r'^.*$', views.CompanyDetail.as_view(), name='company-detail'),
]


company_urls = [

    url(r'new/supplier/', views.CompanyCreate.as_view(), name='supplier-create'),
    url(r'new/manufacturer/', views.CompanyCreate.as_view(), name='manufacturer-create'),
    url(r'new/customer/', views.CompanyCreate.as_view(), name='customer-create'),
    url(r'new/?', views.CompanyCreate.as_view(), name='company-create'),

    url(r'^(?P<pk>\d+)/', include(company_detail_urls)),

    url(r'suppliers/', views.CompanyIndex.as_view(), name='supplier-index'),
    url(r'manufacturers/', views.CompanyIndex.as_view(), name='manufacturer-index'),
    url(r'customers/', views.CompanyIndex.as_view(), name='customer-index'),

    # Redirect any other patterns to the 'company' index which displays all companies
    url(r'^.*$', views.CompanyIndex.as_view(), name='company-index'),
]

price_break_urls = [
    url('^new/', views.PriceBreakCreate.as_view(), name='price-break-create'),

    url(r'^(?P<pk>\d+)/edit/', views.PriceBreakEdit.as_view(), name='price-break-edit'),
    url(r'^(?P<pk>\d+)/delete/', views.PriceBreakDelete.as_view(), name='price-break-delete'),
]

manufacturer_part_detail_urls = [
    url(r'^edit/?', views.ManufacturerPartEdit.as_view(), name='manufacturer-part-edit'),
    
    url(r'^suppliers/', views.ManufacturerPartDetail.as_view(template_name='company/manufacturer_part_suppliers.html'), name='manufacturer-part-suppliers'),

    url('^.*$', views.ManufacturerPartDetail.as_view(template_name='company/manufacturer_part_suppliers.html'), name='manufacturer-part-detail'),
]

manufacturer_part_urls = [
    url(r'^new/?', views.ManufacturerPartCreate.as_view(), name='manufacturer-part-create'),

    url(r'delete/', views.ManufacturerPartDelete.as_view(), name='manufacturer-part-delete'),

    url(r'^(?P<pk>\d+)/', include(manufacturer_part_detail_urls)),
]

supplier_part_detail_urls = [
    url(r'^edit/?', views.SupplierPartEdit.as_view(), name='supplier-part-edit'),

    url(r'^manufacturers/', views.SupplierPartDetail.as_view(template_name='company/supplier_part_manufacturers.html'), name='supplier-part-manufacturers'),
    url(r'^pricing/', views.SupplierPartDetail.as_view(template_name='company/supplier_part_pricing.html'), name='supplier-part-pricing'),
    url(r'^orders/', views.SupplierPartDetail.as_view(template_name='company/supplier_part_orders.html'), name='supplier-part-orders'),
    url(r'^stock/', views.SupplierPartDetail.as_view(template_name='company/supplier_part_stock.html'), name='supplier-part-stock'),

    url('^.*$', views.SupplierPartDetail.as_view(template_name='company/supplier_part_pricing.html'), name='supplier-part-detail'),
]

supplier_part_urls = [
    url(r'^new/?', views.SupplierPartCreate.as_view(), name='supplier-part-create'),

    url(r'delete/', views.SupplierPartDelete.as_view(), name='supplier-part-delete'),

    url(r'^(?P<pk>\d+)/', include(supplier_part_detail_urls)),
]
