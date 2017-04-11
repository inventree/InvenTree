from django.conf.urls import url

from . import views

urlpatterns = [
    # Single part detail
    url(r'^(?P<pk>[0-9]+)/$', views.PartDetail.as_view()),

    # Part category detail
    url(r'^category/(?P<pk>[0-9]+)/$', views.PartCategoryDetail.as_view()),

    # List of top-level categories
    url(r'^category/$', views.PartCategoryList.as_view()),

    # List of all parts
    url(r'^$', views.PartList.as_view())
]
