from django.conf.urls import url, include

from . import views

build_detail_urls = [
    url(r'^edit/?', views.BuildUpdate.as_view(), name='build-edit'),
    url(r'^allocate/?', views.BuildAllocate.as_view(), name='build-allocate'),
    url(r'^cancel/?', views.BuildCancel.as_view(), name='build-cancel'),

    url(r'^.*$', views.BuildDetail.as_view(), name='build-detail'),
]

build_urls = [
    url(r'new/?', views.BuildCreate.as_view(), name='build-create'),

    url(r'^(?P<pk>\d+)/', include(build_detail_urls)),

    url(r'.*$', views.BuildIndex.as_view(), name='build-index'),
]
