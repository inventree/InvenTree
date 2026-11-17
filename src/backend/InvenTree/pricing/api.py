"""Provides a JSON API for the 'pricing' app."""

from django.shortcuts import get_object_or_404
from django.urls import include, path

from django_filters.rest_framework.filterset import FilterSet
from rest_framework import permissions
from rest_framework.settings import api_settings

from data_exporter.mixins import DataExportViewMixin
from generic.states.api import StatusView
from InvenTree.filters import SEARCH_ORDER_FILTER, InvenTreeDateFilter
from InvenTree.mixins import (
    ListAPI,
    ListCreateAPI,
    OutputOptionsMixin,
    RetrieveAPI,
    RetrieveUpdateAPI,
    RetrieveUpdateDestroyAPI,
)
from InvenTree.permissions import ACTION_MAP
from part.models import Part
from users.oauth2_scopes import DEFAULT_READ, get_granular_scope
from users.permissions import check_user_role
from users.ruleset import RuleSetEnum

from . import serializers as pricing_serializers
from .models import (
    CostSource,
    PartInternalPriceBreak,
    PartPricing,
    PartSellPriceBreak,
    StockItemCost,
    StockItemCostEntry,
)
from .status_codes import CostType


class PartSalePriceDetail(RetrieveUpdateDestroyAPI):
    """Detail endpoint for PartSellPriceBreak model."""

    queryset = PartSellPriceBreak.objects.all()
    serializer_class = pricing_serializers.PartSalePriceSerializer


class PartSalePriceList(DataExportViewMixin, ListCreateAPI):
    """API endpoint for list view of PartSalePriceBreak model."""

    queryset = PartSellPriceBreak.objects.all()
    serializer_class = pricing_serializers.PartSalePriceSerializer

    filter_backends = SEARCH_ORDER_FILTER
    filterset_fields = ['part']
    ordering_fields = ['quantity', 'price']
    ordering = 'quantity'


class PartInternalPriceDetail(RetrieveUpdateDestroyAPI):
    """Detail endpoint for PartInternalPriceBreak model."""

    queryset = PartInternalPriceBreak.objects.all()
    serializer_class = pricing_serializers.PartInternalPriceSerializer


class PartInternalPriceList(DataExportViewMixin, ListCreateAPI):
    """API endpoint for list view of PartInternalPriceBreak model."""

    queryset = PartInternalPriceBreak.objects.all()
    serializer_class = pricing_serializers.PartInternalPriceSerializer

    filter_backends = SEARCH_ORDER_FILTER
    filterset_fields = ['part']
    ordering_fields = ['quantity', 'price']
    ordering = 'quantity'


class PartPricingDetail(RetrieveUpdateAPI):
    """API endpoint for viewing part pricing data.

    Note: The URL 'pk' refers to the linked Part instance (not the PartPricing instance).
    """

    serializer_class = pricing_serializers.PartPricingSerializer

    # The queryset model determines the required (model) permissions for this endpoint,
    # so it must be PartPricing (rather than Part)
    queryset = PartPricing.objects.all()

    def get_object(self):
        """Return the PartPricing object associated with the linked Part.

        If no PartPricing instance exists for the Part, a new (unsaved) instance is returned.
        """
        part = get_object_or_404(Part, pk=self.kwargs.get('pk'))
        pricing = part.pricing

        self.check_object_permissions(self.request, pricing)

        return pricing


def stock_action_for_method(method: str):
    """Return the 'stock' role permission required to access stock item cost data.

    Reading cost data requires 'stock.view'. Any change to the cost data of a stock item
    (adding, editing or removing a cost entry) modifies an existing stock item,
    so requires 'stock.change' - rather than 'stock.add' or 'stock.delete'.

    Returns:
        The required permission, or None if the method is not supported
    """
    action = {**ACTION_MAP, 'HEAD': 'view', 'OPTIONS': 'view'}.get(method)

    if action is None:
        return None

    return 'view' if action == 'view' else 'change'


class StockRolePermission(permissions.BasePermission):
    """Require the matching 'stock' role permission for the request.

    This is applied in addition to the default permission checks, which require
    the matching 'pricing' role permission for the pricing models.
    Stock item cost data exposes information about individual stock items,
    so access requires both roles (see stock_action_for_method).
    """

    def has_permission(self, request, view):
        """Check that the user has the required 'stock' role permission."""
        user = request.user

        if not user or not user.is_authenticated:
            return False

        permission = stock_action_for_method(request.method)

        if permission is None:
            return False

        return check_user_role(user, RuleSetEnum.STOCK, permission)


def stock_item_cost_scopes() -> dict:
    """Return the OAuth2 scopes required for the stock item cost endpoints.

    Each request requires the matching 'pricing' scope, *and* the 'stock' scope
    which matches the required 'stock' role permission (see stock_action_for_method).
    """
    scopes = {}

    for method, action in ACTION_MAP.items():
        if method == 'OPTIONS':
            scopes[method] = [[DEFAULT_READ]]
        else:
            scopes[method] = [
                [
                    get_granular_scope(action, RuleSetEnum.PRICING),
                    get_granular_scope(
                        stock_action_for_method(method), RuleSetEnum.STOCK
                    ),
                ]
            ]

    return scopes


