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

from InvenTree.tasks import offload_task

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


class APIDownloadMixin:
    """
    Mixin for enabling a LIST endpoint to be downloaded a file.

    To download the data, add the ?export=<fmt> to the query string.

    The implementing class must provided a download_queryset method,
    e.g.

    def download_queryset(self, queryset, export_format):
        dataset = StockItemResource().export(queryset=queryset)

        filedata = dataset.export(export_format)

        filename = 'InvenTree_Stocktake_{date}.{fmt}'.format(
            date=datetime.now().strftime("%d-%b-%Y"),
            fmt=export_format
        )

        return DownloadFile(filedata, filename)
    """

    def get(self, request, *args, **kwargs):

        export_format = request.query_params.get('export', None)

        if export_format and export_format in ['csv', 'tsv', 'xls', 'xlsx']:
            queryset = self.filter_queryset(self.get_queryset())
            return self.download_queryset(queryset, export_format)

        else:
            # Default to the parent class implementation
            return super().get(request, *args, **kwargs)

    def download_queryset(self, queryset, export_format):
        raise NotImplementedError("download_queryset method not implemented!")


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
