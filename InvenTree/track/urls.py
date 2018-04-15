from django.conf.urls import url, include

from . import views

"""
TODO - Implement JSON API for part serial number tracking
part_track_api_urls = [
    url(r'^(?P<pk>[0-9]+)/?$', api.PartTrackingDetail.as_view(), name='parttrackinginfo-detail'),

    url(r'^\?.*/?$', api.PartTrackingList.as_view()),
    url(r'^$', api.PartTrackingList.as_view())
]

unique_api_urls = [

    # Detail for a single unique part
    url(r'^(?P<pk>[0-9]+)/?$', api.UniquePartDetail.as_view(), name='uniquepart-detail'),

    # List all unique parts, with optional filters
    url(r'^\?.*/?$', api.UniquePartList.as_view()),
    url(r'^$', api.UniquePartList.as_view()),
]
"""

track_detail_urls = [
    url(r'^edit/?', views.TrackEdit.as_view(), name='track-edit'),
    url(r'^delete/?', views.TrackDelete.as_view(), name='track-delete'),

    url('^.*$', views.TrackDetail.as_view(), name='track-detail'),
]

tracking_urls = [
    # Detail view
    url(r'^(?P<pk>\d+)/', include(track_detail_urls)),

    # Create a new tracking item
    url(r'^new/?', views.TrackCreate.as_view(), name='track-create'),

    # List ALL tracked items
    url(r'^.*$', views.TrackIndex.as_view(), name='track-index'),
]
