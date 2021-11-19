"""
Provides a JSON API for common components.
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

from django.http.response import HttpResponse
from django.utils.decorators import method_decorator
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from django.conf.urls import url, include

from rest_framework.views import APIView
from rest_framework.exceptions import NotAcceptable, NotFound
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, permissions
from django_q.tasks import async_task

import common.models
import common.serializers
from InvenTree.helpers import inheritors


class CsrfExemptMixin(object):
    """
    Exempts the view from CSRF requirements.
    """

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(CsrfExemptMixin, self).dispatch(*args, **kwargs)


class WebhookView(CsrfExemptMixin, APIView):
    """
    Endpoint for receiving webhooks.
    """
    authentication_classes = []
    permission_classes = []
    model_class = common.models.WebhookEndpoint
    run_async = False

    def post(self, request, endpoint, *args, **kwargs):
        # get webhook definition
        self._get_webhook(endpoint, request, *args, **kwargs)

        # check headers
        headers = request.headers
        try:
            payload = json.loads(request.body)
        except json.decoder.JSONDecodeError as error:
            raise NotAcceptable(error.msg)

        # validate
        self.webhook.validate_token(payload, headers, request)
        # process data
        message = self.webhook.save_data(payload, headers, request)
        if self.run_async:
            async_task(self._process_payload, message.id)
        else:
            self._process_result(
                self.webhook.process_payload(message, payload, headers),
                message,
            )

        # return results
        data = self.webhook.get_return(payload, headers, request)
        return HttpResponse(data)

    def _process_payload(self, message_id):
        message = common.models.WebhookMessage.objects.get(message_id=message_id)
        self._process_result(
            self.webhook.process_payload(message, message.body, message.header),
            message,
        )

    def _process_result(self, result, message):
        if result:
            message.worked_on = result
            message.save()
        else:
            message.delete()

    def _escalate_object(self, obj):
        classes = inheritors(obj.__class__)
        for cls in classes:
            mdl_name = cls._meta.model_name
            if hasattr(obj, mdl_name):
                return getattr(obj, mdl_name)
        return obj

    def _get_webhook(self, endpoint, request, *args, **kwargs):
        try:
            webhook = self.model_class.objects.get(endpoint_id=endpoint)
            self.webhook = self._escalate_object(webhook)
            self.webhook.init(request, *args, **kwargs)
            return self.webhook.process_webhook()
        except self.model_class.DoesNotExist:
            raise NotFound()


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


common_api_urls = [
    path('webhook/<slug:endpoint>/', WebhookView.as_view(), name='api-webhook'),

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

]
