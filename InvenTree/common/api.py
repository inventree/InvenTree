"""Provides a JSON API for common components."""

import json

from django.http.response import HttpResponse
from django.urls import include, path, re_path
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_exempt

from django_filters.rest_framework import DjangoFilterBackend
from django_q.tasks import async_task
from rest_framework import filters, permissions, serializers
from rest_framework.exceptions import NotAcceptable, NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

import common.models
import common.serializers
from InvenTree.api import BulkDeleteMixin
from InvenTree.helpers import inheritors
from InvenTree.mixins import (CreateAPI, ListAPI, ListCreateAPI, RetrieveAPI,
                              RetrieveUpdateAPI, RetrieveUpdateDestroyAPI)
from plugin.models import NotificationUserSetting, PluginConfig
from plugin.serializers import NotificationUserSettingSerializer


class CsrfExemptMixin(object):
    """Exempts the view from CSRF requirements."""

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        """Overwrites dispatch to be extempt from csrf checks."""
        return super().dispatch(*args, **kwargs)


class WebhookView(CsrfExemptMixin, APIView):
    """Endpoint for receiving webhooks."""
    authentication_classes = []
    permission_classes = []
    model_class = common.models.WebhookEndpoint
    run_async = False

    def post(self, request, endpoint, *args, **kwargs):
        """Process incomming webhook."""
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


class SettingsList(ListAPI):
    """Generic ListView for settings.

    This is inheritted by all list views for settings.
    """

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
    """API endpoint for accessing a list of global settings objects."""

    queryset = common.models.InvenTreeSetting.objects.all()
    serializer_class = common.serializers.GlobalSettingsSerializer


class GlobalSettingsPermissions(permissions.BasePermission):
    """Special permission class to determine if the user is "staff"."""

    def has_permission(self, request, view):
        """Check that the requesting user is 'admin'."""
        try:
            user = request.user

            if request.method in ['GET', 'HEAD', 'OPTIONS']:
                return True
            else:
                # Any other methods require staff access permissions
                return user.is_staff

        except AttributeError:  # pragma: no cover
            return False


class GlobalSettingsDetail(RetrieveUpdateAPI):
    """Detail view for an individual "global setting" object.

    - User must have 'staff' status to view / edit
    """

    lookup_field = 'key'
    queryset = common.models.InvenTreeSetting.objects.all()
    serializer_class = common.serializers.GlobalSettingsSerializer

    def get_object(self):
        """Attempt to find a global setting object with the provided key."""
        key = self.kwargs['key']

        if key not in common.models.InvenTreeSetting.SETTINGS.keys():
            raise NotFound()

        return common.models.InvenTreeSetting.get_setting_object(key)

    permission_classes = [
        permissions.IsAuthenticated,
        GlobalSettingsPermissions,
    ]


class UserSettingsList(SettingsList):
    """API endpoint for accessing a list of user settings objects."""

    queryset = common.models.InvenTreeUserSetting.objects.all()
    serializer_class = common.serializers.UserSettingsSerializer

    def filter_queryset(self, queryset):
        """Only list settings which apply to the current user."""
        try:
            user = self.request.user
        except AttributeError:  # pragma: no cover
            return common.models.InvenTreeUserSetting.objects.none()

        queryset = super().filter_queryset(queryset)

        queryset = queryset.filter(user=user)

        return queryset


class UserSettingsPermissions(permissions.BasePermission):
    """Special permission class to determine if the user can view / edit a particular setting."""

    def has_object_permission(self, request, view, obj):
        """Check if the user that requested is also the object owner."""
        try:
            user = request.user
        except AttributeError:  # pragma: no cover
            return False

        return user == obj.user


class UserSettingsDetail(RetrieveUpdateAPI):
    """Detail view for an individual "user setting" object.

    - User can only view / edit settings their own settings objects
    """

    lookup_field = 'key'
    queryset = common.models.InvenTreeUserSetting.objects.all()
    serializer_class = common.serializers.UserSettingsSerializer

    def get_object(self):
        """Attempt to find a user setting object with the provided key."""
        key = self.kwargs['key']

        if key not in common.models.InvenTreeUserSetting.SETTINGS.keys():
            raise NotFound()

        return common.models.InvenTreeUserSetting.get_setting_object(key, user=self.request.user)

    permission_classes = [
        UserSettingsPermissions,
    ]


class NotificationUserSettingsList(SettingsList):
    """API endpoint for accessing a list of notification user settings objects."""

    queryset = NotificationUserSetting.objects.all()
    serializer_class = NotificationUserSettingSerializer

    def filter_queryset(self, queryset):
        """Only list settings which apply to the current user."""
        try:
            user = self.request.user
        except AttributeError:
            return NotificationUserSetting.objects.none()

        queryset = super().filter_queryset(queryset)
        queryset = queryset.filter(user=user)
        return queryset


class NotificationUserSettingsDetail(RetrieveUpdateAPI):
    """Detail view for an individual "notification user setting" object.

    - User can only view / edit settings their own settings objects
    """

    queryset = NotificationUserSetting.objects.all()
    serializer_class = NotificationUserSettingSerializer

    permission_classes = [
        UserSettingsPermissions,
    ]


class NotificationList(BulkDeleteMixin, ListAPI):
    """List view for all notifications of the current user."""

    queryset = common.models.NotificationMessage.objects.all()
    serializer_class = common.serializers.NotificationMessageSerializer

    permission_classes = [
        permissions.IsAuthenticated,
    ]

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    ordering_fields = [
        'category',
        'name',
        'read',
        'creation',
    ]

    search_fields = [
        'name',
        'message',
    ]

    filterset_fields = [
        'category',
        'read',
    ]

    def filter_queryset(self, queryset):
        """Only list notifications which apply to the current user."""
        try:
            user = self.request.user
        except AttributeError:
            return common.models.NotificationMessage.objects.none()

        queryset = super().filter_queryset(queryset)
        queryset = queryset.filter(user=user)
        return queryset

    def filter_delete_queryset(self, queryset, request):
        """Ensure that the user can only delete their *own* notifications"""

        queryset = queryset.filter(user=request.user)
        return queryset


