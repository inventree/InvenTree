from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^(?P<pk>[0-9]+)/?$', views.LocationDetail.as_view(), name='stocklocation-detail'),

    url(r'^\?.*/?$', views.LocationList.as_view()),

    url(r'^$', views.LocationList.as_view())
]
