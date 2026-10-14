"""API endpoints for the pricing app."""

from django.urls import include, path

from django_filters.rest_framework.filterset import FilterSet

from generic.states.api import StatusView
from InvenTree.filters import SEARCH_ORDER_FILTER, InvenTreeDateFilter
from InvenTree.mixins import (
    ListAPI,
    ListCreateAPI,
    RetrieveAPI,
    RetrieveUpdateDestroyAPI,
)

from .models import StockItemCost, StockItemCostEntry
from .serializers import StockItemCostEntrySerializer, StockItemCostSerializer
from .status_codes import CostType


class StockItemCostEntryFilter(FilterSet):
    """API filter options for the StockItemCostEntry endpoints."""

    class Meta:
        """Metaclass options."""

        model = StockItemCostEntry
        fields = ['stock_item', 'user', 'cost_type']

    min_date = InvenTreeDateFilter(
        label='Date after', field_name='date', lookup_expr='gt'
    )

    max_date = InvenTreeDateFilter(
        label='Date before', field_name='date', lookup_expr='lt'
    )


class StockItemCostEntryMixin:
    """Mixin class for StockItemCostEntry API endpoints."""

    queryset = StockItemCostEntry.objects.all()
    serializer_class = StockItemCostEntrySerializer

    def get_queryset(self):
        """Return the queryset, prefetching related fields."""
        return super().get_queryset().prefetch_related('stock_item', 'user')


class StockItemCostEntryList(StockItemCostEntryMixin, ListCreateAPI):
    """API endpoint for listing (and creating) StockItemCostEntry objects.

    - GET: Return list of StockItemCostEntry objects
    - POST: Create a new StockItemCostEntry object

    A stock item may have any number of cost entries, including several of the
    same cost type - posting again always creates a new entry. To replace an
    existing cost, update or delete that entry directly.
    """

    filterset_class = StockItemCostEntryFilter
    filter_backends = SEARCH_ORDER_FILTER

    ordering_fields = ['date', 'cost_type', 'min_cost', 'max_cost']

    ordering = '-date'

    def perform_create(self, serializer):
        """Record the user who created this cost entry."""
        user = self.request.user

        serializer.save(user=user if user and user.is_authenticated else None)


class StockItemCostEntryDetail(StockItemCostEntryMixin, RetrieveUpdateDestroyAPI):
    """Detail API endpoint for a single StockItemCostEntry instance."""

    def perform_update(self, serializer):
        """Record the user who last updated this cost entry."""
        user = self.request.user

        serializer.save(user=user if user and user.is_authenticated else None)


class StockItemCostFilter(FilterSet):
    """API filter options for the (read-only) StockItemCost summary endpoint."""

    class Meta:
        """Metaclass options."""

        model = StockItemCost
        fields = ['stock_item']


class StockItemCostList(ListAPI):
    """API endpoint for listing StockItemCost summaries.

    This is a read-only, calculated value - see pricing.models.StockItemCost.
    """

    queryset = StockItemCost.objects.all()
    serializer_class = StockItemCostSerializer
    filterset_class = StockItemCostFilter
    filter_backends = SEARCH_ORDER_FILTER


class StockItemCostDetail(RetrieveAPI):
    """Detail API endpoint for a single (read-only) StockItemCost summary."""

    queryset = StockItemCost.objects.all()
    serializer_class = StockItemCostSerializer


pricing_api_urls = [
    path(
        'cost-entry/',
        include([
            path(
                'status/',
                StatusView.as_view(),
                {StatusView.MODEL_REF: CostType},
                name='api-pricing-cost-entry-status-codes',
            ),
            path(
                '<int:pk>/',
                StockItemCostEntryDetail.as_view(),
                name='api-pricing-cost-entry-detail',
            ),
            path(
                '', StockItemCostEntryList.as_view(), name='api-pricing-cost-entry-list'
            ),
        ]),
    ),
    path(
        'cost/',
        include([
            path(
                '<int:pk>/',
                StockItemCostDetail.as_view(),
                name='api-pricing-cost-detail',
            ),
            path('', StockItemCostList.as_view(), name='api-pricing-cost-list'),
        ]),
    ),
]
