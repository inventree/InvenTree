from django.conf.urls import url, include

from . import views

infopatterns = [
    url(r'^(?P<pk>[0-9]+)/?$', views.PartTrackingDetail.as_view(), name='tracking-detail'),

    url(r'^\?.*/?$', views.PartTrackingList.as_view(), name='tracking-list'),
    url(r'^$', views.PartTrackingList.as_view(), name='tracking-list')
]

urlpatterns = [
    url(r'info/', include(infopatterns)),

    # Detail for a single unique part
    url(r'^(?P<pk>[0-9]+)/?$', views.UniquePartDetail.as_view(), name='unique-detail'),

    # List all unique parts, with optional filters
    url(r'^\?.*/?$', views.UniquePartList.as_view(), name='unique-list'),
    url(r'^$', views.UniquePartList.as_view(), name='unique-list'),
]
