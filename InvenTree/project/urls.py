from django.conf.urls import url, include

from . import views

projectpartpatterns = [
    # Detail of a single project part
    url(r'^(?P<pk>[0-9]+)/?$', views.ProjectPartDetail.as_view(), name='projectpart-detail'),

    # List project parts, with optional filters
    url(r'^\?.*/?$', views.ProjectPartsList.as_view()),
    url(r'^$', views.ProjectPartsList.as_view()),
]

projectcategorypatterns = [
    # Detail of a single project category
    url(r'^(?P<pk>[0-9]+)/?$', views.ProjectCategoryDetail.as_view(), name='projectcategory-detail'),

    # List of project categories, with filters
    url(r'^\?.*/?$', views.ProjectCategoryList.as_view()),
    url(r'^$', views.ProjectCategoryList.as_view()),
]

urlpatterns = [
    # Individual project URL
    url(r'^(?P<pk>[0-9]+)/?$', views.ProjectDetail.as_view(), name='project-detail'),

    # List of all projects
    url(r'^\?.*/?$', views.ProjectList.as_view()),
    url(r'^$', views.ProjectList.as_view()),

    # Project parts
    url(r'^parts/', include(projectpartpatterns)),

    # Project categories
    url(r'^category/', include(projectcategorypatterns)),
]
