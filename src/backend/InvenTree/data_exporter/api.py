"""API endpoints for the exporter app."""

from django.urls import include, path

from rest_framework import permissions

import data_exporter.models
import data_exporter.serializers
from InvenTree.api import BulkDeleteMixin
from InvenTree.filters import SEARCH_ORDER_FILTER
from InvenTree.mixins import ListAPI


class DataExportList(BulkDeleteMixin, ListAPI):
    """API endpoint for viewing a list of ExportOutput objects."""

    queryset = data_exporter.models.ExportOutput.objects.all()
    serializer_class = data_exporter.serializers.DataExportOutputSerializer

    permission_classes = [permissions.IsAuthenticated]

    filter_backends = SEARCH_ORDER_FILTER

    ordering_fields = ['created', 'user', 'plugin', 'progress', 'complete']


exporter_api_urls = [
    path(
        'session/',
        include([path('', DataExportList.as_view(), name='api-export-session-list')]),
    )
]
