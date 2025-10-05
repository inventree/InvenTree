"""API endpoints for the tenant app."""

from django.db.models import Q
from django.urls import path
from django.utils.translation import gettext_lazy as _

import django_filters.rest_framework.filters as rest_filters
from django_filters.rest_framework.filterset import FilterSet

from InvenTree.filters import SEARCH_ORDER_FILTER
from InvenTree.mixins import ListCreateAPI, RetrieveUpdateDestroyAPI
from InvenTree.permissions import IsStaffOrReadOnlyScope

from .models import Tenant
from .serializers import TenantSerializer


class TenantFilter(FilterSet):
    """API filters for the TenantList endpoint."""

    class Meta:
        """Metaclass options."""

        model = Tenant
        fields = ['is_active', 'name', 'code']

    search = rest_filters.CharFilter(label=_('Search'), method='filter_search')

    def filter_search(self, queryset, name, value):
        """Filter the queryset by search term."""
        return queryset.filter(
            Q(name__icontains=value)
            | Q(description__icontains=value)
            | Q(code__icontains=value)
            | Q(contact_name__icontains=value)
            | Q(contact_email__icontains=value)
        )


class TenantList(ListCreateAPI):
    """API endpoint for accessing a list of Tenant objects.

    Provides two methods:
    - GET: Return list of tenant objects
    - POST: Create a new tenant object
    """

    permission_classes = [IsStaffOrReadOnlyScope]
    serializer_class = TenantSerializer
    queryset = Tenant.objects.all()
    filter_backends = SEARCH_ORDER_FILTER
    filterset_class = TenantFilter

    search_fields = ['name', 'description', 'code', 'contact_name', 'contact_email']

    ordering_fields = ['name', 'code', 'is_active']
    ordering = 'name'


class TenantDetail(RetrieveUpdateDestroyAPI):
    """API endpoint for detail of a single Tenant object."""

    permission_classes = [IsStaffOrReadOnlyScope]
    serializer_class = TenantSerializer
    queryset = Tenant.objects.all()


tenant_api_urls = [
    # Tenant URLs
    path('tenant/', TenantList.as_view(), name='api-tenant-list'),
    path('tenant/<int:pk>/', TenantDetail.as_view(), name='api-tenant-detail'),
]
