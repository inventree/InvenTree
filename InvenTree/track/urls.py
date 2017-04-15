from django.conf.urls import url

from . import views

part_track_urls = [
    url(r'^(?P<pk>[0-9]+)/?$', views.PartTrackingDetail.as_view(), name='parttrackinginfo-detail'),

    url(r'^\?.*/?$', views.PartTrackingList.as_view()),
    url(r'^$', views.PartTrackingList.as_view())
]

unique_urls = [

    # Detail for a single unique part
    url(r'^(?P<pk>[0-9]+)/?$', views.UniquePartDetail.as_view(), name='uniquepart-detail'),

    # List all unique parts, with optional filters
    url(r'^\?.*/?$', views.UniquePartList.as_view()),
    url(r'^$', views.UniquePartList.as_view()),
]
