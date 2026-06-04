"""Generic implementation of status api functions for InvenTree models."""

import inspect

from django.urls import include, path

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import serializers
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

import common.models
import common.serializers
import InvenTree.permissions
from data_exporter.mixins import DataExportViewMixin
from InvenTree.filters import SEARCH_ORDER_FILTER
from InvenTree.helpers import inheritors
from InvenTree.mixins import ListCreateAPI, RetrieveUpdateDestroyAPI
from InvenTree.serializers import EmptySerializer

from .serializers import GenericStateClassSerializer
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

    permission_classes = [InvenTree.permissions.IsAuthenticatedOrReadScope]
    serializer_class = GenericStateClassSerializer

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
            200: GenericStateClassSerializer,
            400: OpenApiResponse(description='Invalid request'),
        },
    )
    def get(self, request, *args, **kwargs):
        """Perform a GET request to learn information about status codes."""
        status_class = self.get_status_model()

        if isinstance(status_class, str):
            # Attempt to convert string to class
            status_classes = inheritors(StatusCode)

            for cls in status_classes:
                if cls.__name__ == status_class:
                    status_class = cls
                    break

        if not inspect.isclass(status_class):
            raise NotImplementedError(f'`{status_class}` not a class')

        if not issubclass(status_class, StatusCode):
            raise NotImplementedError(f'`{status_class}` not a valid StatusCode class')

        data = {'status_class': status_class.__name__, 'values': status_class.dict()}

        # Extend with custom values
        try:
            custom_values = status_class.custom_values()
            for item in custom_values:
                if item.name not in data['values']:
                    data['values'][item.name] = {
                        'color': item.color,
                        'logical_key': item.logical_key,
                        'key': item.key,
                        'label': item.label,
                        'name': item.name,
                        'custom': True,
                    }
        except Exception:
            pass

        serializer = GenericStateClassSerializer(data, many=False)

        return Response(serializer.data)


class AllStatusViews(StatusView):
    """Endpoint for listing all defined status models."""

    permission_classes = [InvenTree.permissions.IsAuthenticatedOrReadScope]
    serializer_class = EmptySerializer

    # Specifically disable pagination for this view
    pagination_class = None

    @extend_schema(
        operation_id='generic_status_retrieve_all',
        responses={
            200: OpenApiResponse(
                description='Mapping from class name to GenericStateClass data',
                response=OpenApiTypes.OBJECT,
            )
        },
    )
    def get(self, request, *args, **kwargs):
        """Perform a GET request to learn information about status codes."""
        data = {}

        # Find all inherited status classes
        status_classes = inheritors(StatusCode)

        # Pre-fetch all custom values from the database
        # This reduces the number of queries required
        from common.models import InvenTreeCustomUserStateModel

        custom_states_map = {}
        for state in InvenTreeCustomUserStateModel.objects.all():
            key = state.reference_status
            if key not in custom_states_map:
                custom_states_map[key] = []
            custom_states_map[key].append(state)

        for cls in status_classes:
            cls_data = {'status_class': cls.__name__, 'values': cls.dict(custom=False)}

            # Extend with custom values (from pre-cached queryset)
            custom_states = custom_states_map.get(cls.__name__, [])

            for item in custom_states:
                label = str(item.name)
                if label not in cls_data['values']:
                    cls_data['values'][label] = {
                        'color': item.color,
                        'logical_key': item.logical_key,
                        'key': item.key,
                        'label': item.label,
                        'name': item.name,
                        'custom': True,
                    }

            data[cls.__name__] = GenericStateClassSerializer(cls_data, many=False).data

        return Response(data)


# Custom states
class CustomStateList(DataExportViewMixin, ListCreateAPI):
    """List view for all custom states."""

    queryset = common.models.InvenTreeCustomUserStateModel.objects.all()
    serializer_class = common.serializers.CustomStateSerializer
    permission_classes = [InvenTree.permissions.IsStaffOrReadOnlyScope]
    filter_backends = SEARCH_ORDER_FILTER
    ordering_fields = ['key']
    search_fields = ['key', 'name', 'label', 'reference_status']
    filterset_fields = ['model', 'reference_status']


class CustomStateDetail(RetrieveUpdateDestroyAPI):
    """Detail view for a particular custom states."""

    queryset = common.models.InvenTreeCustomUserStateModel.objects.all()
    serializer_class = common.serializers.CustomStateSerializer
    permission_classes = [InvenTree.permissions.IsStaffOrReadOnlyScope]


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
