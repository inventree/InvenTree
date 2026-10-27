"""API endpoints for the audit app."""

from django import forms
from django.db.models import Q
from django.urls import include, path
from django.utils.text import capfirst
from django.utils.translation import gettext_lazy as _

from django_filters import rest_framework as rest_filters
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError

import audit.serializers
from audit.models import AuditLogEntry
from audit.permissions import (
    get_viewable_audit_content_types,
    parent_permission_content_types,
    user_can_view_audit_model,
)
from common.filters import determine_content_type
from InvenTree.filters import SEARCH_ORDER_FILTER
from InvenTree.helpers_api import InvenTreeApiRouter
from InvenTree.permissions import IsAuthenticatedOrReadScope


def audited_model_type_choices(user=None) -> list[tuple[str, str]]:
    """Return (model_type, label) choices for the audited models.

    If a user is provided, only the models which the user may view are returned.
    """
    from django.contrib.contenttypes.models import ContentType

    from audit.registry import audited_models

    allowed = get_viewable_audit_content_types(user) if user else None

    choices = []

    for model in audited_models():
        ct = ContentType.objects.get_for_model(model)

        if allowed is not None and ct.pk not in allowed:
            continue

        choices.append((
            f'{ct.app_label}.{ct.model}',
            capfirst(str(model._meta.verbose_name)),
        ))

    return sorted(choices, key=lambda choice: choice[1])


class AnyValueChoiceField(forms.ChoiceField):
    """A ChoiceField which provides a list of choices, but accepts any value.

    The choices are used to describe the common values (e.g. for display in a client),
    while other supported formats are still accepted by the filter.
    """

    def valid_value(self, value):
        """Accept any value."""
        return True


# Note: the choices are dynamic (and any value is accepted), so the schema type is declared explicitly
@extend_schema_field(OpenApiTypes.STR)
class ModelTypeChoiceFilter(rest_filters.ChoiceFilter):
    """Choice filter for the model type of an audit entry.

    The choices are the audited model types ('app_label.model'), but any value supported
    by common.filters.determine_content_type is accepted (e.g. a model name, or a ContentType ID).
    """

    field_class = AnyValueChoiceField


class AuditLogFilter(rest_filters.FilterSet):
    """Custom filters for the AuditLogList API endpoint."""

    class Meta:
        """Metaclass options."""

        model = AuditLogEntry
        fields = ['action', 'actor', 'cid', 'event_type']

    model_type = ModelTypeChoiceFilter(
        choices=audited_model_type_choices,
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

    def __init__(self, *args, **kwargs):
        """Limit the model type choices to those which the requesting user may view."""
        super().__init__(*args, **kwargs)

        user = getattr(self.request, 'user', None)

        if user and user.is_authenticated:
            self.filters['model_type'].extra['choices'] = audited_model_type_choices(
                user
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


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for audit log entries (read-only).

    - GET (list): Return a list of audit log entries
    - GET (detail): Return a single audit log entry
    """

    queryset = AuditLogEntry.objects.all().select_related(
        'content_type', 'parent_content_type'
    )
    serializer_class = audit.serializers.AuditLogEntrySerializer

    # Entries are filtered by the user's permissions on each audited model
    # (some models are further restricted to staff users, see audit.registry.AUDIT_VIEW_RESTRICTIONS)
    permission_classes = [IsAuthenticatedOrReadScope]

    filterset_class = AuditLogFilter
    filter_backends = SEARCH_ORDER_FILTER

    ordering_fields = ['timestamp', 'action', 'actor']
    ordering = '-timestamp'

    search_fields = ['object_repr', 'actor__username']

    def get_queryset(self):
        """Restrict entries to those the requesting user is allowed to view."""
        queryset = super().get_queryset()

        allowed = get_viewable_audit_content_types(self.request.user)

        if allowed is None:
            return queryset

        queryset = queryset.filter(content_type__in=allowed)

        # Some models (e.g. attachments) are only visible with permission on the parent model
        if restricted := parent_permission_content_types():
            queryset = queryset.filter(
                ~Q(content_type__in=restricted) | Q(parent_content_type__in=allowed)
            )

        # Note: otherwise parent permissions are handled by the filter (and serializer)
        return queryset


audit_router = InvenTreeApiRouter()
audit_router.register('', AuditLogViewSet, basename='api-audit-log')

audit_api_urls = [path('', include(audit_router.urls))]
