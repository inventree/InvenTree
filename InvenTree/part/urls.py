from django.conf.urls import url, include

from . import views

""" URL patterns associated with part categories:
/category       -> List all top-level categories
/category/<pk>  -> Detail view of given category
/category/new   -> Create a new category
"""
categorypatterns = [

    # Part category detail
    url(r'^(?P<pk>[0-9]+)/?$', views.PartCategoryDetail.as_view(), name='part-category-detail'),

    # List of top-level categories
    url(r'^\?*.*/?$', views.PartCategoryList.as_view(), name='part-category-list'),
    url(r'^$', views.PartCategoryList.as_view(), name='part-category-list')
]

partparampatterns = [
    # Detail of a single part parameter
    url(r'^(?P<pk>[0-9]+)/?$', views.PartParamDetail.as_view(), name='part-parameter-detail'),

    # Parameters associated with a particular part
    url(r'^\?.*/?$', views.PartParamList.as_view(), name='part-parameter-list'),
    url(r'^$', views.PartParamList.as_view(), name='part-parameter-list'),
]

parttemplatepatterns = [
    # Detail of a single part field template
    url(r'^(?P<pk>[0-9]+)/?$', views.PartTemplateDetail.as_view(), name='part-template-detail'),

    # List all part field templates
    url(r'^\?.*/?$', views.PartTemplateList.as_view(), name='part-template-list'),
    url(r'^$', views.PartTemplateList.as_view(), name='part-template-list')
]

""" Top-level URL patterns for the Part app:
/part/          -> List all parts
/part/new       -> Create a new part
/part/<pk>      -> (refer to partdetailpatterns)
/part/category  -> (refer to categorypatterns)
"""
urlpatterns = [
    # Individual part
    url(r'^(?P<pk>[0-9]+)/?$', views.PartDetail.as_view(), name='part-detail'),

    # Part categories
    url(r'^category/', include(categorypatterns)),

    # Part parameters
    url(r'^parameters/', include(partparampatterns)),

    # Part templates
    url(r'^templates/', include(parttemplatepatterns)),

    # List parts with optional filters
    url(r'^\?.*/?$', views.PartList.as_view(), name='part-list'),
    url(r'^$', views.PartList.as_view(), name='part-list'),
]
