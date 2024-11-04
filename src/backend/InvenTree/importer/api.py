"""API endpoints for the importer app."""

from django.shortcuts import get_object_or_404
from django.urls import include, path

from drf_spectacular.utils import extend_schema
from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

import importer.models
import importer.registry
import importer.serializers
from InvenTree.api import BulkDeleteMixin
from InvenTree.filters import SEARCH_ORDER_FILTER
from InvenTree.mixins import (
    CreateAPI,
    ListAPI,
    ListCreateAPI,
    RetrieveUpdateAPI,
    RetrieveUpdateDestroyAPI,
)
from users.models import check_user_permission


class DataImporterPermission(permissions.BasePermission):
    """Mixin class for determining if the user has correct permissions."""

    def has_permission(self, request, view):
        """Class level permission checks are handled via permissions.IsAuthenticated."""
        return True

    def has_object_permission(self, request, view, obj):
        """Check if the user has permission to access the imported object."""
        # For safe methods (GET, HEAD, OPTIONS), allow access
        if request.method in permissions.SAFE_METHODS:
            return True

        if isinstance(obj, importer.models.DataImportSession):
            session = obj
        else:
            session = getattr(obj, 'session', None)

        if session:
            if model_class := session.model_class:
                return check_user_permission(request.user, model_class, 'change')

        return True


class DataImporterPermissionMixin:
    """Mixin class for checking permissions on DataImporter objects."""

    # Default permissions: User must be authenticated
    permission_classes = [permissions.IsAuthenticated, DataImporterPermission]


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


class DataImportSessionList(DataImporterPermission, BulkDeleteMixin, ListCreateAPI):
    """API endpoint for accessing a list of DataImportSession objects."""

    queryset = importer.models.DataImportSession.objects.all()
    serializer_class = importer.serializers.DataImportSessionSerializer

    filter_backends = SEARCH_ORDER_FILTER

    filterset_fields = ['model_type', 'status', 'user']

    ordering_fields = ['timestamp', 'status', 'model_type']


class DataImportSessionDetail(DataImporterPermission, RetrieveUpdateDestroyAPI):
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

        # Check that the user has permission to accept the field mapping
        if model_class := session.model_class:
            if not check_user_permission(request.user, model_class, 'change'):
                raise PermissionDenied()

        # Attempt to accept the mapping (may raise an exception if the mapping is invalid)
        session.accept_mapping()

        return Response(importer.serializers.DataImportSessionSerializer(session).data)


class DataImportSessionAcceptRows(DataImporterPermission, CreateAPI):
    """API endpoint to accept the rows for a DataImportSession."""

    queryset = importer.models.DataImportSession.objects.all()
    serializer_class = importer.serializers.DataImportAcceptRowSerializer

    def get_serializer_context(self):
        """Add the import session object to the serializer context."""
        ctx = super().get_serializer_context()

        try:
            ctx['session'] = importer.models.DataImportSession.objects.get(
                pk=self.kwargs.get('pk', None)
            )
        except Exception:
            pass

        ctx['request'] = self.request
        return ctx


class DataImportColumnMappingList(DataImporterPermissionMixin, ListAPI):
    """API endpoint for accessing a list of DataImportColumnMap objects."""

    queryset = importer.models.DataImportColumnMap.objects.all()
    serializer_class = importer.serializers.DataImportColumnMapSerializer

    filter_backends = SEARCH_ORDER_FILTER

    filterset_fields = ['session']


class DataImportColumnMappingDetail(DataImporterPermissionMixin, RetrieveUpdateAPI):
    """Detail endpoint for a single DataImportColumnMap object."""

    queryset = importer.models.DataImportColumnMap.objects.all()
    serializer_class = importer.serializers.DataImportColumnMapSerializer


class DataImportRowList(DataImporterPermission, BulkDeleteMixin, ListAPI):
    """API endpoint for accessing a list of DataImportRow objects."""

    queryset = importer.models.DataImportRow.objects.all()
    serializer_class = importer.serializers.DataImportRowSerializer

    filter_backends = SEARCH_ORDER_FILTER

    filterset_fields = ['session', 'valid', 'complete']

    ordering_fields = ['pk', 'row_index', 'valid']

    ordering = 'row_index'


class DataImportRowDetail(DataImporterPermission, RetrieveUpdateDestroyAPI):
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
                        'accept_rows/',
                        DataImportSessionAcceptRows.as_view(),
                        name='api-import-session-accept-rows',
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
