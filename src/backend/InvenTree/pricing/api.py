"""Provides a JSON API for the 'pricing' app."""

from django.shortcuts import get_object_or_404
from django.urls import include, path

from data_exporter.mixins import DataExportViewMixin
from InvenTree.filters import SEARCH_ORDER_FILTER
from InvenTree.mixins import ListCreateAPI, RetrieveUpdateAPI, RetrieveUpdateDestroyAPI
from part.models import Part

from . import serializers as pricing_serializers
from .models import PartInternalPriceBreak, PartPricing, PartSellPriceBreak


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


# Note: URL names are retained from when these endpoints were part of the 'part' app
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
]
