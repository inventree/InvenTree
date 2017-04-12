from django.conf.urls import url, include

from . import views

""" URL patterns associated with part categories:
/category       -> List all top-level categories
/category/<pk>  -> Detail view of given category
/category/new   -> Create a new category
"""
categorypatterns = [

    # Part category detail
    url(r'^category/(?P<pk>[0-9]+)/$', views.PartCategoryDetail.as_view()),

    # List of top-level categories
    url(r'^$', views.PartCategoryList.as_view())
]

""" URL patterns associated with a particular part:
/part/<pk>              -> Detail view of a given part
/part/<pk>/parameters   -> List parameters associated with a part
"""
partdetailpatterns = [
    # Single part detail
    url(r'^$', views.PartDetail.as_view()),

    # View part parameters
    url(r'parameters/$', views.PartParameters.as_view())
]

""" Top-level URL patterns for the Part app:
/part/          -> List all parts
/part/new       -> Create a new part
/part/<pk>      -> (refer to partdetailpatterns)
/part/category  -> (refer to categorypatterns)
"""
urlpatterns = [
    # Individual part
    url(r'^(?P<pk>[0-9]+)/', include(partdetailpatterns)),

    # Part categories
    url(r'^category/', views.PartCategoryList.as_view()),

    # List of all parts
    url(r'^$', views.PartList.as_view())
]
