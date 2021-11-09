"""
Provides a JSON API for common components.
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url, include

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics

import common.models
import common.serializers


class SettingsList(generics.ListAPIView):

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    ordering_fields = [
        'pk',
        'key',
        'name',
    ]

    search_fields = [
        'key',
    ]


class GlobalSettingsList(SettingsList):
    """
    API endpoint for accessing a list of global settings objects
    """

    queryset = common.models.InvenTreeSetting.objects.all()
    serializer_class = common.serializers.GlobalSettingsSerializer



class UserSettingsList(SettingsList):
    """
    API endpoint for accessing a list of user settings objects
    """

    queryset = common.models.InvenTreeUserSetting.objects.all()
    serializer_class = common.serializers.UserSettingsSerializer

    def filter_queryset(self, queryset):
        """
        Only list settings which apply to the current user        
        """

        try:
            user = self.request.user
        except AttributeError:
            return common.models.InvenTreeUserSetting.objects.none()

        queryset = super().filter_queryset(queryset)

        queryset = queryset.filter(user=user)

        return queryset


common_api_urls = [

    # User settings
    url(r'^user/', include([
        # User Settings Detail

        # User Settings List
        url(r'^.*$', UserSettingsList.as_view(), name='api-user-setting-list'),
    ])),

    # Global settings
    url(r'^global/', include([
        # Global Settings Detail

        # Global Settings List
        url(r'^.*$', GlobalSettingsList.as_view(), name='api-global-setting-list'),
    ]))

]
