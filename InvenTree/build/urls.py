"""URL lookup for Build app."""

from django.urls import include, re_path

from . import views

build_detail_urls = [
    re_path(r'^delete/', views.BuildDelete.as_view(), name='build-delete'),

    re_path(r'^.*$', views.BuildDetail.as_view(), name='build-detail'),
]

build_urls = [

    re_path(r'^(?P<pk>\d+)/', include(build_detail_urls)),

    re_path(r'.*$', views.BuildIndex.as_view(), name='build-index'),
]
