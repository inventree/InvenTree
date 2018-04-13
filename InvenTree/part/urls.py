from django.conf.urls import url, include
from django.views.generic.base import RedirectView

from . import views

app_nam='part'

# URL list for part category API
part_cat_api_urls = [

    # Part category detail
    url(r'^(?P<pk>[0-9]+)/?$', views.PartCategoryDetail.as_view(), name='partcategory-detail'),

    # List of top-level categories
    url(r'^\?*.*/?$', views.PartCategoryList.as_view()),
    url(r'^$', views.PartCategoryList.as_view())
]


# URL list for part API
part_api_urls = [

    # Individual part
    url(r'^(?P<pk>[0-9]+)/?$', views.PartDetail.as_view(), name='part-detail'),

    # List parts with optional filters
    url(r'^\?.*/?$', views.PartList.as_view()),
    url(r'^$', views.PartList.as_view()),
]

part_detail_urls = [

    url(r'^bom/?', views.bom, name='bom'),
    url(r'^stock/?', views.stock, name='stock'),
    url('', views.detail, name='detail'),
]

# URL list for part web interface
part_urls = [
    # Individual
    url(r'^(?P<pk>\d+)/', include(part_detail_urls)),

    url('list', views.index, name='index'),
    # ex: /part/5/

     url(r'^.*$', RedirectView.as_view(url='list', permanent=False), name='index'),
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


