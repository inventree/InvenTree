"""
URL lookup for Build app
"""

from django.conf.urls import url, include

from . import views

build_detail_urls = [
    url(r'^edit/', views.BuildUpdate.as_view(), name='build-edit'),
    url(r'^allocate/', views.BuildAllocate.as_view(), name='build-allocate'),
    url(r'^cancel/', views.BuildCancel.as_view(), name='build-cancel'),
    url(r'^delete/', views.BuildDelete.as_view(), name='build-delete'),
    url(r'^create-output/', views.BuildOutputCreate.as_view(), name='build-output-create'),
    url(r'^delete-output/', views.BuildOutputDelete.as_view(), name='build-output-delete'),
    url(r'^complete-output/?', views.BuildOutputComplete.as_view(), name='build-output-complete'),
    url(r'^auto-allocate/?', views.BuildAutoAllocate.as_view(), name='build-auto-allocate'),
    url(r'^unallocate/', views.BuildUnallocate.as_view(), name='build-unallocate'),
    url(r'^complete/', views.BuildComplete.as_view(), name='build-complete'),

    url(r'^notes/', views.BuildNotes.as_view(), name='build-notes'),

    url(r'^attachments/', views.BuildDetail.as_view(template_name='build/attachments.html'), name='build-attachments'),
    url(r'^output/', views.BuildDetail.as_view(template_name='build/build_output.html'), name='build-output'),

    url(r'^.*$', views.BuildDetail.as_view(), name='build-detail'),
]

build_urls = [
    url(r'item/', include([
        url(r'^(?P<pk>\d+)/', include([
            url('^edit/?', views.BuildItemEdit.as_view(), name='build-item-edit'),
            url('^delete/?', views.BuildItemDelete.as_view(), name='build-item-delete'),
        ])),
        url('^new/', views.BuildItemCreate.as_view(), name='build-item-create'),
    ])),

    url('^attachment/', include([
        url('^new/', views.BuildAttachmentCreate.as_view(), name='build-attachment-create'),
        url(r'^(?P<pk>\d+)/edit/', views.BuildAttachmentEdit.as_view(), name='build-attachment-edit'),
        url(r'^(?P<pk>\d+)/delete/', views.BuildAttachmentDelete.as_view(), name='build-attachment-delete'),
    ])),

    url(r'new/', views.BuildCreate.as_view(), name='build-create'),

    url(r'^(?P<pk>\d+)/', include(build_detail_urls)),

    url(r'.*$', views.BuildIndex.as_view(), name='build-index'),
]
