"""URL lookup for Build app."""

from django.urls import include, path, re_path

from . import views


build_urls = [

    path(r'<int:pk>/', include([
        re_path(r'^.*$', views.BuildDetail.as_view(), name='build-detail'),
    ])),

    re_path(r'.*$', views.BuildIndex.as_view(), name='build-index'),
]
