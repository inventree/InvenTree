from django.conf.urls import url, include
from django.views.generic.base import RedirectView

from . import views
from . import api

app_nam='part'

# URL list for part category API
part_cat_api_urls = [

    # Part category detail
    url(r'^(?P<pk>[0-9]+)/?$', api.PartCategoryDetail.as_view(), name='partcategory-detail'),

    # List of top-level categories
    url(r'^\?*.*/?$', api.PartCategoryList.as_view()),
    url(r'^$', api.PartCategoryList.as_view())
]


# URL list for part API
part_api_urls = [

    # Individual part
    url(r'^(?P<pk>[0-9]+)/?$', api.PartDetail.as_view(), name='part-detail'),

    # List parts with optional filters
    url(r'^\?.*/?$', api.PartList.as_view()),
    url(r'^$', api.PartList.as_view()),
]

bom_api_urls = [
    # Bom Item detail
    url(r'^(?P<pk>[0-9]+)/?$', api.BomItemDetail.as_view(), name='bomitem-detail'),

    # List of top-level categories
    url(r'^\?*.*/?$', api.BomItemList.as_view()),
    url(r'^$', api.BomItemList.as_view())
]

part_detail_urls = [
    url(r'^track/?', views.track, name='part-track'),
    url(r'^bom/?', views.bom, name='part-bom'),
    url(r'^stock/?', views.stock, name='part-stock'),
    url(r'^suppliers/?', views.suppliers, name='part-suppliers'),
    url('', views.detail, name='part-detail'),
]

# URL list for part web interface
part_urls = [
    # Individual
    url(r'^(?P<pk>\d+)/', include(part_detail_urls)),

    url('list', views.index, name='part-index'),
    # ex: /part/5/

     url(r'^.*$', RedirectView.as_view(url='list', permanent=False), name='part-index'),
]



"""
part_param_urls = [
    # Detail of a single part parameter
    url(r'^(?P<pk>[0-9]+)/?$', views.PartParamDetail.as_view(), name='partparameter-detail'),

    # Parameters associated with a particular part
    url(r'^\?.*/?$', views.PartParamList.as_view()),
    url(r'^$', views.PartParamList.as_view()),
]

part_param_template_urls = [
    # Detail of a single part field template
    url(r'^(?P<pk>[0-9]+)/?$', views.PartTemplateDetail.as_view(), name='partparametertemplate-detail'),

    # List all part field templates
    url(r'^\?.*/?$', views.PartTemplateList.as_view()),
    url(r'^$', views.PartTemplateList.as_view())
]
"""


