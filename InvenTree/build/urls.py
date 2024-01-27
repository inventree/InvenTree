"""URL lookup for Build app."""

from django.urls import include, path

from . import views


build_urls = [

    path('<int:pk>/', include([
        path('', views.BuildDetail.as_view(), name='build-detail'),
    ])),

    path('', views.BuildIndex.as_view(), name='build-index'),
]
