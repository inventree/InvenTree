"""Generic implementation of status api functions for InvenTree models."""

import inspect

from django.urls import include, path

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import permissions, serializers
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

import common.models
import common.serializers
from generic.states.custom import get_status_api_response
from importer.mixins import DataExportViewMixin
from InvenTree.filters import SEARCH_ORDER_FILTER
from InvenTree.mixins import ListCreateAPI, RetrieveUpdateDestroyAPI
from InvenTree.permissions import IsStaffOrReadOnly
from InvenTree.serializers import EmptySerializer
from machine.machine_type import MachineStatus

from .states import StatusCode


class StatusViewSerializer(serializers.Serializer):
    """Serializer for the StatusView responses."""

    class_name = serializers.CharField()
    values = serializers.DictField()


class StatusView(GenericAPIView):
    """Generic API endpoint for discovering information on 'status codes' for a particular model.

    This class should be implemented as a subclass for each type of status.
    For example, the API endpoint /stock/status/ will have information about
    all available 'StockStatus' codes
    """

    permission_classes = [permissions.IsAuthenticated]

    # Override status_class for implementing subclass
    MODEL_REF = 'statusmodel'

    def get_status_model(self, *args, **kwargs):
        """Return the StatusCode model based on extra parameters passed to the view."""
        status_model = self.kwargs.get(self.MODEL_REF, None)

        if status_model is None:
            raise serializers.ValidationError(
                f"StatusView view called without '{self.MODEL_REF}' parameter"
            )

        return status_model

    @extend_schema(
        description='Retrieve information about a specific status code',
        responses={
            200: OpenApiResponse(description='Status code information'),
            400: OpenApiResponse(description='Invalid request'),
        },
    )
    def get(self, request, *args, **kwargs):
        """Perform a GET request to learn information about status codes."""
        status_class = self.get_status_model()

        if not inspect.isclass(status_class):
            raise NotImplementedError('`status_class` not a class')

        if not issubclass(status_class, StatusCode):
            raise NotImplementedError('`status_class` not a valid StatusCode class')

        data = {'class': status_class.__name__, 'values': status_class.dict()}

        return Response(data)


class AllStatusViews(StatusView):
    """Endpoint for listing all defined status models."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = EmptySerializer

    def get(self, request, *args, **kwargs):
        """Perform a GET request to learn information about status codes."""
        data = get_status_api_response()
        # Extend with MachineStatus classes
        data.update(get_status_api_response(MachineStatus, prefix=['MachineStatus']))
        return Response(data)


# Custom states
class CustomStateList(DataExportViewMixin, ListCreateAPI):
    """List view for all custom states."""

    queryset = common.models.InvenTreeCustomUserStateModel.objects.all()
    serializer_class = common.serializers.CustomStateSerializer
    permission_classes = [permissions.IsAuthenticated, IsStaffOrReadOnly]
    filter_backends = SEARCH_ORDER_FILTER
    ordering_fields = ['key']
    search_fields = ['key', 'name', 'label', 'reference_status']


class CustomStateDetail(RetrieveUpdateDestroyAPI):
    """Detail view for a particular custom states."""

    queryset = common.models.InvenTreeCustomUserStateModel.objects.all()
    serializer_class = common.serializers.CustomStateSerializer
    permission_classes = [permissions.IsAuthenticated, IsStaffOrReadOnly]


urlpattern = [
    # Custom state
    path(
        'custom/',
        include([
            path(
                '<int:pk>/', CustomStateDetail.as_view(), name='api-custom-state-detail'
            ),
            path('', CustomStateList.as_view(), name='api-custom-state-list'),
        ]),
    ),
    # Generic status views
    path(
        '',
        include([
            path(
                f'<str:{StatusView.MODEL_REF}>/',
                include([path('', StatusView.as_view(), name='api-status')]),
            ),
            path('', AllStatusViews.as_view(), name='api-status-all'),
        ]),
    ),
]
