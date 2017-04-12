from django.conf.urls import url

from . import views

urlpatterns = [
    # Single project detail
    url(r'^(?P<pk>[0-9]+)/$', views.ProjectDetail.as_view()),

    # Parts associated with a project
    url(r'^(?P<pk>[0-9]+)/parts$', views.ProjectPartsList.as_view()),

    # List of all projects
    url(r'^$', views.ProjectList.as_view()),

    # List of top-level project categories
    url(r'^category/$', views.ProjectCategoryList.as_view()),

    # Detail of a single project category
    url(r'^category/(?P<pk>[0-9]+)/$', views.ProjectCategoryDetail.as_view())
]
