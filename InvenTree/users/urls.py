from django.conf.urls import url

from . import api

user_urls = [
    url(r'^(?P<pk>[0-9]+)/?$', api.UserDetail.as_view(), name='user-detail'),

    url(r'roles/?$', api.RoleDetails.as_view(), name='api-user-roles'),
    url(r'token/?$', api.GetAuthToken.as_view(), name='api-token'),

    url(r'^$', api.UserList.as_view()),
]
