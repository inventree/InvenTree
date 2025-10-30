"""DRF API definition for the 'web' app."""

from django.urls import include, path

import structlog

import InvenTree.permissions
from InvenTree.fields import InvenTreeOutputOption, OutputConfiguration
from InvenTree.filters import SEARCH_ORDER_FILTER
from InvenTree.mixins import (
    ListAPI,
    OutputOptionsMixin,
    RetrieveAPI,
    SerializerContextMixin,
)
from web.models import GuideDefinition
from web.serializers import GuideDefinitionSerializer

logger = structlog.get_logger('inventree')


class GuideDefinitionMixin(SerializerContextMixin):
    """Mixin for GuideDefinition detail views."""

    queryset = GuideDefinition.objects.all()
    serializer_class = GuideDefinitionSerializer
    permission_classes = [InvenTree.permissions.IsStaffOrReadOnlyScope]

    def get_queryset(self):
        """Return queryset for this endpoint."""
        return super().get_queryset().prefetch_related('executions')


class GuideDefinitionDetailOptions(OutputConfiguration):
    """Holds all available output options for Group views."""

    OPTIONS = [
        InvenTreeOutputOption(
            'description',
            description='Include description field (optional, may be large)',
        ),
        InvenTreeOutputOption(
            'guide_data',
            description='Include data field (optional, may be large JSON object and is only meant for machines)',
        ),
    ]


class GuideDefinitionDetail(GuideDefinitionMixin, OutputOptionsMixin, RetrieveAPI):
    """Detail for a particular guide definition."""

    output_options = GuideDefinitionDetailOptions


class GuideDefinitionList(GuideDefinitionMixin, OutputOptionsMixin, ListAPI):
    """List of guide definitions."""

    output_options = GuideDefinitionDetailOptions
    filter_backends = SEARCH_ORDER_FILTER
    search_fields = ['name', 'slug', 'description']
    ordering_fields = ['guide_type', 'slug', 'name']


web_urls = [
    path(
        'guides/',
        include([
            path('<int:pk>/', GuideDefinitionDetail.as_view(), name='api-guide-detail'),
            path('', GuideDefinitionList.as_view(), name='api-guide-list'),
        ]),
    )
]
