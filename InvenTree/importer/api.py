"""API endpoints for the importer app."""

from django.urls import include, path

import importer.models
import importer.serializers
from InvenTree.filters import SEARCH_ORDER_FILTER
from InvenTree.mixins import ListAPI, ListCreateAPI, RetrieveUpdateDestroyAPI


class DataImportSessionList(ListCreateAPI):
    """API endpoint for accessing a list of DataImportSession objects."""

    queryset = importer.models.DataImportSession.objects.all()
    serializer_class = importer.serializers.DataImportSessionSerializer


class DataImportSessionDetail(RetrieveUpdateDestroyAPI):
    """Detail endpoint for a single DataImportSession object."""

    queryset = importer.models.DataImportSession.objects.all()
    serializer_class = importer.serializers.DataImportSessionSerializer


class DataImportColumnMappingList(ListCreateAPI):
    """API endpoint for accessing a list of DataImportColumnMap objects."""

    queryset = importer.models.DataImportColumnMap.objects.all()
    serializer_class = importer.serializers.DataImportColumnMapSerializer

    filter_backends = SEARCH_ORDER_FILTER

    filterset_fields = ['session']


class DataImportColumnMappingDetail(RetrieveUpdateDestroyAPI):
    """Detail endpoint for a single DataImportColumnMap object."""

    queryset = importer.models.DataImportColumnMap.objects.all()
    serializer_class = importer.serializers.DataImportColumnMapSerializer


class DataImportRowList(ListAPI):
    """API endpoint for accessing a list of DataImportRow objects."""

    queryset = importer.models.DataImportRow.objects.all()
    serializer_class = importer.serializers.DataImportRowSerializer

    filter_backends = SEARCH_ORDER_FILTER

    filterset_fields = ['session']

    ordering_fields = ['pk', 'row_index']

    ordering = 'row_index'


class DataImportRowDetail(RetrieveUpdateDestroyAPI):
    """Detail endpoint for a single DataImportRow object."""

    queryset = importer.models.DataImportRow.objects.all()
    serializer_class = importer.serializers.DataImportRowSerializer


importer_api_urls = [
    path(
        'session/',
        include([
            path(
                '<int:pk>/',
                DataImportSessionDetail.as_view(),
                name='api-import-session-detail',
            ),
            path('', DataImportSessionList.as_view(), name='api-importer-session-list'),
        ]),
    ),
    path(
        'column-mapping/',
        include([
            path(
                '<int:pk>/',
                DataImportColumnMappingDetail.as_view(),
                name='api-importer-mapping-detail',
            ),
            path(
                '',
                DataImportColumnMappingList.as_view(),
                name='api-importer-mapping-list',
            ),
        ]),
    ),
    path(
        'row/',
        include([
            path(
                '<int:pk>/',
                DataImportRowDetail.as_view(),
                name='api-importer-row-detail',
            ),
            path('', DataImportRowList.as_view(), name='api-importer-row-list'),
        ]),
    ),
]
