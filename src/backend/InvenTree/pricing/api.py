"""API endpoints for the pricing app."""

from django.urls import include, path

from django_filters.rest_framework.filterset import FilterSet
from rest_framework import status
from rest_framework.response import Response

from generic.states.api import StatusView
from InvenTree.filters import SEARCH_ORDER_FILTER, InvenTreeDateFilter
from InvenTree.mixins import ListCreateAPI, RetrieveUpdateDestroyAPI

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
    - POST: Create (or update) a StockItemCost object

    Only one entry is kept per (stock_item, cost_type) pair - posting again for a
    pair that already has an entry updates that entry in place, rather than
    creating a duplicate.
    """

    filterset_class = StockItemCostFilter
    filter_backends = SEARCH_ORDER_FILTER

    ordering_fields = ['date', 'cost_type', 'min_cost', 'max_cost', 'cost']

    ordering = '-date'

    def create(self, request, *args, **kwargs):
        """Create a new StockItemCost entry, or update a matching existing one.

        The existing (stock_item, cost_type) entry (if any) must be located before
        validation, so that the serializer's model-level uniqueness check validates
        against the correct instance rather than rejecting the request outright.
        """
        data = self.clean_data(request.data)

        instance = StockItemCost.objects.filter(
            stock_item=data.get('stock_item'),
            cost_type=data.get('cost_type', CostType.PURCHASE.value),
        ).first()

        serializer = self.get_serializer(instance, data=data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        serializer.save(user=user if user and user.is_authenticated else None)

        headers = self.get_success_headers(serializer.data)
        response_status = status.HTTP_200_OK if instance else status.HTTP_201_CREATED
        return Response(serializer.data, status=response_status, headers=headers)


class StockItemCostDetail(StockItemCostMixin, RetrieveUpdateDestroyAPI):
    """Detail API endpoint for a single StockItemCost instance."""

    def perform_update(self, serializer):
        """Record the user who last updated this cost entry."""
        user = self.request.user

        serializer.save(user=user if user and user.is_authenticated else None)


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
