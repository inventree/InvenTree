"""
Main JSON interface views
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.http import JsonResponse

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

from rest_framework import permissions

from .views import AjaxView
from .version import inventreeVersion, inventreeApiVersion, inventreeInstanceName
from .status import is_worker_running


class InfoView(AjaxView):
    """ Simple JSON endpoint for InvenTree information.
    Use to confirm that the server is running, etc.
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):

        data = {
            'server': 'InvenTree',
            'version': inventreeVersion(),
            'instance': inventreeInstanceName(),
            'apiVersion': inventreeApiVersion(),
            'worker_running': is_worker_running(),
            'plugins_enabled': settings.PLUGINS_ENABLED,
        }

        return JsonResponse(data)


class NotFoundView(AjaxView):
    """
    Simple JSON view when accessing an invalid API view.
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):

        data = {
            'details': _('API endpoint not found'),
            'url': request.build_absolute_uri(),
        }

        return JsonResponse(data, status=404)


class AttachmentMixin:
    """
    Mixin for creating attachment objects,
    and ensuring the user information is saved correctly.
    """

    permission_classes = [permissions.IsAuthenticated]

    filter_backends = [
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    ]

    def perform_create(self, serializer):
        """ Save the user information when a file is uploaded """

        attachment = serializer.save()
        attachment.user = self.request.user
        attachment.save()
