"""URL lookup for Build app."""

from django.urls import include, re_path

from . import views


build_urls = [

    re_path(r'^(?P<pk>\d+)/', include([
        re_path(r'^.*$', views.BuildDetail.as_view(), name='build-detail'),
    ])),

    re_path(r'.*$', views.BuildIndex.as_view(), name='build-index'),
]
