"""
URL lookup for Company app
"""


from django.conf.urls import url, include
from django.views.generic.base import RedirectView

from . import views


company_detail_urls = [
    url(r'edit/?', views.CompanyEdit.as_view(), name='company-edit'),
    url(r'delete/?', views.CompanyDelete.as_view(), name='company-delete'),

    # url(r'orders/?', views.CompanyDetail.as_view(template_name='company/orders.html'), name='company-detail-orders'),

    url(r'parts/?', views.CompanyDetail.as_view(template_name='company/detail_part.html'), name='company-detail-parts'),
    url(r'stock/?', views.CompanyDetail.as_view(template_name='company/detail_stock.html'), name='company-detail-stock'),
    url(r'purchase-orders/?', views.CompanyDetail.as_view(template_name='company/detail_purchase_orders.html'), name='company-detail-purchase-orders'),

    url(r'thumbnail/?', views.CompanyImage.as_view(), name='company-image'),

    # Any other URL
    url(r'^.*$', views.CompanyDetail.as_view(), name='company-detail'),
]


company_urls = [

    url(r'new/?', views.CompanyCreate.as_view(), name='company-create'),

    url(r'^(?P<pk>\d+)/', include(company_detail_urls)),

    url(r'', views.CompanyIndex.as_view(), name='company-index'),

    # Redirect any other patterns
    url(r'^.*$', RedirectView.as_view(url='', permanent=False), name='company-index'),
]

price_break_urls = [
    url('^new/', views.PriceBreakCreate.as_view(), name='price-break-create'),

    url(r'^(?P<pk>\d+)/edit/', views.PriceBreakEdit.as_view(), name='price-break-edit'),
    url(r'^(?P<pk>\d+)/delete/', views.PriceBreakDelete.as_view(), name='price-break-delete'),
]

supplier_part_detail_urls = [
    url(r'edit/?', views.SupplierPartEdit.as_view(), name='supplier-part-edit'),

    url('^.*$', views.SupplierPartDetail.as_view(), name='supplier-part-detail'),
]

supplier_part_urls = [
    url(r'^new/?', views.SupplierPartCreate.as_view(), name='supplier-part-create'),

    url(r'delete/', views.SupplierPartDelete.as_view(), name='supplier-part-delete'),

    url(r'^(?P<pk>\d+)/', include(supplier_part_detail_urls)),
]
