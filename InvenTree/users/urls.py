from django.conf.urls import url

from . import views

user_urls = [
    url(r'^(?P<pk>[0-9]+)/?$', views.UserDetail.as_view(), name='user-detail'),

    url(r'token', views.GetAuthToken.as_view(), name='api-token'),

    url(r'^$', views.UserList.as_view()),
]
