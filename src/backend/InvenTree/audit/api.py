"""API endpoints for the audit app."""

from django.db.models import Q
from django.urls import path
from django.utils.translation import gettext_lazy as _

from django_filters import rest_framework as rest_filters
from rest_framework.exceptions import ValidationError

import audit.serializers
from audit.models import AuditLogEntry
from audit.permissions import (
    get_viewable_audit_content_types,
    user_can_view_audit_model,
)
from common.filters import determine_content_type
from InvenTree.filters import SEARCH_ORDER_FILTER
from InvenTree.mixins import ListAPI, RetrieveAPI
from InvenTree.permissions import IsAuthenticatedOrReadScope


class AuditLogFilter(rest_filters.FilterSet):
    """Custom filters for the AuditLogList API endpoint."""

    class Meta:
        """Metaclass options."""

        model = AuditLogEntry
        fields = ['action', 'actor', 'cid']

    model_type = rest_filters.CharFilter(
        method='filter_noop',
        label=_('Model Type'),
        help_text=_('Model type (e.g. "order.purchaseorder" or "purchaseorder")'),
    )

    model_id = rest_filters.CharFilter(
        method='filter_noop',
        label=_('Model ID'),
        help_text=_('Primary key of the object (requires model_type)'),
    )

    include_children = rest_filters.BooleanFilter(
        method='filter_noop',
        label=_('Include Children'),
        help_text=_('Include entries for child objects (default = true)'),
    )

    min_date = rest_filters.DateFilter(
        field_name='timestamp', lookup_expr='date__gte', label=_('Min Date')
    )

    max_date = rest_filters.DateFilter(
        field_name='timestamp', lookup_expr='date__lte', label=_('Max Date')
    )

    def filter_noop(self, queryset, name, value):
        """Combined filtering is performed in filter_queryset()."""
        return queryset

    def filter_queryset(self, queryset):
        """Filter by (model_type, model_id), optionally including child entries."""
        queryset = super().filter_queryset(queryset)

        model_type = self.form.cleaned_data.get('model_type')
        model_id = self.form.cleaned_data.get('model_id')
        include_children = self.form.cleaned_data.get('include_children')

        if include_children is None:
            include_children = True

        if model_id and not model_type:
            raise ValidationError({'model_id': _('model_type must also be provided')})

        if not model_type:
            return queryset

        ct = determine_content_type(model_type)

        if ct is None:
            raise ValidationError({'model_type': _('Invalid model type')})

        own = Q(content_type=ct)
        children = Q(parent_content_type=ct)

        if model_id:
            own &= Q(object_pk=str(model_id))
            children &= Q(parent_object_pk=str(model_id))

        # Querying *through* a parent requires permission to view the parent model,
        # otherwise the parent linkage of child objects would be exposed
        user = getattr(self.request, 'user', None)

        if include_children and user_can_view_audit_model(user, ct.model_class()):
            return queryset.filter(own | children)

        return queryset.filter(own)


class AuditLogMixin:
    """Mixin class for AuditLogEntry API endpoints."""

    queryset = AuditLogEntry.objects.all().select_related(
        'content_type', 'parent_content_type'
    )
    serializer_class = audit.serializers.AuditLogEntrySerializer
    permission_classes = [IsAuthenticatedOrReadScope]

    def get_queryset(self):
        """Restrict entries to those the requesting user is allowed to view."""
        queryset = super().get_queryset()

        allowed = get_viewable_audit_content_types(self.request.user)

        if allowed is None:
            return queryset

        # Note: parent permissions are handled by the filter (and serializer)
        return queryset.filter(content_type__in=allowed)


class AuditLogList(AuditLogMixin, ListAPI):
    """List API endpoint for audit log entries (read-only)."""

    filterset_class = AuditLogFilter
    filter_backends = SEARCH_ORDER_FILTER

    ordering_fields = ['timestamp', 'action', 'actor']
    ordering = '-timestamp'

    search_fields = ['object_repr', 'actor__username']


class AuditLogDetail(AuditLogMixin, RetrieveAPI):
    """Detail API endpoint for a single audit log entry (read-only)."""


audit_api_urls = [
    path('<int:pk>/', AuditLogDetail.as_view(), name='api-audit-log-detail'),
    path('', AuditLogList.as_view(), name='api-audit-log-list'),
]
