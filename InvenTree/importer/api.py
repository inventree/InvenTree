"""API endpoints for the importer app."""

from django.urls import include, path

import importer.models
import importer.serializers
from InvenTree.filters import SEARCH_ORDER_FILTER
from InvenTree.mixins import ListAPI, ListCreateAPI


class DataImportSessionList(ListCreateAPI):
    """API endpoint for accessing a list of DataImportSession objects."""

    queryset = importer.models.DataImportSession.objects.all()
    serializer_class = importer.serializers.DataImportSessionSerializer


class DataImportColumnMappingList(ListCreateAPI):
    """API endpoint for accessing a list of DataImportColumnMap objects."""

    queryset = importer.models.DataImportColumnMap.objects.all()
    serializer_class = importer.serializers.DataImportColumnMapSerializer

    filter_backends = SEARCH_ORDER_FILTER

    filterset_fields = ['session']


class DataImportRowList(ListAPI):
    """API endpoint for accessing a list of DataImportRow objects."""

    queryset = importer.models.DataImportRow.objects.all()
    serializer_class = importer.serializers.DataImportRowSerializer

    filter_backends = SEARCH_ORDER_FILTER

    filterset_fields = ['session']

    ordering_fields = ['pk', 'row_index']

    ordering = 'row_index'


importer_api_urls = [
    path(
        'session/',
        include([
            path('', DataImportSessionList.as_view(), name='api-importer-session-list')
        ]),
    ),
    path(
        'column-mapping/',
        include([
            path(
                '',
                DataImportColumnMappingList.as_view(),
                name='api-importer-mapping-list',
            )
        ]),
    ),
    path(
        'row/',
        include([path('', DataImportRowList.as_view(), name='api-importer-row-list')]),
    ),
]
