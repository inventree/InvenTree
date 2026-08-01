"""API endpoints for the pricing app."""

from django.urls import include, path

from django_filters.rest_framework.filterset import FilterSet

from generic.states.api import StatusView
from InvenTree.filters import SEARCH_ORDER_FILTER, InvenTreeDateFilter
from InvenTree.mixins import ListCreateAPI, RetrieveDestroyAPI

from .models import StockItemCost
from .serializers import StockItemCostSerializer
from .status_codes import CostType


class StockItemCostFilter(FilterSet):
    """API filter options for the StockItemCost endpoints."""

    class Meta:
        """Metaclass options."""

        model = StockItemCost
        fields = ['stock_item', 'part', 'user', 'cost_type']

    min_date = InvenTreeDateFilter(
        label='Date after', field_name='date', lookup_expr='gt'
    )

    max_date = InvenTreeDateFilter(
        label='Date before', field_name='date', lookup_expr='lt'
    )


class StockItemCostMixin:
    """Mixin class for StockItemCost API endpoints."""

    queryset = StockItemCost.objects.all()
    serializer_class = StockItemCostSerializer

    def get_queryset(self):
        """Return the queryset, prefetching related fields."""
        return super().get_queryset().prefetch_related('stock_item', 'part', 'user')


class StockItemCostList(StockItemCostMixin, ListCreateAPI):
    """API endpoint for listing (and creating) StockItemCost objects.

    - GET: Return list of StockItemCost objects
    - POST: Create a new StockItemCost object
    """

    filterset_class = StockItemCostFilter
    filter_backends = SEARCH_ORDER_FILTER

    ordering_fields = ['date', 'cost_type', 'min_cost', 'max_cost', 'cost']

    ordering = '-date'

    def perform_create(self, serializer):
        """Save the user who created this cost entry."""
        user = self.request.user

        serializer.save(user=user if user and user.is_authenticated else None)


class StockItemCostDetail(StockItemCostMixin, RetrieveDestroyAPI):
    """Detail API endpoint for a single StockItemCost instance.

    StockItemCost entries are part of an append-only ledger, and cannot be edited once created.
    """


pricing_api_urls = [
    path(
        'cost/',
        include([
            path(
                'status/',
                StatusView.as_view(),
                {StatusView.MODEL_REF: CostType},
                name='api-pricing-cost-status-codes',
            ),
            path(
                '<int:pk>/',
                StockItemCostDetail.as_view(),
                name='api-pricing-cost-detail',
            ),
            path('', StockItemCostList.as_view(), name='api-pricing-cost-list'),
        ]),
    )
]
