"""API endpoints for tax models."""

from django.urls import include, path

from InvenTree.filters import SEARCH_ORDER_FILTER
from InvenTree.mixins import ListCreateAPI, RetrieveUpdateDestroyAPI

from .models import TaxConfiguration
from .serializers import TaxConfigurationSerializer


class TaxConfigurationList(ListCreateAPI):
    """API endpoint for accessing a list of TaxConfiguration objects."""

    serializer_class = TaxConfigurationSerializer
    queryset = TaxConfiguration.objects.all()

    filter_backends = SEARCH_ORDER_FILTER

    filterset_fields = [
        'year',
        'is_active',
        'is_inclusive',
        'applies_to_sales',
        'applies_to_purchases',
        'currency',
    ]

    search_fields = ['name', 'description']

    ordering_fields = ['year', 'rate', 'created']
    ordering = '-year'


class TaxConfigurationDetail(RetrieveUpdateDestroyAPI):
    """API endpoint for detail of a single TaxConfiguration object."""

    serializer_class = TaxConfigurationSerializer
    queryset = TaxConfiguration.objects.all()


# URL patterns for tax API
tax_api_urls = [
    path(
        'configuration/',
        include([
            path(
                '<int:pk>/',
                TaxConfigurationDetail.as_view(),
                name='api-tax-configuration-detail',
            ),
            path('', TaxConfigurationList.as_view(), name='api-tax-configuration-list'),
        ]),
    )
]
