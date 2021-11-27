"""
Provides a JSON API for common components.
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url, include

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, permissions

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


class GlobalSettingsPermissions(permissions.BasePermission):
    """
    Special permission class to determine if the user is "staff"
    """

    def has_permission(self, request, view):
        """
        Check that the requesting user is 'admin'
        """

        try:
            user = request.user

            return user.is_staff
        except AttributeError:
            return False


class GlobalSettingsDetail(generics.RetrieveUpdateAPIView):
    """
    Detail view for an individual "global setting" object.

    - User must have 'staff' status to view / edit
    """

    queryset = common.models.InvenTreeSetting.objects.all()
    serializer_class = common.serializers.GlobalSettingsSerializer

    permission_classes = [
        GlobalSettingsPermissions,
    ]


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


class UserSettingsPermissions(permissions.BasePermission):
    """
    Special permission class to determine if the user can view / edit a particular setting
    """

    def has_object_permission(self, request, view, obj):

        try:
            user = request.user
        except AttributeError:
            return False

        return user == obj.user


class UserSettingsDetail(generics.RetrieveUpdateAPIView):
    """
    Detail view for an individual "user setting" object

    - User can only view / edit settings their own settings objects
    """

    queryset = common.models.InvenTreeUserSetting.objects.all()
    serializer_class = common.serializers.UserSettingsSerializer

    permission_classes = [
        UserSettingsPermissions,
    ]


class NotificationList(generics.ListAPIView):
    queryset = common.models.NotificationMessage.objects.all()
    serializer_class = common.serializers.NotificationMessageSerializer

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    ordering_fields = [
        #'age',  # TODO enable ordering by age
        'category',
        'name',
    ]

    search_fields = [
        'name',
        'message',
    ]

    def filter_queryset(self, queryset):
        """
        Only list notifications which apply to the current user
        """

        try:
            user = self.request.user
        except AttributeError:
            return common.models.NotificationMessage.objects.none()

        queryset = super().filter_queryset(queryset)
        queryset = queryset.filter(user=user)
        return queryset


class NotificationDetail(generics.RetrieveDestroyAPIView):
    """
    Detail view for an individual notification object

    - User can only view / delete their own notification objects
    """

    queryset = common.models.NotificationMessage.objects.all()
    serializer_class = common.serializers.NotificationMessageSerializer

    permission_classes = [
        UserSettingsPermissions,
    ]


common_api_urls = [

    # User settings
    url(r'^user/', include([
        # User Settings Detail
        url(r'^(?P<pk>\d+)/', UserSettingsDetail.as_view(), name='api-user-setting-detail'),

        # User Settings List
        url(r'^.*$', UserSettingsList.as_view(), name='api-user-setting-list'),
    ])),

    # Global settings
    url(r'^global/', include([
        # Global Settings Detail
        url(r'^(?P<pk>\d+)/', GlobalSettingsDetail.as_view(), name='api-global-setting-detail'),

        # Global Settings List
        url(r'^.*$', GlobalSettingsList.as_view(), name='api-global-setting-list'),
    ])),

    # Notifications
    url(r'^notifications/', include([
        url(r'^(?P<pk>\d+)/', NotificationDetail.as_view(), name='api-notifications-detail'),
        url(r'^.*$', NotificationList.as_view(), name='api-notifications-list'),
    ])),

]