class NotificationDetail(RetrieveUpdateDestroyAPI):
    """Detail view for an individual notification object.

    - User can only view / delete their own notification objects
    """

    queryset = common.models.NotificationMessage.objects.all()
    serializer_class = common.serializers.NotificationMessageSerializer
    permission_classes = [
        UserSettingsPermissions,
    ]


class NotificationReadEdit(CreateAPI):
    """General API endpoint to manipulate read state of a notification."""

    queryset = common.models.NotificationMessage.objects.all()
    serializer_class = common.serializers.NotificationReadSerializer

    permission_classes = [
        UserSettingsPermissions,
    ]

    def get_serializer_context(self):
        """Add instance to context so it can be accessed in the serializer."""
        context = super().get_serializer_context()
        if self.request:
            context['instance'] = self.get_object()
        return context

    def perform_create(self, serializer):
        """Set the `read` status to the target value."""
        message = self.get_object()
        try:
            message.read = self.target
            message.save()
        except Exception as exc:
            raise serializers.ValidationError(detail=serializers.as_serializer_error(exc))


class NotificationRead(NotificationReadEdit):
    """API endpoint to mark a notification as read."""
    target = True


class NotificationUnread(NotificationReadEdit):
    """API endpoint to mark a notification as unread."""
    target = False


class NotificationReadAll(RetrieveAPI):
    """API endpoint to mark all notifications as read."""

    queryset = common.models.NotificationMessage.objects.all()

    permission_classes = [
        UserSettingsPermissions,
    ]

    def get(self, request, *args, **kwargs):
        """Set all messages for the current user as read."""
        try:
            self.queryset.filter(user=request.user, read=False).update(read=True)
            return Response({'status': 'ok'})
        except Exception as exc:
            raise serializers.ValidationError(detail=serializers.as_serializer_error(exc))


class WebConnectionList(ListCreateAPI):
    """List view for all webconnections."""

    queryset = common.models.WebConnection.objects.all()
    serializer_class = common.serializers.WebConnectionSerializer

    permission_classes = [
        permissions.IsAdminUser,
    ]

    def perform_create(self, serializer):
        """Validate correctness and set creator if not present."""
        connection = serializer.data.get('connection_key')
        plugin = PluginConfig.objects.get(pk=serializer.data.get('plugin')).plugin

        # Check if connections are defined
        if not hasattr(plugin, 'connections'):
            raise ValidationError({'plugin': _('The selected plugin is not a valid supplier plugin.')})

        # Check if connection exsists
        con_setting = plugin.connections.get(connection)
        if not con_setting:
            raise ValidationError({'plugin': _(f'The selected plugin does not declare the connection `{connection}`.')})

        # Check that the multiples restriction is not breached
        if not con_setting.multiple and len(self.queryset.filter(plugin=serializer.data.get('plugin'), connection_key=connection)) > 1:
            raise ValidationError(_('This connection can only be set once.'))

        # Create instance
        return_data = super().perform_create(serializer)

        # Set the creator if not present
        instance = serializer.instance
        if not instance.creator:
            user = serializer.context['request'].user
            instance.creator = user
            instance.save()

        # REturn data
        return return_data


class WebConnectionDetail(RetrieveUpdateDestroyAPI):
    """Detail view for an individual webconnection object."""

    queryset = common.models.WebConnection.objects.all()
    serializer_class = common.serializers.WebConnectionSerializer
    permission_classes = [
        permissions.IsAdminUser,
    ]


settings_api_urls = [
    # User settings
    re_path(r'^user/', include([
        # User Settings Detail
        re_path(r'^(?P<key>\w+)/', UserSettingsDetail.as_view(), name='api-user-setting-detail'),

        # User Settings List
        re_path(r'^.*$', UserSettingsList.as_view(), name='api-user-setting-list'),
    ])),

    # Notification settings
    re_path(r'^notification/', include([
        # Notification Settings Detail
        re_path(r'^(?P<pk>\d+)/', NotificationUserSettingsDetail.as_view(), name='api-notification-setting-detail'),

        # Notification Settings List
        re_path(r'^.*$', NotificationUserSettingsList.as_view(), name='api-notifcation-setting-list'),
    ])),

    # Global settings
    re_path(r'^global/', include([
        # Global Settings Detail
        re_path(r'^(?P<key>\w+)/', GlobalSettingsDetail.as_view(), name='api-global-setting-detail'),

        # Global Settings List
        re_path(r'^.*$', GlobalSettingsList.as_view(), name='api-global-setting-list'),
    ])),
]

common_api_urls = [
    # Webhooks
    path('webhook/<slug:endpoint>/', WebhookView.as_view(), name='api-webhook'),

    # Notifications
    re_path(r'^notifications/', include([
        # Individual purchase order detail URLs
        re_path(r'^(?P<pk>\d+)/', include([
            re_path(r'^read/', NotificationRead.as_view(), name='api-notifications-read'),
            re_path(r'^unread/', NotificationUnread.as_view(), name='api-notifications-unread'),
            re_path(r'.*$', NotificationDetail.as_view(), name='api-notifications-detail'),
        ])),
        # Read all
        re_path(r'^readall/', NotificationReadAll.as_view(), name='api-notifications-readall'),

        # Notification messages list
        re_path(r'^.*$', NotificationList.as_view(), name='api-notifications-list'),
    ])),

]
