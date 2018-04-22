from django.conf.urls import url, include
from django.views.generic.base import RedirectView

from . import views


company_detail_urls = [
    url(r'edit/?', views.CompanyEdit.as_view(), name='company-edit'),
    url(r'delete/?', views.CompanyDelete.as_view(), name='company-delete'),

    # url(r'orders/?', views.CompanyDetail.as_view(template_name='company/orders.html'), name='company-detail-orders'),

    url(r'^.*$', views.CompanyDetail.as_view(), name='company-detail'),
]


company_urls = [

    url(r'new/?', views.CompanyCreate.as_view(), name='company-create'),

    url(r'^(?P<pk>\d+)/', include(company_detail_urls)),

    url(r'', views.CompanyIndex.as_view(), name='company-index'),

    # Redirect any other patterns
    url(r'^.*$', RedirectView.as_view(url='', permanent=False), name='company-index'),
]