class StockItemCostPermissionMixin:
    """Mixin class requiring both the 'pricing' and 'stock' roles."""

    permission_classes = [*api_settings.DEFAULT_PERMISSION_CLASSES, StockRolePermission]

    # OAuth2 tokens require the matching scope for both roles
    required_alternate_scopes = stock_item_cost_scopes()


class StockItemCostEntryFilter(FilterSet):
    """API filter options for the StockItemCostEntry endpoints."""

    class Meta:
        """Metaclass options."""

        model = StockItemCostEntry
        fields = ['stock_item', 'cost_type', 'source', 'user']

    min_date = InvenTreeDateFilter(
        label='Updated after', field_name='date', lookup_expr='gt'
    )

    max_date = InvenTreeDateFilter(
        label='Updated before', field_name='date', lookup_expr='lt'
    )


class StockItemCostEntryMixin(StockItemCostPermissionMixin):
    """Mixin class for the StockItemCostEntry API endpoints."""

    queryset = StockItemCostEntry.objects.all()
    serializer_class = pricing_serializers.StockItemCostEntrySerializer

    def user_or_none(self):
        """Return the requesting user, or None if not authenticated."""
        user = self.request.user
        return user if user and user.is_authenticated else None


class StockItemCostEntryList(
    StockItemCostEntryMixin, OutputOptionsMixin, ListCreateAPI
):
    """API endpoint for listing (and creating) StockItemCostEntry objects.

    A stock item may have any number of cost entries - posting always creates a new entry.
    """

    filterset_class = StockItemCostEntryFilter
    filter_backends = SEARCH_ORDER_FILTER

    search_fields = ['source', 'notes']

    ordering_fields = [
        'date',
        'cost_type',
        'source',
        'converted_min_cost',
        'converted_max_cost',
    ]

    ordering = '-date'

    def perform_create(self, serializer):
        """Record the creating user, and mark the entry as manually entered (unless a source is provided)."""
        source = serializer.validated_data.get('source') or CostSource.MANUAL

        serializer.save(user=self.user_or_none(), source=source)


class StockItemCostEntryDetail(
    StockItemCostEntryMixin, OutputOptionsMixin, RetrieveUpdateDestroyAPI
):
    """Detail API endpoint for a single StockItemCostEntry object."""

    def perform_update(self, serializer):
        """Record the user who last updated this cost entry."""
        serializer.save(user=self.user_or_none())


class StockItemCostFilter(FilterSet):
    """API filter options for the StockItemCost summary endpoints."""

    class Meta:
        """Metaclass options."""

        model = StockItemCost
        fields = ['stock_item', 'incomplete']


class StockItemCostMixin(StockItemCostPermissionMixin):
    """Mixin class for the (read-only) StockItemCost API endpoints."""

    queryset = StockItemCost.objects.all()
    serializer_class = pricing_serializers.StockItemCostSerializer


class StockItemCostList(StockItemCostMixin, ListAPI):
    """API endpoint for listing StockItemCost summaries (read-only)."""

    filterset_class = StockItemCostFilter
    filter_backends = SEARCH_ORDER_FILTER

    ordering_fields = ['date', 'min_cost', 'max_cost']

    ordering = '-date'


class StockItemCostDetail(StockItemCostMixin, RetrieveAPI):
    """Detail API endpoint for a single StockItemCost summary (read-only)."""


# Note: Part pricing URL names are retained from when these endpoints were part of the 'part' app
pricing_api_urls = [
    # Part sale pricing
    path(
        'sale-price/',
        include([
            path(
                '<int:pk>/',
                PartSalePriceDetail.as_view(),
                name='api-part-sale-price-detail',
            ),
            path('', PartSalePriceList.as_view(), name='api-part-sale-price-list'),
        ]),
    ),
    # Part internal pricing
    path(
        'internal-price/',
        include([
            path(
                '<int:pk>/',
                PartInternalPriceDetail.as_view(),
                name='api-part-internal-price-detail',
            ),
            path(
                '', PartInternalPriceList.as_view(), name='api-part-internal-price-list'
            ),
        ]),
    ),
    # Cached pricing data for a particular part
    path('part/<int:pk>/', PartPricingDetail.as_view(), name='api-part-pricing'),
    # Stock item cost entries
    path(
        'stock-cost-entry/',
        include([
            path(
                'status/',
                StatusView.as_view(),
                {StatusView.MODEL_REF: CostType},
                name='api-stock-cost-entry-status-codes',
            ),
            path(
                '<int:pk>/',
                StockItemCostEntryDetail.as_view(),
                name='api-stock-cost-entry-detail',
            ),
            path(
                '', StockItemCostEntryList.as_view(), name='api-stock-cost-entry-list'
            ),
        ]),
    ),
    # Stock item cost summaries
    path(
        'stock-cost/',
        include([
            path(
                '<int:pk>/', StockItemCostDetail.as_view(), name='api-stock-cost-detail'
            ),
            path('', StockItemCostList.as_view(), name='api-stock-cost-list'),
        ]),
    ),
]
