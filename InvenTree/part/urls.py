from django.conf.urls import url

from . import views

part_cat_urls = [

    # Part category detail
    url(r'^(?P<pk>[0-9]+)/?$', views.PartCategoryDetail.as_view(), name='partcategory-detail'),

    # List of top-level categories
    url(r'^\?*.*/?$', views.PartCategoryList.as_view()),
    url(r'^$', views.PartCategoryList.as_view())
]

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

part_urls = [

    # Individual part
    url(r'^(?P<pk>[0-9]+)/?$', views.PartDetail.as_view(), name='part-detail'),

    # List parts with optional filters
    url(r'^\?.*/?$', views.PartList.as_view()),
    url(r'^$', views.PartList.as_view()),
]
