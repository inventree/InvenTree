from django.conf.urls import url, include

from . import views

projectpartpatterns = [
    # Detail of a single project part
    url(r'^(?P<pk>[0-9]+)/?$', views.ProjectPartDetail.as_view(), name='project-part-detail'),

    # List project parts, with optional filters
    url(r'^\?.*/?$', views.ProjectPartsList.as_view(), name='project-part-list'),
    url(r'^$', views.ProjectPartsList.as_view(), name='project-part-list'),
]

projectcategorypatterns = [
    # Detail of a single project category
    url(r'^(?P<pk>[0-9]+)/?$', views.ProjectCategoryDetail.as_view(), name='project-category-detail'),

    # List of project categories, with filters
    url(r'^\?.*/?$', views.ProjectCategoryList.as_view(), name='project-category-list'),
    url(r'^$', views.ProjectCategoryList.as_view(), name='project-category-list'),
]

urlpatterns = [
    # Individual project URL
    url(r'^(?P<pk>[0-9]+)/?$', views.ProjectDetail.as_view(), name='project-detail'),

    # List of all projects
    url(r'^\?.*/?$', views.ProjectList.as_view(), name='project-list'),
    url(r'^$', views.ProjectList.as_view(), name='project-list'),

    # Project parts
    url(r'^parts/', include(projectpartpatterns)),

    # Project categories
    url(r'^category/', include(projectcategorypatterns)),
]
