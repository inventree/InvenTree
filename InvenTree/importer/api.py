"""API endpoints for the importer app."""

from django.shortcuts import get_object_or_404
from django.urls import include, path

from drf_spectacular.utils import extend_schema
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

import importer.models
import importer.registry
import importer.serializers
from InvenTree.filters import SEARCH_ORDER_FILTER
from InvenTree.mixins import ListAPI, ListCreateAPI, RetrieveUpdateDestroyAPI


class DataImporterModelList(APIView):
    """API endpoint for displaying a list of models available for import."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Return a list of models available for import."""
        models = []

        for serializer in importer.registry.get_supported_serializers():
            model = serializer.Meta.model
            url = model.get_api_url() if hasattr(model, 'get_api_url') else None

            models.append({
                'serializer': str(serializer.__name__),
                'model_type': model.__name__.lower(),
                'api_url': url,
            })

        return Response(models)


class DataImportSessionList(ListCreateAPI):
    """API endpoint for accessing a list of DataImportSession objects."""

    queryset = importer.models.DataImportSession.objects.all()
    serializer_class = importer.serializers.DataImportSessionSerializer


class DataImportSessionDetail(RetrieveUpdateDestroyAPI):
    """Detail endpoint for a single DataImportSession object."""

    queryset = importer.models.DataImportSession.objects.all()
    serializer_class = importer.serializers.DataImportSessionSerializer


class DataImportSessionAcceptFields(APIView):
    """API endpoint to accept the field mapping for a DataImportSession."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        responses={200: importer.serializers.DataImportSessionSerializer(many=False)}
    )
    def post(self, request, pk):
        """Accept the field mapping for a DataImportSession."""
        session = get_object_or_404(importer.models.DataImportSession, pk=pk)

        # Attempt to accept the mapping (may raise an exception if the mapping is invalid)
        session.accept_mapping()

        return Response(importer.serializers.DataImportSessionSerializer(session).data)


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
    path('models/', DataImporterModelList.as_view(), name='api-importer-model-list'),
    path(
        'session/',
        include([
            path(
                '<int:pk>/',
                include([
                    path(
                        'accept_fields/',
                        DataImportSessionAcceptFields.as_view(),
                        name='api-import-session-accept-fields',
                    ),
                    path(
                        '',
                        DataImportSessionDetail.as_view(),
                        name='api-import-session-detail',
                    ),
                ]),
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
