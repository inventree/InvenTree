"""JSON API for the Order app."""

from decimal import Decimal
from typing import Any, cast

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model, login
from django.contrib.auth.models import User
from django.db.models import F, Q
from django.http.response import JsonResponse
from django.urls import include, path, re_path
from django.utils.translation import gettext_lazy as _

import django_filters.rest_framework.filters as rest_filters
import requests
import rest_framework.serializers
import structlog
from django_filters.rest_framework.filterset import FilterSet
from django_ical.views import ICalFeed
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, extend_schema_field
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.response import Response

import build.models
import common.models
import common.serializers
import common.settings
import company.models as company_models
import stock.models as stock_models
import stock.serializers as stock_serializers
from data_exporter.mixins import DataExportViewMixin
from generic.states.api import StatusView
from InvenTree.api import (
    BulkUpdateMixin,
    ListCreateDestroyAPIView,
    ParameterListMixin,
    meta_path,
)
from InvenTree.fields import InvenTreeOutputOption, OutputConfiguration
from InvenTree.filters import SEARCH_ORDER_FILTER, InvenTreeDateFilter
from InvenTree.helpers import current_date, str2bool
from InvenTree.helpers_model import construct_absolute_url, get_base_url
from InvenTree.mixins import (
    CreateAPI,
    ListAPI,
    ListCreateAPI,
    OutputOptionsMixin,
    RetrieveUpdateDestroyAPI,
    SerializerContextMixin,
)
from order import models, serializers
from order.status_codes import (
    PurchaseOrderStatus,
    PurchaseOrderStatusGroups,
    ReturnOrderLineStatus,
    ReturnOrderStatus,
    SalesOrderStatus,
    SalesOrderStatusGroups,
)
from part.models import Part
from users.models import Owner

logger = structlog.get_logger('inventree')


class GeneralExtraLineListOutputOptions(OutputConfiguration):
    """Output options for the GeneralExtraLineList endpoint."""

    OPTIONS = [InvenTreeOutputOption('order_detail')]


class GeneralExtraLineList(SerializerContextMixin, DataExportViewMixin):
    """General template for ExtraLine API classes."""

    def get_queryset(self, *args, **kwargs):
        """Return the annotated queryset for this endpoint."""
        queryset = super().get_queryset(*args, **kwargs)

        queryset = queryset.prefetch_related('order')

        return queryset

    output_options = GeneralExtraLineListOutputOptions

    filter_backends = SEARCH_ORDER_FILTER

    ordering_fields = ['quantity', 'notes', 'reference', 'line']

    ordering_field_aliases = {'line': ['line_int', 'line']}

    search_fields = ['quantity', 'notes', 'reference', 'description']

    filterset_fields = ['order']


class OrderCreateMixin:
    """Mixin class which handles order creation via API."""

    def create(self, request, *args, **kwargs):
        """Save user information on order creation."""
        serializer = self.get_serializer(data=self.clean_data(request.data))
        serializer.is_valid(raise_exception=True)

        item = serializer.save()
        item.created_by = request.user
        item.save()

        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )


class OrderFilter(FilterSet):
    """Base class for custom API filters for the OrderList endpoint."""

    # Filter against order status
    status = rest_filters.NumberFilter(label=_('Order Status'), method='filter_status')

    def filter_status(self, queryset, name, value):
        """Filter by integer status code.

        Note: Also account for the possibility of a custom status code.
        """
        q1 = Q(status=value, status_custom_key__isnull=True)
        q2 = Q(status_custom_key=value)

        return queryset.filter(q1 | q2).distinct()

    # Exact match for reference
    reference = rest_filters.CharFilter(
        label=_('Order Reference'), field_name='reference', lookup_expr='iexact'
    )

    assigned_to_me = rest_filters.BooleanFilter(
        label=_('Assigned to me'), method='filter_assigned_to_me'
    )

    def filter_assigned_to_me(self, queryset, name, value):
        """Filter by orders which are assigned to the current user."""
        # Work out who "me" is!
        owners = Owner.get_owners_matching_user(self.request.user)

        if str2bool(value):
            return queryset.filter(responsible__in=owners)
        return queryset.exclude(responsible__in=owners)

    overdue = rest_filters.BooleanFilter(label='overdue', method='filter_overdue')

    def filter_overdue(self, queryset, name, value):
        """Generic filter for determining if an order is 'overdue'.

        Note that the overdue_filter() classmethod must be defined for the model
        """
        if str2bool(value):
            return queryset.filter(self.Meta.model.overdue_filter())
        return queryset.exclude(self.Meta.model.overdue_filter())

    outstanding = rest_filters.BooleanFilter(
        label=_('Outstanding'), method='filter_outstanding'
    )

    def filter_outstanding(self, queryset, name, value):
        """Generic filter for determining if an order is 'outstanding'."""
        if str2bool(value):
            return queryset.filter(status__in=self.Meta.model.get_status_class().OPEN)
        return queryset.exclude(status__in=self.Meta.model.get_status_class().OPEN)

    project_code = rest_filters.ModelChoiceFilter(
        queryset=common.models.ProjectCode.objects.all(),
        field_name='project_code',
        label=_('Project Code'),
    )

    has_project_code = rest_filters.BooleanFilter(
        method='filter_has_project_code', label=_('Has Project Code')
    )

    def filter_has_project_code(self, queryset, name, value):
        """Filter by whether or not the order has a project code."""
        if str2bool(value):
            return queryset.exclude(project_code=None)
        return queryset.filter(project_code=None)

    assigned_to = rest_filters.ModelChoiceFilter(
        queryset=Owner.objects.all(), field_name='responsible', label=_('Responsible')
    )

    created_by = rest_filters.ModelChoiceFilter(
        queryset=User.objects.all(), field_name='created_by', label=_('Created By')
    )

    created_before = InvenTreeDateFilter(
        label=_('Created Before'), field_name='creation_date', lookup_expr='lt'
    )

    created_after = InvenTreeDateFilter(
        label=_('Created After'), field_name='creation_date', lookup_expr='gt'
    )

    has_start_date = rest_filters.BooleanFilter(
        label=_('Has Start Date'), method='filter_has_start_date'
    )

    def filter_has_start_date(self, queryset, name, value):
        """Filter by whether or not the order has a start date."""
        return queryset.filter(start_date__isnull=not str2bool(value))

    start_date_before = InvenTreeDateFilter(
        label=_('Start Date Before'), field_name='start_date', lookup_expr='lt'
    )

    start_date_after = InvenTreeDateFilter(
        label=_('Start Date After'), field_name='start_date', lookup_expr='gt'
    )

    has_target_date = rest_filters.BooleanFilter(
        label=_('Has Target Date'), method='filter_has_target_date'
    )

    def filter_has_target_date(self, queryset, name, value):
        """Filter by whether or not the order has a target date."""
        return queryset.filter(target_date__isnull=not str2bool(value))

    target_date_before = InvenTreeDateFilter(
        label=_('Target Date Before'), field_name='target_date', lookup_expr='lt'
    )

    target_date_after = InvenTreeDateFilter(
        label=_('Target Date After'), field_name='target_date', lookup_expr='gt'
    )

    updated_before = InvenTreeDateFilter(
        label=_('Updated Before'), field_name='updated_at', lookup_expr='lt'
    )

    updated_after = InvenTreeDateFilter(
        label=_('Updated After'), field_name='updated_at', lookup_expr='gt'
    )

    min_date = InvenTreeDateFilter(label=_('Min Date'), method='filter_min_date')

    def filter_min_date(self, queryset, name, value):
        """Filter the queryset to include orders *after* a specified date.

        This is used in combination with filter_max_date,
        to provide a queryset which matches a particular range of dates.

        In particular, this is used in the UI for the calendar view.
        """
        q1 = Q(
            creation_date__gte=value, issue_date__isnull=True, start_date__isnull=True
        )
        q2 = Q(issue_date__gte=value, start_date__isnull=True)
        q3 = Q(start_date__gte=value)
        q4 = Q(target_date__gte=value)

        return queryset.filter(q1 | q2 | q3 | q4).distinct()

    max_date = InvenTreeDateFilter(label=_('Max Date'), method='filter_max_date')

    def filter_max_date(self, queryset, name, value):
        """Filter the queryset to include orders *before* a specified date.

        This is used in combination with filter_min_date,
        to provide a queryset which matches a particular range of dates.

        In particular, this is used in the UI for the calendar view.
        """
        q1 = Q(
            creation_date__lte=value, issue_date__isnull=True, start_date__isnull=True
        )
        q2 = Q(issue_date__lte=value, start_date__isnull=True)
        q3 = Q(start_date__lte=value)
        q4 = Q(target_date__lte=value)

        return queryset.filter(q1 | q2 | q3 | q4).distinct()


class LineItemFilter(FilterSet):
    """Base class for custom API filters for order line item list(s)."""

    # Filter by order status
    order_status = rest_filters.NumberFilter(
        label=_('Order Status'), field_name='order__status'
    )

    has_pricing = rest_filters.BooleanFilter(
        label=_('Has Pricing'), method='filter_has_pricing'
    )

    def filter_has_pricing(self, queryset, name, value):
        """Filter by whether or not the line item has pricing information."""
        filters = {self.Meta.price_field: None}

        if str2bool(value):
            return queryset.exclude(**filters)
        return queryset.filter(**filters)


class PurchaseOrderFilter(OrderFilter):
    """Custom API filters for the PurchaseOrderList endpoint."""

    class Meta:
        """Metaclass options."""

        model = models.PurchaseOrder
        fields = ['supplier']

    part = rest_filters.ModelChoiceFilter(
        queryset=Part.objects.all(),
        field_name='part',
        label=_('Part'),
        method='filter_part',
    )

    @extend_schema_field(rest_framework.serializers.IntegerField(help_text=_('Part')))
    def filter_part(self, queryset, name, part: Part):
        """Filter by provided Part instance."""
        orders = part.purchase_orders()

        return queryset.filter(pk__in=[o.pk for o in orders])

    supplier_part = rest_filters.ModelChoiceFilter(
        queryset=company_models.SupplierPart.objects.all(),
        label=_('Supplier Part'),
        method='filter_supplier_part',
    )

    @extend_schema_field(
        rest_framework.serializers.IntegerField(help_text=_('Supplier Part'))
    )
    def filter_supplier_part(
        self, queryset, name, supplier_part: company_models.SupplierPart
    ):
        """Filter by provided SupplierPart instance."""
        orders = supplier_part.purchase_orders()

        return queryset.filter(pk__in=[o.pk for o in orders])

    completed_before = InvenTreeDateFilter(
        label=_('Completed Before'), field_name='complete_date', lookup_expr='lt'
    )

    completed_after = InvenTreeDateFilter(
        label=_('Completed After'), field_name='complete_date', lookup_expr='gt'
    )

    external_build = rest_filters.ModelChoiceFilter(
        queryset=build.models.Build.objects.filter(external=True),
        method='filter_external_build',
        label=_('External Build Order'),
    )

    @extend_schema_field(
        rest_framework.serializers.IntegerField(help_text=_('External Build Order'))
    )
    def filter_external_build(self, queryset, name, build):
        """Filter to only include orders which fill fulfil the provided Build Order.

        To achieve this, we return any order which has a line item which is allocated to the build order.
        """
        return queryset.filter(lines__build_order=build).distinct()


class PurchaseOrderOutputOptions(OutputConfiguration):
    """Output options for the PurchaseOrder endpoint."""

    OPTIONS = [InvenTreeOutputOption('supplier_detail')]


class PurchaseOrderMixin(SerializerContextMixin):
    """Mixin class for PurchaseOrder endpoints."""

    queryset = models.PurchaseOrder.objects.all().prefetch_related(
        'supplier', 'created_by'
    )
    serializer_class = serializers.PurchaseOrderSerializer

    def get_queryset(self, *args, **kwargs):
        """Return the annotated queryset for this endpoint."""
        queryset = super().get_queryset(*args, **kwargs)

        queryset = serializers.PurchaseOrderSerializer.annotate_queryset(queryset)

        return queryset


class PurchaseOrderList(
    PurchaseOrderMixin,
    OrderCreateMixin,
    DataExportViewMixin,
    OutputOptionsMixin,
    ParameterListMixin,
    ListCreateAPI,
):
    """API endpoint for accessing a list of PurchaseOrder objects.

    - GET: Return list of PurchaseOrder objects (with filters)
    - POST: Create a new PurchaseOrder object
    """

    filterset_class = PurchaseOrderFilter
    filter_backends = SEARCH_ORDER_FILTER
    output_options = PurchaseOrderOutputOptions

    ordering_field_aliases = {
        'reference': ['reference_int', 'reference'],
        'project_code': ['project_code__code'],
    }

    search_fields = [
        'reference',
        'supplier__name',
        'supplier_reference',
        'project_code__code',
        'description',
    ]

    ordering_fields = [
        'creation_date',
        'created_by',
        'reference',
        'supplier__name',
        'start_date',
        'target_date',
        'complete_date',
        'line_items',
        'status',
        'responsible',
        'total_price',
        'project_code',
        'updated_at',
    ]

    ordering = '-reference'


class PurchaseOrderDetail(
    PurchaseOrderMixin, OutputOptionsMixin, RetrieveUpdateDestroyAPI
):
    """API endpoint for detail view of a PurchaseOrder object."""

    output_options = PurchaseOrderOutputOptions


class PurchaseOrderContextMixin:
    """Mixin to add purchase order object as serializer context variable."""

    queryset = models.PurchaseOrder.objects.all()

    def get_serializer_context(self):
        """Add the PurchaseOrder object to the serializer context."""
        context = super().get_serializer_context()

        # Pass the purchase order through to the serializer for validation
        try:
            context['order'] = models.PurchaseOrder.objects.get(
                pk=self.kwargs.get('pk', None)
            )
        except Exception:
            pass

        context['request'] = self.request

        return context


class PurchaseOrderHold(PurchaseOrderContextMixin, CreateAPI):
    """API endpoint to place a PurchaseOrder on hold."""

    serializer_class = serializers.PurchaseOrderHoldSerializer


class PurchaseOrderCancel(PurchaseOrderContextMixin, CreateAPI):
    """API endpoint to 'cancel' a purchase order.

    The purchase order must be in a state which can be cancelled
    """

    serializer_class = serializers.PurchaseOrderCancelSerializer


class PurchaseOrderComplete(PurchaseOrderContextMixin, CreateAPI):
    """API endpoint to 'complete' a purchase order."""

    serializer_class = serializers.PurchaseOrderCompleteSerializer


class PurchaseOrderIssue(PurchaseOrderContextMixin, CreateAPI):
    """API endpoint to 'issue' (place) a PurchaseOrder."""

    serializer_class = serializers.PurchaseOrderIssueSerializer


@extend_schema(responses={201: stock_serializers.StockItemSerializer(many=True)})
class PurchaseOrderReceive(PurchaseOrderContextMixin, CreateAPI):
    """API endpoint to receive stock items against a PurchaseOrder.

    - The purchase order is specified in the URL.
    - Items to receive are specified as a list called "items" with the following options:
        - line_item: pk of the PO Line item
        - supplier_part: pk value of the supplier part
        - quantity: quantity to receive
        - status: stock item status
        - expiry_date: stock item expiry date (optional)
        - location: destination for stock item (optional)
        - batch_code: the batch code for this stock item
        - serial_numbers: serial numbers for this stock item
    - A global location must also be specified. This is used when no locations are specified for items, and no location is given in the PO line item
    """

    queryset = models.PurchaseOrderLineItem.objects.none()
    serializer_class = serializers.PurchaseOrderReceiveSerializer
    pagination_class = None

    def create(self, request, *args, **kwargs):
        """Override the create method to handle stock item creation."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        items = serializer.save()
        queryset = stock_serializers.StockItemSerializer.annotate_queryset(items)
        response = stock_serializers.StockItemSerializer(queryset, many=True)

        return Response(response.data, status=status.HTTP_201_CREATED)


class PurchaseOrderLineItemFilter(LineItemFilter):
    """Custom filters for the PurchaseOrderLineItemList endpoint."""

    class Meta:
        """Metaclass options."""

        price_field = 'purchase_price'
        model = models.PurchaseOrderLineItem
        fields = []

    order = rest_filters.ModelChoiceFilter(
        queryset=models.PurchaseOrder.objects.all(),
        field_name='order',
        label=_('Order'),
    )

    order_complete = rest_filters.BooleanFilter(
        label=_('Order Complete'), method='filter_order_complete'
    )

    def filter_order_complete(self, queryset, name, value):
        """Filter by whether the order is 'complete' or not."""
        if str2bool(value):
            return queryset.filter(order__status=PurchaseOrderStatus.COMPLETE.value)

        return queryset.exclude(order__status=PurchaseOrderStatus.COMPLETE.value)

    part = rest_filters.ModelChoiceFilter(
        queryset=company_models.SupplierPart.objects.all(),
        field_name='part',
        label=_('Supplier Part'),
    )

    include_variants = rest_filters.BooleanFilter(
        label=_('Include Variants'), method='filter_include_variants'
    )

    def filter_include_variants(self, queryset, name, value):
        """Filter by whether or not to include variants of the selected part.

        Note:
        - This filter does nothing by itself, and requires the 'base_part' filter to be set.
        - Refer to the 'filter_base_part' method for more information.
        """
        return queryset

    base_part = rest_filters.ModelChoiceFilter(
        queryset=Part.objects.filter(purchaseable=True),
        method='filter_base_part',
        label=_('Internal Part'),
    )

    @extend_schema_field(
        rest_framework.serializers.IntegerField(help_text=_('Internal Part'))
    )
    def filter_base_part(self, queryset, name, base_part):
        """Filter by the 'base_part' attribute.

        Note:
        - If "include_variants" is True, include all variants of the selected part
        - Otherwise, just filter by the selected part
        """
        include_variants = str2bool(self.data.get('include_variants', False))

        if include_variants:
            parts = base_part.get_descendants(include_self=True)
            return queryset.filter(part__part__in=parts)
        else:
            return queryset.filter(part__part=base_part)

    pending = rest_filters.BooleanFilter(
        method='filter_pending', label=_('Order Pending')
    )

    def filter_pending(self, queryset, name, value):
        """Filter by "pending" status (order status = pending)."""
        if str2bool(value):
            return queryset.filter(order__status__in=PurchaseOrderStatusGroups.OPEN)
        return queryset.exclude(order__status__in=PurchaseOrderStatusGroups.OPEN)

    received = rest_filters.BooleanFilter(
        label=_('Items Received'), method='filter_received'
    )

    def filter_received(self, queryset, name, value):
        """Filter by lines which are "received" (or "not" received).

        A line is considered "received" when received >= quantity
        """
        q = Q(received__gte=F('quantity'))

        if str2bool(value):
            return queryset.filter(q)
        # Only count "pending" orders
        return queryset.exclude(q).filter(
            order__status__in=PurchaseOrderStatusGroups.OPEN
        )


class PurchaseOrderLineItemOutputOptions(OutputConfiguration):
    """Output options for the PurchaseOrderLineItem endpoint."""

    OPTIONS = [
        InvenTreeOutputOption('part_detail'),
        InvenTreeOutputOption('order_detail'),
    ]


class PurchaseOrderLineItemMixin(SerializerContextMixin):
    """Mixin class for PurchaseOrderLineItem endpoints."""

    queryset = models.PurchaseOrderLineItem.objects.all()
    serializer_class = serializers.PurchaseOrderLineItemSerializer

    def get_queryset(self, *args, **kwargs):
        """Return annotated queryset for this endpoint."""
        queryset = super().get_queryset(*args, **kwargs)

        queryset = serializers.PurchaseOrderLineItemSerializer.annotate_queryset(
            queryset
        )

        return queryset

    def perform_update(self, serializer):
        """Override the perform_update method to auto-update pricing if required."""
        super().perform_update(serializer)

        # possibly auto-update pricing based on the supplier part pricing data
        if serializer.validated_data.get('auto_pricing', True):
            serializer.instance.update_pricing()


class PurchaseOrderLineItemList(
    PurchaseOrderLineItemMixin,
    DataExportViewMixin,
    OutputOptionsMixin,
    ListCreateDestroyAPIView,
):
    """API endpoint for accessing a list of PurchaseOrderLineItem objects.

    - GET: Return a list of PurchaseOrder Line Item objects
    - POST: Create a new PurchaseOrderLineItem object
    """

    filterset_class = PurchaseOrderLineItemFilter
    output_options = PurchaseOrderLineItemOutputOptions

    def create(self, request, *args, **kwargs):
        """Create or update a new PurchaseOrderLineItem object."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = cast(dict, serializer.validated_data)

        # possibly merge duplicate items
        line_item = None
        if data.get('merge_items', True):
            other_line = models.PurchaseOrderLineItem.objects.filter(
                part=data.get('part'),
                order=data.get('order'),
                target_date=data.get('target_date'),
                destination=data.get('destination'),
            ).first()

            if other_line is not None:
                other_line.quantity += Decimal(data.get('quantity', 0))
                other_line.save()

                line_item = other_line

        # otherwise create a new line item
        if line_item is None:
            line_item = serializer.save()

        # possibly auto-update pricing based on the supplier part pricing data
        if data.get('auto_pricing', True) and isinstance(
            line_item, models.PurchaseOrderLineItem
        ):
            line_item.update_pricing()

        serializer = serializers.PurchaseOrderLineItemSerializer(line_item)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    filter_backends = SEARCH_ORDER_FILTER

    ordering_field_aliases = {
        'MPN': 'part__manufacturer_part__MPN',
        'SKU': 'part__SKU',
        'IPN': 'part__part__IPN',
        'part_name': 'part__part__name',
        'order': 'order__reference',
        'status': 'order__status',
        'complete_date': 'order__complete_date',
        'line': ['line_int', 'line', 'part__SKU'],
    }

    ordering_fields = [
        'MPN',
        'part_name',
        'purchase_price',
        'quantity',
        'received',
        'reference',
        'SKU',
        'IPN',
        'total_price',
        'target_date',
        'order',
        'status',
        'complete_date',
        'line',
    ]

    search_fields = [
        'part__part__name',
        'part__part__description',
        'part__manufacturer_part__MPN',
        'part__SKU',
        'reference',
    ]


class PurchaseOrderLineItemDetail(
    PurchaseOrderLineItemMixin, OutputOptionsMixin, RetrieveUpdateDestroyAPI
):
    """Detail API endpoint for PurchaseOrderLineItem object."""

    output_options = PurchaseOrderLineItemOutputOptions


class PurchaseOrderExtraLineList(
    GeneralExtraLineList, OutputOptionsMixin, ListCreateAPI
):
    """API endpoint for accessing a list of PurchaseOrderExtraLine objects."""

    queryset = models.PurchaseOrderExtraLine.objects.all()
    serializer_class = serializers.PurchaseOrderExtraLineSerializer


class PurchaseOrderExtraLineDetail(RetrieveUpdateDestroyAPI):
    """API endpoint for detail view of a PurchaseOrderExtraLine object."""

    queryset = models.PurchaseOrderExtraLine.objects.all()
    serializer_class = serializers.PurchaseOrderExtraLineSerializer


class SalesOrderFilter(OrderFilter):
    """Custom API filters for the SalesOrderList endpoint."""

    class Meta:
        """Metaclass options."""

        model = models.SalesOrder
        fields = ['customer']

    include_variants = rest_filters.BooleanFilter(
        label=_('Include Variants'), method='filter_include_variants'
    )

    def filter_include_variants(self, queryset, name, value):
        """Filter by whether or not to include variants of the selected part.

        Note:
        - This filter does nothing by itself, and requires the 'part' filter to be set.
        - Refer to the 'filter_part' method for more information.
        """
        return queryset

    part = rest_filters.ModelChoiceFilter(
        queryset=Part.objects.all(), field_name='part', method='filter_part'
    )

    @extend_schema_field(OpenApiTypes.INT)
    def filter_part(self, queryset, name, part):
        """Filter SalesOrder by selected 'part'.

        Note:
        - If 'include_variants' is set to True, then all variants of the selected part will be included.
        - Otherwise, just filter by the selected part.
        """
        include_variants = str2bool(self.data.get('include_variants', False))

        # Construct a queryset of parts to filter by
        if include_variants:
            parts = part.get_descendants(include_self=True)
        else:
            parts = Part.objects.filter(pk=part.pk)

        # Now that we have a queryset of parts, find all the matching sales orders
        line_items = models.SalesOrderLineItem.objects.filter(part__in=parts)

        # Generate a list of ID values for the matching sales orders
        sales_orders = line_items.values_list('order', flat=True).distinct()

        # Now we have a list of matching IDs, filter the queryset
        return queryset.filter(pk__in=sales_orders)

    completed_before = InvenTreeDateFilter(
        label=_('Completed Before'), field_name='shipment_date', lookup_expr='lt'
    )

    completed_after = InvenTreeDateFilter(
        label=_('Completed After'), field_name='shipment_date', lookup_expr='gt'
    )


class SalesOrderMixin(SerializerContextMixin):
    """Mixin class for SalesOrder endpoints."""

    queryset = models.SalesOrder.objects.all().prefetch_related(
        'customer', 'created_by'
    )
    serializer_class = serializers.SalesOrderSerializer

    def get_queryset(self, *args, **kwargs):
        """Return annotated queryset for this endpoint."""
        queryset = super().get_queryset(*args, **kwargs)

        queryset = serializers.SalesOrderSerializer.annotate_queryset(queryset)

        return queryset


class SalesOrderOutputOptions(OutputConfiguration):
    """Output options for the SalesOrder endpoint."""

    OPTIONS = [InvenTreeOutputOption('customer_detail')]


class SalesOrderList(
    SalesOrderMixin,
    OrderCreateMixin,
    DataExportViewMixin,
    OutputOptionsMixin,
    ParameterListMixin,
    ListCreateAPI,
):
    """API endpoint for accessing a list of SalesOrder objects.

    - GET: Return list of SalesOrder objects (with filters)
    - POST: Create a new SalesOrder
    """

    filterset_class = SalesOrderFilter
    filter_backends = SEARCH_ORDER_FILTER
    output_options = SalesOrderOutputOptions

    ordering_field_aliases = {
        'reference': ['reference_int', 'reference'],
        'project_code': ['project_code__code'],
    }

    filterset_fields = ['customer']

    ordering_fields = [
        'creation_date',
        'created_by',
        'reference',
        'customer__name',
        'customer_reference',
        'status',
        'start_date',
        'target_date',
        'line_items',
        'shipment_date',
        'total_price',
        'project_code',
        'updated_at',
    ]

    search_fields = [
        'customer__name',
        'reference',
        'description',
        'customer_reference',
        'project_code__code',
    ]

    ordering = '-reference'


class SalesOrderDetail(SalesOrderMixin, OutputOptionsMixin, RetrieveUpdateDestroyAPI):
    """API endpoint for detail view of a SalesOrder object."""

    output_options = SalesOrderOutputOptions


class SalesOrderLineItemFilter(LineItemFilter):
    """Custom filters for SalesOrderLineItemList endpoint."""

    class Meta:
        """Metaclass options."""

        price_field = 'sale_price'
        model = models.SalesOrderLineItem
        fields = []

    order = rest_filters.ModelChoiceFilter(
        queryset=models.SalesOrder.objects.all(), field_name='order', label=_('Order')
    )

    def filter_include_variants(self, queryset, name, value):
        """Filter by whether or not to include variants of the selected part.

        Note:
        - This filter does nothing by itself, and requires the 'part' filter to be set.
        - Refer to the 'filter_part' method for more information.
        """
        return queryset

    part = rest_filters.ModelChoiceFilter(
        queryset=Part.objects.all(),
        field_name='part',
        label=_('Part'),
        method='filter_part',
    )

    @extend_schema_field(OpenApiTypes.INT)
    def filter_part(self, queryset, name, part):
        """Filter SalesOrderLineItem by selected 'part'.

        Note:
        - If 'include_variants' is set to True, then all variants of the selected part will be included.
        - Otherwise, just filter by the selected part.
        """
        include_variants = str2bool(self.data.get('include_variants', False))

        # Construct a queryset of parts to filter by
        if include_variants:
            parts = part.get_descendants(include_self=True)
        else:
            parts = Part.objects.filter(pk=part.pk)

        return queryset.filter(part__in=parts)

    allocated = rest_filters.BooleanFilter(
        label=_('Allocated'), method='filter_allocated'
    )

    def filter_allocated(self, queryset, name, value):
        """Filter by lines which are 'allocated'.

        A line is 'allocated' when allocated >= quantity
        """
        q = Q(allocated__gte=F('quantity'))

        if str2bool(value):
            return queryset.filter(q)
        return queryset.exclude(q)

    completed = rest_filters.BooleanFilter(
        label=_('Completed'), method='filter_completed'
    )

    def filter_completed(self, queryset, name, value):
        """Filter by lines which are "completed".

        A line is 'completed' when shipped >= quantity
        """
        q = Q(shipped__gte=F('quantity'))

        if str2bool(value):
            return queryset.filter(q)
        return queryset.exclude(q)

    order_complete = rest_filters.BooleanFilter(
        label=_('Order Complete'), method='filter_order_complete'
    )

    def filter_order_complete(self, queryset, name, value):
        """Filter by whether the order is 'complete' or not."""
        if str2bool(value):
            return queryset.filter(order__status__in=SalesOrderStatusGroups.COMPLETE)

        return queryset.exclude(order__status__in=SalesOrderStatusGroups.COMPLETE)

    order_outstanding = rest_filters.BooleanFilter(
        label=_('Order Outstanding'), method='filter_order_outstanding'
    )

    def filter_order_outstanding(self, queryset, name, value):
        """Filter by whether the order is 'outstanding' or not."""
        if str2bool(value):
            return queryset.filter(order__status__in=SalesOrderStatusGroups.OPEN)

        return queryset.exclude(order__status__in=SalesOrderStatusGroups.OPEN)


class SalesOrderLineItemMixin(SerializerContextMixin):
    """Mixin class for SalesOrderLineItem endpoints."""

    queryset = models.SalesOrderLineItem.objects.all()
    serializer_class = serializers.SalesOrderLineItemSerializer

    def get_queryset(self, *args, **kwargs):
        """Return annotated queryset for this endpoint."""
        queryset = super().get_queryset(*args, **kwargs)

        queryset = queryset.prefetch_related(
            'part',
            'allocations',
            'allocations__shipment',
            'allocations__item__part',
            'allocations__item__location',
            'order',
        )

        queryset = serializers.SalesOrderLineItemSerializer.annotate_queryset(queryset)

        return queryset


class SalesOrderLineItemOutputOptions(OutputConfiguration):
    """Output options for the SalesOrderAllocation endpoint."""

    OPTIONS = [
        InvenTreeOutputOption('part_detail'),
        InvenTreeOutputOption('order_detail'),
        InvenTreeOutputOption('customer_detail'),
    ]


class SalesOrderLineItemList(
    SalesOrderLineItemMixin, DataExportViewMixin, OutputOptionsMixin, ListCreateAPI
):
    """API endpoint for accessing a list of SalesOrderLineItem objects."""

    filterset_class = SalesOrderLineItemFilter

    filter_backends = SEARCH_ORDER_FILTER

    output_options = SalesOrderLineItemOutputOptions

    ordering_fields = [
        'customer',
        'order',
        'part',
        'IPN',
        'part__name',
        'quantity',
        'allocated',
        'shipped',
        'reference',
        'sale_price',
        'target_date',
        'line',
    ]

    ordering_field_aliases = {
        'customer': 'order__customer__name',
        'part': 'part__name',
        'IPN': 'part__IPN',
        'order': 'order__reference',
        'line': ['line_int', 'line', 'part__name'],
    }

    search_fields = ['part__name', 'quantity', 'reference']


class SalesOrderLineItemDetail(
    SalesOrderLineItemMixin, OutputOptionsMixin, RetrieveUpdateDestroyAPI
):
    """API endpoint for detail view of a SalesOrderLineItem object."""

    output_options = SalesOrderLineItemOutputOptions


class SalesOrderExtraLineList(GeneralExtraLineList, OutputOptionsMixin, ListCreateAPI):
    """API endpoint for accessing a list of SalesOrderExtraLine objects."""

    queryset = models.SalesOrderExtraLine.objects.all()
    serializer_class = serializers.SalesOrderExtraLineSerializer


class SalesOrderExtraLineDetail(RetrieveUpdateDestroyAPI):
    """API endpoint for detail view of a SalesOrderExtraLine object."""

    queryset = models.SalesOrderExtraLine.objects.all()
    serializer_class = serializers.SalesOrderExtraLineSerializer


class SalesOrderContextMixin:
    """Mixin to add sales order object as serializer context variable."""

    queryset = models.SalesOrder.objects.all()

    def get_serializer_context(self):
        """Add the 'order' reference to the serializer context for any classes which inherit this mixin."""
        ctx = super().get_serializer_context()

        ctx['request'] = self.request

        try:
            ctx['order'] = models.SalesOrder.objects.get(pk=self.kwargs.get('pk', None))
        except Exception:
            pass

        return ctx


class SalesOrderHold(SalesOrderContextMixin, CreateAPI):
    """API endpoint to place a SalesOrder on hold."""

    serializer_class = serializers.SalesOrderHoldSerializer


class SalesOrderCancel(SalesOrderContextMixin, CreateAPI):
    """API endpoint to cancel a SalesOrder."""

    serializer_class = serializers.SalesOrderCancelSerializer


class SalesOrderIssue(SalesOrderContextMixin, CreateAPI):
    """API endpoint to issue a SalesOrder."""

    serializer_class = serializers.SalesOrderIssueSerializer


class SalesOrderComplete(SalesOrderContextMixin, CreateAPI):
    """API endpoint for manually marking a SalesOrder as "complete"."""

    serializer_class = serializers.SalesOrderCompleteSerializer


class SalesOrderAllocateSerials(SalesOrderContextMixin, CreateAPI):
    """API endpoint to allocation stock items against a SalesOrder, by specifying serial numbers."""

    queryset = models.SalesOrder.objects.none()
    serializer_class = serializers.SalesOrderSerialAllocationSerializer


class SalesOrderAllocate(SalesOrderContextMixin, CreateAPI):
    """API endpoint to allocate stock items against a SalesOrder.

    - The SalesOrder is specified in the URL
    - See the SalesOrderShipmentAllocationSerializer class
    """

    queryset = models.SalesOrder.objects.none()
    serializer_class = serializers.SalesOrderShipmentAllocationSerializer


class SalesOrderAllocationFilter(FilterSet):
    """Custom filterset for the SalesOrderAllocationList endpoint."""

    class Meta:
        """Metaclass options."""

        model = models.SalesOrderAllocation
        fields = ['shipment', 'line', 'item']

    order = rest_filters.ModelChoiceFilter(
        queryset=models.SalesOrder.objects.all(),
        field_name='line__order',
        label=_('Order'),
    )

    include_variants = rest_filters.BooleanFilter(
        label=_('Include Variants'), method='filter_include_variants'
    )

    def filter_include_variants(self, queryset, name, value):
        """Filter by whether or not to include variants of the selected part.

        Note:
        - This filter does nothing by itself, and requires the 'part' filter to be set.
        - Refer to the 'filter_part' method for more information.
        """
        return queryset

    part = rest_filters.ModelChoiceFilter(
        queryset=Part.objects.all(), method='filter_part', label=_('Part')
    )

    @extend_schema_field(rest_framework.serializers.IntegerField(help_text=_('Part')))
    def filter_part(self, queryset, name, part):
        """Filter by the 'part' attribute.

        Note:
        - If "include_variants" is True, include all variants of the selected part
        - Otherwise, just filter by the selected part
        """
        include_variants = str2bool(self.data.get('include_variants', False))

        if include_variants:
            parts = part.get_descendants(include_self=True)
            return queryset.filter(item__part__in=parts)
        else:
            return queryset.filter(item__part=part)

    outstanding = rest_filters.BooleanFilter(
        label=_('Outstanding'), method='filter_outstanding'
    )

    def filter_outstanding(self, queryset, name, value):
        """Filter by "outstanding" status (boolean)."""
        if str2bool(value):
            return queryset.filter(
                line__order__status__in=SalesOrderStatusGroups.OPEN,
                shipment__shipment_date=None,
            )
        return queryset.exclude(
            shipment__shipment_date=None,
            line__order__status__in=SalesOrderStatusGroups.OPEN,
        )

    assigned_to_shipment = rest_filters.BooleanFilter(
        label=_('Has Shipment'), method='filter_assigned_to_shipment'
    )

    def filter_assigned_to_shipment(self, queryset, name, value):
        """Filter by whether or not the allocation has been assigned to a shipment."""
        if str2bool(value):
            return queryset.exclude(shipment=None)
        return queryset.filter(shipment=None)

    location = rest_filters.ModelChoiceFilter(
        queryset=stock_models.StockLocation.objects.all(),
        label=_('Location'),
        method='filter_location',
    )

    @extend_schema_field(
        rest_framework.serializers.IntegerField(help_text=_('Location'))
    )
    def filter_location(self, queryset, name, location):
        """Filter by the location of the allocated StockItem."""
        locations = location.get_descendants(include_self=True)
        return queryset.filter(item__location__in=locations)


class SalesOrderAllocationMixin:
    """Mixin class for SalesOrderAllocation endpoints."""

    queryset = models.SalesOrderAllocation.objects.all()
    serializer_class = serializers.SalesOrderAllocationSerializer

    def get_queryset(self, *args, **kwargs):
        """Annotate the queryset for this endpoint."""
        queryset = super().get_queryset(*args, **kwargs)

        queryset = queryset.prefetch_related(
            'item',
            'item__sales_order',
            'item__part',
            'line__part',
            'item__location',
            'line__order',
            'line__order__responsible',
            'line__order__project_code',
            'line__order__project_code__responsible',
            'shipment',
            'shipment__order',
            'shipment__checked_by',
        ).select_related('line__part__pricing_data', 'item__part__pricing_data')

        return queryset


class SalesOrderAllocationOutputOptions(OutputConfiguration):
    """Output options for the SalesOrderAllocation endpoint."""

    OPTIONS = [
        InvenTreeOutputOption('part_detail'),
        InvenTreeOutputOption('item_detail'),
        InvenTreeOutputOption('order_detail'),
        InvenTreeOutputOption('location_detail'),
        InvenTreeOutputOption('customer_detail'),
    ]


class SalesOrderAllocationList(
    SalesOrderAllocationMixin, BulkUpdateMixin, OutputOptionsMixin, ListAPI
):
    """API endpoint for listing SalesOrderAllocation objects."""

    filterset_class = SalesOrderAllocationFilter
    filter_backends = SEARCH_ORDER_FILTER
    output_options = SalesOrderAllocationOutputOptions

    ordering_fields = [
        'quantity',
        'part',
        'serial',
        'IPN',
        'batch',
        'location',
        'order',
        'shipment_date',
    ]

    ordering_field_aliases = {
        'IPN': 'item__part__IPN',
        'part': 'item__part__name',
        'serial': ['item__serial_int', 'item__serial'],
        'batch': 'item__batch',
        'location': 'item__location__name',
        'order': 'line__order__reference',
        'shipment_date': 'shipment__shipment_date',
    }

    search_fields = {
        'item__part__name',
        'item__part__IPN',
        'item__serial',
        'item__batch',
    }


class SalesOrderAllocationDetail(SalesOrderAllocationMixin, RetrieveUpdateDestroyAPI):
    """API endpoint for detail view of a SalesOrderAllocation object."""


class SalesOrderShipmentFilter(FilterSet):
    """Custom filterset for the SalesOrderShipmentList endpoint."""

    class Meta:
        """Metaclass options."""

        model = models.SalesOrderShipment
        fields = ['order']

    checked = rest_filters.BooleanFilter(label='checked', method='filter_checked')

    def filter_checked(self, queryset, name, value):
        """Filter SalesOrderShipment list by 'checked' status (boolean)."""
        if str2bool(value):
            return queryset.exclude(checked_by=None)
        return queryset.filter(checked_by=None)

    shipped = rest_filters.BooleanFilter(label='shipped', method='filter_shipped')

    def filter_shipped(self, queryset, name, value):
        """Filter SalesOrder list by 'shipped' status (boolean)."""
        if str2bool(value):
            return queryset.exclude(shipment_date=None)
        return queryset.filter(shipment_date=None)

    delivered = rest_filters.BooleanFilter(label='delivered', method='filter_delivered')

    def filter_delivered(self, queryset, name, value):
        """Filter SalesOrder list by 'delivered' status (boolean)."""
        if str2bool(value):
            return queryset.exclude(delivery_date=None)
        return queryset.filter(delivery_date=None)

    order_outstanding = rest_filters.BooleanFilter(
        label=_('Order Outstanding'), method='filter_order_outstanding'
    )

    def filter_order_outstanding(self, queryset, name, value):
        """Filter by whether the order is 'outstanding' or not."""
        if str2bool(value):
            return queryset.filter(order__status__in=SalesOrderStatusGroups.OPEN)
        return queryset.exclude(order__status__in=SalesOrderStatusGroups.OPEN)

    order_status = rest_filters.NumberFilter(
        label=_('Order Status'), method='filter_order_status'
    )

    def filter_order_status(self, queryset, name, value):
        """Filter by linked SalesOrder status."""
        q1 = Q(order__status=value, order__status_custom_key__isnull=True)
        q2 = Q(order__status_custom_key=value)

        return queryset.filter(q1 | q2).distinct()


class SalesOrderShipmentMixin:
    """Mixin class for SalesOrderShipment endpoints."""

    queryset = models.SalesOrderShipment.objects.all()
    serializer_class = serializers.SalesOrderShipmentSerializer

    def get_queryset(self, *args, **kwargs):
        """Return annotated queryset for this endpoint."""
        queryset = super().get_queryset(*args, **kwargs)

        queryset = serializers.SalesOrderShipmentSerializer.annotate_queryset(queryset)

        return queryset


class SalesOrderShipmentList(SalesOrderShipmentMixin, ListCreateAPI):
    """API list endpoint for SalesOrderShipment model."""

    filterset_class = SalesOrderShipmentFilter
    filter_backends = SEARCH_ORDER_FILTER
    ordering_fields = ['reference', 'delivery_date', 'shipment_date', 'allocated_items']

    search_fields = [
        'order__reference',
        'reference',
        'tracking_number',
        'invoice_number',
    ]


class SalesOrderShipmentDetail(SalesOrderShipmentMixin, RetrieveUpdateDestroyAPI):
    """API detail endpoint for SalesOrderShipment model."""


class SalesOrderShipmentComplete(CreateAPI):
    """API endpoint for completing (shipping) a SalesOrderShipment."""

    queryset = models.SalesOrderShipment.objects.all()
    serializer_class = serializers.SalesOrderShipmentCompleteSerializer

    def get_shipment(self):
        """Return the shipment associated with this endpoint."""
        try:
            shipment = models.SalesOrderShipment.objects.get(
                pk=self.kwargs.get('pk', None)
            )
        except (ValueError, models.SalesOrderShipment.DoesNotExist):
            raise NotFound(detail=_('Shipment not found'))

        return shipment

    def get_serializer_context(self):
        """Pass the request object to the serializer."""
        ctx = super().get_serializer_context()
        ctx['request'] = self.request
        ctx['shipment'] = self.get_shipment()

        return ctx

    @extend_schema(responses={200: common.serializers.TaskDetailSerializer})
    def post(self, request, *args, **kwargs):
        """Override the post method to handle shipment completion."""
        shipment = self.get_shipment()

        serializer = self.get_serializer(shipment, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        task_id = shipment.complete_shipment(
            request.user,
            tracking_number=data.get('tracking_number', shipment.tracking_number),
            invoice_number=data.get('invoice_number', shipment.invoice_number),
            link=data.get('link', shipment.link),
            shipment_date=data.get('shipment_date', None) or current_date(),
            delivery_date=data.get('delivery_date', shipment.delivery_date),
        )

        response = common.serializers.TaskDetailSerializer.from_task(task_id).data
        return Response(response, status=response['http_status'])


class ReturnOrderFilter(OrderFilter):
    """Custom API filters for the ReturnOrderList endpoint."""

    class Meta:
        """Metaclass options."""

        model = models.ReturnOrder
        fields = ['customer']

    include_variants = rest_filters.BooleanFilter(
        label=_('Include Variants'), method='filter_include_variants'
    )

    def filter_include_variants(self, queryset, name, value):
        """Filter by whether or not to include variants of the selected part.

        Note:
        - This filter does nothing by itself, and requires the 'part' filter to be set.
        - Refer to the 'filter_part' method for more information.
        """
        return queryset

    part = rest_filters.ModelChoiceFilter(
        queryset=Part.objects.all(), field_name='part', method='filter_part'
    )

    @extend_schema_field(OpenApiTypes.INT)
    def filter_part(self, queryset, name, part):
        """Filter by selected 'part'.

        Note:
        - If 'include_variants' is set to True, then all variants of the selected part will be included.
        - Otherwise, just filter by the selected part.
        """
        include_variants = str2bool(self.data.get('include_variants', False))

        if include_variants:
            parts = part.get_descendants(include_self=True)
        else:
            parts = Part.objects.filter(pk=part.pk)

        # Now that we have a queryset of parts, find all the matching return orders
        line_items = models.ReturnOrderLineItem.objects.filter(item__part__in=parts)

        # Generate a list of ID values for the matching return orders
        return_orders = line_items.values_list('order', flat=True).distinct()

        # Now we have a list of matching IDs, filter the queryset
        return queryset.filter(pk__in=return_orders)

    completed_before = InvenTreeDateFilter(
        label=_('Completed Before'), field_name='complete_date', lookup_expr='lt'
    )

    completed_after = InvenTreeDateFilter(
        label=_('Completed After'), field_name='complete_date', lookup_expr='gt'
    )


class ReturnOrderMixin(SerializerContextMixin):
    """Mixin class for ReturnOrder endpoints."""

    queryset = models.ReturnOrder.objects.all()
    serializer_class = serializers.ReturnOrderSerializer

    def get_queryset(self, *args, **kwargs):
        """Return annotated queryset for this endpoint."""
        queryset = super().get_queryset(*args, **kwargs)
        queryset = serializers.ReturnOrderSerializer.annotate_queryset(queryset)
        queryset = queryset.prefetch_related(
            'contact', 'created_by', 'customer', 'responsible'
        )

        return queryset


class ReturnOrderOutputOptions(OutputConfiguration):
    """Output options for the ReturnOrder endpoint."""

    OPTIONS = [InvenTreeOutputOption(flag='customer_detail')]


class ReturnOrderList(
    ReturnOrderMixin,
    OrderCreateMixin,
    DataExportViewMixin,
    OutputOptionsMixin,
    ParameterListMixin,
    ListCreateAPI,
):
    """API endpoint for accessing a list of ReturnOrder objects."""

    filterset_class = ReturnOrderFilter
    filter_backends = SEARCH_ORDER_FILTER

    output_options = ReturnOrderOutputOptions

    ordering_field_aliases = {
        'reference': ['reference_int', 'reference'],
        'project_code': ['project_code__code'],
    }

    ordering_fields = [
        'creation_date',
        'created_by',
        'reference',
        'customer__name',
        'customer_reference',
        'line_items',
        'status',
        'start_date',
        'target_date',
        'complete_date',
        'project_code',
        'updated_at',
    ]

    search_fields = [
        'customer__name',
        'reference',
        'description',
        'customer_reference',
        'project_code__code',
    ]

    ordering = '-reference'


class ReturnOrderDetail(ReturnOrderMixin, OutputOptionsMixin, RetrieveUpdateDestroyAPI):
    """API endpoint for detail view of a single ReturnOrder object."""

    output_options = ReturnOrderOutputOptions


class ReturnOrderContextMixin:
    """Simple mixin class to add a ReturnOrder to the serializer context."""

    queryset = models.ReturnOrder.objects.all()

    def get_serializer_context(self):
        """Add the PurchaseOrder object to the serializer context."""
        context = super().get_serializer_context()

        # Pass the ReturnOrder instance through to the serializer for validation
        try:
            context['order'] = models.ReturnOrder.objects.get(
                pk=self.kwargs.get('pk', None)
            )
        except Exception:
            pass

        context['request'] = self.request

        return context


class ReturnOrderCancel(ReturnOrderContextMixin, CreateAPI):
    """API endpoint to cancel a ReturnOrder."""

    serializer_class = serializers.ReturnOrderCancelSerializer


class ReturnOrderHold(ReturnOrderContextMixin, CreateAPI):
    """API endpoint to hold a ReturnOrder."""

    serializer_class = serializers.ReturnOrderHoldSerializer


class ReturnOrderComplete(ReturnOrderContextMixin, CreateAPI):
    """API endpoint to complete a ReturnOrder."""

    serializer_class = serializers.ReturnOrderCompleteSerializer


class ReturnOrderIssue(ReturnOrderContextMixin, CreateAPI):
    """API endpoint to issue (place) a ReturnOrder."""

    serializer_class = serializers.ReturnOrderIssueSerializer


class ReturnOrderReceive(ReturnOrderContextMixin, CreateAPI):
    """API endpoint to receive items against a ReturnOrder."""

    queryset = models.ReturnOrder.objects.none()
    serializer_class = serializers.ReturnOrderReceiveSerializer


class ReturnOrderLineItemFilter(LineItemFilter):
    """Custom filters for the ReturnOrderLineItemList endpoint."""

    class Meta:
        """Metaclass options."""

        price_field = 'price'
        model = models.ReturnOrderLineItem
        fields = ['order', 'item']

    outcome = rest_filters.NumberFilter(label='outcome')

    received = rest_filters.BooleanFilter(label='received', method='filter_received')

    def filter_received(self, queryset, name, value):
        """Filter by 'received' field."""
        if str2bool(value):
            return queryset.exclude(received_date=None)
        return queryset.filter(received_date=None)


class ReturnOrderLineItemMixin(SerializerContextMixin):
    """Mixin class for ReturnOrderLineItem endpoints."""

    queryset = models.ReturnOrderLineItem.objects.all()
    serializer_class = serializers.ReturnOrderLineItemSerializer

    def get_queryset(self, *args, **kwargs):
        """Return annotated queryset for this endpoint."""
        queryset = super().get_queryset(*args, **kwargs)

        queryset = queryset.prefetch_related('order', 'item', 'item__part')

        return queryset


class ReturnOrderLineItemOutputOptions(OutputConfiguration):
    """Output options for the ReturnOrderLineItem endpoint."""

    OPTIONS = [
        InvenTreeOutputOption('part_detail'),
        InvenTreeOutputOption('item_detail', default=True),
        InvenTreeOutputOption('order_detail'),
    ]


class ReturnOrderLineItemList(
    ReturnOrderLineItemMixin, DataExportViewMixin, OutputOptionsMixin, ListCreateAPI
):
    """API endpoint for accessing a list of ReturnOrderLineItemList objects."""

    filterset_class = ReturnOrderLineItemFilter

    filter_backends = SEARCH_ORDER_FILTER

    output_options = ReturnOrderLineItemOutputOptions

    ordering_fields = [
        'part',
        'IPN',
        'stock',
        'reference',
        'target_date',
        'received_date',
        'line',
    ]

    ordering_field_aliases = {
        'line': ['line_int', 'line', 'item__part__name'],
        'part': 'item__part__name',
        'IPN': 'item__part__IPN',
        'stock': ['item__quantity', 'item__serial_int', 'item__serial'],
    }

    search_fields = [
        'item__serial',
        'item__part__name',
        'item__part__description',
        'reference',
    ]


class ReturnOrderLineItemDetail(
    ReturnOrderLineItemMixin, OutputOptionsMixin, RetrieveUpdateDestroyAPI
):
    """API endpoint for detail view of a ReturnOrderLineItem object."""

    output_options = ReturnOrderLineItemOutputOptions


class ReturnOrderExtraLineList(GeneralExtraLineList, OutputOptionsMixin, ListCreateAPI):
    """API endpoint for accessing a list of ReturnOrderExtraLine objects."""

    queryset = models.ReturnOrderExtraLine.objects.all()
    serializer_class = serializers.ReturnOrderExtraLineSerializer


class ReturnOrderExtraLineDetail(RetrieveUpdateDestroyAPI):
    """API endpoint for detail view of a ReturnOrderExtraLine object."""

    queryset = models.ReturnOrderExtraLine.objects.all()
    serializer_class = serializers.ReturnOrderExtraLineSerializer


class OrderCalendarExport(ICalFeed):
    """Calendar export for Purchase/Sales Orders.

    Optional parameters:
    - include_completed: true/false
        whether or not to show completed orders. Defaults to false
    """

    instance_url = get_base_url()

    instance_url = instance_url.replace('http://', '').replace('https://', '')
    timezone = settings.TIME_ZONE
    file_name = 'calendar.ics'

    def __call__(self, request, *args, **kwargs):
        """Overload call in order to check for authentication.

        This is required to force Django to look for the authentication,
        otherwise login request with Basic auth via curl or similar are ignored,
        and login via a calendar client will not work.

        See:
        https://stackoverflow.com/questions/3817694/django-rss-feed-authentication
        https://stackoverflow.com/questions/152248/can-i-use-http-basic-authentication-with-django
        https://www.djangosnippets.org/snippets/243/
        """
        import base64

        if request.user.is_authenticated:
            # Authenticated on first try - maybe normal browser call?
            return super().__call__(request, *args, **kwargs)

        # No login yet - check in headers
        if 'authorization' in request.headers:
            auth = request.headers['authorization'].split()
            if len(auth) == 2:
                # NOTE: We are only support basic authentication for now.
                #
                if auth[0].lower() == 'basic':
                    uname, passwd = base64.b64decode(auth[1]).decode('ascii').split(':')
                    user = authenticate(username=uname, password=passwd)
                    if user is not None and user.is_active:
                        login(request, user)
                        request.user = user

        # Check again
        if request.user.is_authenticated:
            # Authenticated after second try
            return super().__call__(request, *args, **kwargs)

        # Still nothing - return Unauth. header with info on how to authenticate
        # Information is needed by client, eg Thunderbird
        response = JsonResponse({
            'detail': 'Authentication credentials were not provided.'
        })
        response['WWW-Authenticate'] = 'Basic realm="api"'
        response.status_code = 401
        return response

    def get_object(self, request, *args, **kwargs):
        """This is where settings from the URL etc will be obtained."""
        # Help:
        # https://django.readthedocs.io/en/stable/ref/contrib/syndication.html

        obj = {}
        obj['ordertype'] = kwargs['ordertype']
        obj['include_completed'] = bool(request.GET.get('include_completed', False))

        return obj

    def title(self, obj):
        """Return calendar title."""
        if obj['ordertype'] == 'purchase-order':
            ordertype_title = _('Purchase Order')
        elif obj['ordertype'] == 'sales-order':
            ordertype_title = _('Sales Order')
        elif obj['ordertype'] == 'return-order':
            ordertype_title = _('Return Order')
        else:
            ordertype_title = _('Unknown')

        company_name = common.settings.get_global_setting('INVENTREE_COMPANY_NAME')

        return f'{company_name} {ordertype_title}'

    def product_id(self, obj):
        """Return calendar product id."""
        return f'//{self.instance_url}//{self.title(obj)}//EN'

    def items(self, obj):
        """Return a list of Orders.

        Filters:
        - Only return those which have a target_date set
        - Only return incomplete orders, unless include_completed is set to True
        """
        if obj['ordertype'] == 'purchase-order':
            if obj['include_completed'] is False:
                # Do not include completed orders from list in this case
                # Completed status = 30
                outlist = models.PurchaseOrder.objects.filter(
                    target_date__isnull=False
                ).filter(status__lt=PurchaseOrderStatus.COMPLETE.value)
            else:
                outlist = models.PurchaseOrder.objects.filter(target_date__isnull=False)
        elif obj['ordertype'] == 'sales-order':
            if obj['include_completed'] is False:
                # Do not include completed (=shipped) orders from list in this case
                # Shipped status = 20
                outlist = models.SalesOrder.objects.filter(
                    target_date__isnull=False
                ).filter(status__lt=SalesOrderStatus.SHIPPED.value)
            else:
                outlist = models.SalesOrder.objects.filter(target_date__isnull=False)
        elif obj['ordertype'] == 'return-order':
            if obj['include_completed'] is False:
                # Do not include completed orders from list in this case
                # Complete status = 30
                outlist = models.ReturnOrder.objects.filter(
                    target_date__isnull=False
                ).filter(status__lt=ReturnOrderStatus.COMPLETE.value)
            else:
                outlist = models.ReturnOrder.objects.filter(target_date__isnull=False)
        else:
            outlist = []

        return outlist

    def item_title(self, item):
        """Set the event title to the order reference."""
        return f'{item.reference}'

    def item_description(self, item):
        """Set the event description."""
        return f'Company: {item.company.name}\nStatus: {item.get_status_display()}\nDescription: {item.description}'

    def item_start_datetime(self, item):
        """Set event start to target date. Goal is all-day event."""
        return item.target_date

    def item_end_datetime(self, item):
        """Set event end to target date. Goal is all-day event."""
        return item.target_date

    def item_created(self, item):
        """Use creation date of PO as creation date of event."""
        return item.creation_date

    def item_class(self, item):
        """Set item class to PUBLIC."""
        return 'PUBLIC'

    def item_guid(self, item):
        """Return globally unique UID for event."""
        return f'po_{item.pk}_{item.reference.replace(" ", "-")}@{self.instance_url}'

    def item_link(self, item):
        """Set the item link."""
        return construct_absolute_url(item.get_absolute_url())


# POS Sales Webhook Orchestration


class PosSalesOrchestrator:
    """Runs the sales-order workflow using InvenTree models and serializers.

    Orchestrates the complete POS sale workflow from receipt data to completed shipment.
    """

    def __init__(self, user: User):
        """Initialize the orchestrator with a service user."""
        self.user = user
        self.request_context = {'request': _FakeRequest(user)}

    def process_sale(self, receipt_id: str, location_id: str) -> models.SalesOrder:
        """End-to-end POS sale processing.

        Workflow (InvenTree-recommended order):
        fetch receipt → create order → lines → issue → shipment → allocate → check →
        complete shipment (async) → ship order → complete order.
        """
        from django.db import transaction

        line_specs = self._parse_receipt_lines(receipt_id)
        customer = self._get_or_create_location_customer(location_id)
        stock_location = self._resolve_stock_location(location_id)

        sales_order = self._get_or_create_sales_order(receipt_id, customer)

        if sales_order.lines.exists():
            logger.info(
                'POS sale already processed',
                receipt_id=receipt_id,
                sales_order_pk=sales_order.pk,
            )
            return sales_order

        shipment: models.SalesOrderShipment

        # DB steps that must commit before the background shipment task runs.
        with transaction.atomic():
            self._create_line_items(sales_order, line_specs)
            self._issue_order(sales_order)
            shipment = self._create_shipment(sales_order, receipt_id)
            self._allocate_stock(sales_order, shipment, line_specs, stock_location)
            self._check_shipment(shipment)

        task_id = self._complete_shipment(shipment)
        self._wait_for_background_task(task_id)

        self._ship_sales_order(sales_order)
        self._complete_sales_order(sales_order)

        sales_order.refresh_from_db()
        return sales_order

    def _get_or_create_location_customer(
        self, location_id: str
    ) -> company_models.Company:
        """Each POS location maps to a dedicated InvenTree customer company."""
        prefix = 'POS Location'  # Can be made configurable
        name = f'{prefix} {location_id}'

        customer = company_models.Company.objects.filter(
            name=name, is_customer=True
        ).first()

        if customer:
            return customer

        customer = company_models.Company.objects.create(
            name=name,
            description=f'Auto-created for POS location_id={location_id}',
            is_customer=True,
            is_supplier=False,
            active=True,
        )

        logger.info(
            'Created POS customer', location_id=location_id, customer_pk=customer.pk
        )
        return customer

    def _resolve_stock_location(self, location_id: str) -> stock_models.StockLocation:
        """Resolve external location_id to an InvenTree stock location."""
        # Try exact location_id match
        try:
            return stock_models.StockLocation.objects.get(pk=location_id)
        except (stock_models.StockLocation.DoesNotExist, ValueError):
            pass

        # Fallback: match by name
        location = stock_models.StockLocation.objects.filter(name=location_id).first()

        if location:
            return location

        raise ValueError(
            _(
                'No stock location found for location_id=%(loc)s. '
                'Provide a valid StockLocation pk or name.'
            )
            % {'loc': location_id}
        )

    def _get_or_create_sales_order(
        self, receipt_id: str, customer: company_models.Company
    ) -> models.SalesOrder:
        """Idempotent sales order keyed by POS receipt id."""
        reference = f'POS-{receipt_id}'

        existing = models.SalesOrder.objects.filter(reference=reference).first()

        if existing:
            return existing

        return models.SalesOrder.objects.create(
            reference=reference,
            customer=customer,
            description=f'POS receipt {receipt_id}',
            created_by=self.user,
        )

    def _parse_receipt_lines(self, receipt_id: str) -> list[dict[str, Any]]:
        """Fetch and normalize itemized receipt data from the external POS API."""
        endpoint = common.settings.get_global_setting(
            'PA_RECEIPT_API_ENDPOINT', environment_key='PA_RECEIPT_API_ENDPOINT'
        )
        api_key = common.settings.get_global_setting(
            'PA_RECEIPT_API_KEY', environment_key='PA_RECEIPT_API_KEY'
        )

        if not endpoint:
            raise ValueError(
                _(
                    'POS receipt API endpoint is not configured. '
                    'Set PA_RECEIPT_API_ENDPOINT in the environment or database.'
                )
            )

        headers = {'Accept': 'application/json', 'Authorization': f'Bearer {api_key}'}

        try:
            response = requests.get(
                endpoint, headers=headers, params={'receipt_id': receipt_id}, timeout=30
            )
            response.raise_for_status()
        except requests.exceptions.Timeout as exc:
            raise ValueError(
                _('POS receipt API timed out for receipt %(id)s') % {'id': receipt_id}
            ) from exc
        except requests.exceptions.HTTPError:
            raise ValueError(
                _('POS receipt API returned %(status)s for receipt %(id)s')
                % {'status': response.status_code, 'id': receipt_id}
            )
        except requests.exceptions.ConnectionError as exc:
            raise ValueError(
                _('POS receipt API is unreachable for receipt %(id)s')
                % {'id': receipt_id}
            ) from exc

        try:
            data = response.json()
        except ValueError as exc:
            raise ValueError(
                _('POS receipt API returned invalid JSON for receipt %(id)s')
                % {'id': receipt_id}
            ) from exc

        lines = data.get('lines') or data.get('items') or data.get('line_items')

        if not lines:
            raise ValueError(
                _('Receipt %(id)s contains no line items in the POS response')
                % {'id': receipt_id}
            )

        normalized: list[dict[str, Any]] = []
        for entry in lines:
            if not isinstance(entry, dict):
                continue

            quantity = entry.get('quantity') or entry.get('qty') or 0

            normalized.append({
                'part_id': entry.get('part_id') or entry.get('partId'),
                'sku': entry.get('sku') or entry.get('ipn') or entry.get('part_number'),
                'barcode': entry.get('barcode') or entry.get('barcode_hash'),
                'quantity': Decimal(str(quantity)),
            })

        if not normalized:
            raise ValueError(
                _('No usable line items in receipt %(id)s') % {'id': receipt_id}
            )

        logger.info(
            'Fetched POS receipt lines',
            receipt_id=receipt_id,
            line_count=len(normalized),
        )

        return normalized

    def _create_line_items(
        self, sales_order: models.SalesOrder, line_specs: list[dict[str, Any]]
    ) -> list[models.SalesOrderLineItem]:
        """Create sales order line items from receipt lines."""
        created: list[models.SalesOrderLineItem] = []

        for spec in line_specs:
            part = self._resolve_part(spec)

            if not part.salable:
                raise ValueError(
                    _('Part %(part)s is not salable') % {'part': part.name}
                )

            line = models.SalesOrderLineItem.objects.create(
                order=sales_order,
                part=part,
                quantity=spec['quantity'],
                reference=spec.get('sku') or part.IPN,
            )
            created.append(line)

        return created

    def _resolve_part(self, spec: dict[str, Any]) -> Part:
        """Resolve a receipt line to an InvenTree Part."""
        if spec.get('part_id'):
            return Part.objects.get(pk=spec['part_id'])

        if spec.get('sku'):
            match = Part.objects.filter(IPN=spec['sku']).first()

            if match:
                return match

        if spec.get('barcode'):
            item = stock_models.StockItem.lookup_barcode(spec['barcode'])

            if item:
                return item.part

        raise ValueError(
            _('Could not resolve part for line: %(line)s') % {'line': spec}
        )

    def _issue_order(self, sales_order: models.SalesOrder) -> None:
        """Issue the sales order (PENDING → IN_PROGRESS)."""
        if not sales_order.can_issue:
            return

        serializer = serializers.SalesOrderIssueSerializer(
            data={}, context={**self.request_context, 'order': sales_order}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

    def _create_shipment(
        self, sales_order: models.SalesOrder, receipt_id: str
    ) -> models.SalesOrderShipment:
        """Create a single shipment for this POS sale."""
        return models.SalesOrderShipment.objects.create(
            order=sales_order, reference=f'POS-SHP-{receipt_id}'
        )

    def _allocate_stock(
        self,
        sales_order: models.SalesOrder,
        shipment: models.SalesOrderShipment,
        line_specs: list[dict[str, Any]],
        stock_location: stock_models.StockLocation,
    ) -> None:
        """Allocate stock from the configured location for each line."""
        allocation_items = []

        locations = stock_location.get_descendants(include_self=True)

        for spec in line_specs:
            part = self._resolve_part(spec)
            line = sales_order.lines.filter(part=part).first()

            if not line:
                raise ValueError(
                    _('No sales order line for part %(part)s') % {'part': part.pk}
                )

            remaining = spec['quantity']

            stock_qs = stock_models.StockItem.objects.filter(
                part=part, location__in=locations
            ).order_by('pk')

            for stock_item in stock_qs:
                if remaining <= 0:
                    break

                available = stock_item.unallocated_quantity()

                if available <= 0:
                    continue

                take = min(remaining, available)

                allocation_items.append({
                    'line_item': line,
                    'stock_item': stock_item,
                    'quantity': take,
                })

                remaining -= take

            if remaining > 0:
                raise ValueError(
                    _(
                        'Insufficient stock for part %(part)s at location %(loc)s '
                        '(short by %(qty)s)'
                    )
                    % {'part': part.name, 'loc': stock_location.name, 'qty': remaining}
                )

        serializer_obj = serializers.SalesOrderShipmentAllocationSerializer(
            data={'items': allocation_items, 'shipment': shipment.pk},
            context={**self.request_context, 'order': sales_order},
        )
        serializer_obj.is_valid(raise_exception=True)
        serializer_obj.save()

    def _check_shipment(self, shipment: models.SalesOrderShipment) -> None:
        """Mark shipment as checked (required when SALESORDER_SHIPMENT_REQUIRES_CHECK)."""
        shipment.checked_by = self.user
        shipment.save(update_fields=['checked_by'])

    def _complete_shipment(self, shipment: models.SalesOrderShipment) -> str:
        """Complete shipment; returns background task id."""
        shipment.check_can_complete(raise_error=True)
        return shipment.complete_shipment(self.user)

    def _wait_for_background_task(
        self, task_id: str | bool | None, timeout_seconds: int = 120
    ) -> None:
        """Wait for django-q shipment completion task."""
        import time

        import django_q.models

        if task_id is None or isinstance(task_id, bool):
            return

        deadline = time.time() + timeout_seconds

        while time.time() < deadline:
            if django_q.models.Success.objects.filter(id=task_id).exists():
                return

            if django_q.models.Failure.objects.filter(id=task_id).exists():
                raise RuntimeError(
                    _('Background task %(task)s failed') % {'task': task_id}
                )

            time.sleep(1)

        raise TimeoutError(
            _('Timed out waiting for background task %(task)s') % {'task': task_id}
        )

    def _ship_sales_order(self, sales_order: models.SalesOrder) -> None:
        """Mark sales order as shipped (InvenTree 'Complete Order' UI action)."""
        sales_order.refresh_from_db()

        if sales_order.status in SalesOrderStatusGroups.COMPLETE:
            return

        serializer_obj = serializers.SalesOrderCompleteSerializer(
            data={'accept_incomplete': False},
            context={**self.request_context, 'order': sales_order},
        )
        serializer_obj.is_valid(raise_exception=True)
        serializer_obj.save()

    def _complete_sales_order(self, sales_order: models.SalesOrder) -> None:
        """Transition order to COMPLETE status when still open after shipping."""
        sales_order.refresh_from_db()

        if sales_order.status == SalesOrderStatus.COMPLETE.value:
            return

        if sales_order.status == SalesOrderStatus.SHIPPED.value:
            sales_order.complete_order(self.user)


class _FakeRequest:
    """Minimal request object for serializer context."""

    def __init__(self, user: User):
        """Initialize with a user."""
        self.user = user


class PosSalesWebhook(CreateAPI):
    """API endpoint for POS sales webhook.

    Receives POS webhook events and orchestrates the sales order workflow.

    POST /api/sales/pos-webhook/
    """

    queryset = models.SalesOrder.objects.none()
    serializer_class = serializers.PosWebhookInboundSerializer

    def create(self, request, *args, **kwargs):
        """Process incoming POS webhook and orchestrate sales order creation."""
        try:
            receipt_id, location_id = self._parse_inbound_webhook(request.data)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        logger.info(
            'POS webhook received', receipt_id=receipt_id, location_id=location_id
        )

        try:
            user = self._get_service_user()
        except Exception as exc:
            logger.exception('POS service user misconfigured')
            return Response(
                {'detail': str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        try:
            orchestrator = PosSalesOrchestrator(user)
            sales_order = orchestrator.process_sale(receipt_id, location_id)
        except (ValueError, DRFValidationError) as exc:
            logger.warning('POS sale rejected', error=str(exc))
            detail = exc.detail if isinstance(exc, DRFValidationError) else str(exc)
            return Response({'detail': detail}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logger.exception('POS sale failed')
            return Response(
                {'detail': str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        payload = {
            'success': True,
            'receipt_id': receipt_id,
            'location_id': location_id,
            'sales_order_id': sales_order.pk,
            'sales_order_reference': sales_order.reference,
            'message': _('POS sale processed successfully'),
        }

        return Response(payload, status=status.HTTP_201_CREATED)

    @staticmethod
    def _parse_inbound_webhook(data: dict) -> tuple[str, str]:
        """Extract receipt and location identifiers from the inbound webhook body."""
        receipt_id = data.get('receipt_id') or data.get('id')
        location_id = data.get('location_id') or data.get('location')

        if not receipt_id:
            raise ValueError(_('Missing receipt_id in webhook payload'))
        if not location_id:
            raise ValueError(_('Missing location_id in webhook payload'))

        return str(receipt_id), str(location_id)

    @staticmethod
    def _get_service_user() -> User:
        """Return the configured service account (defaults to 'admin')."""
        User = get_user_model()

        try:
            return User.objects.get(username='admin')
        except User.DoesNotExist as exc:
            raise ValueError(_('Service user "admin" does not exist')) from exc


order_api_urls = [
    # API endpoints for purchase orders
    path(
        'po/',
        include([
            # Individual purchase order detail URLs
            path(
                '<int:pk>/',
                include([
                    path(
                        'cancel/', PurchaseOrderCancel.as_view(), name='api-po-cancel'
                    ),
                    path('hold/', PurchaseOrderHold.as_view(), name='api-po-hold'),
                    path(
                        'complete/',
                        PurchaseOrderComplete.as_view(),
                        name='api-po-complete',
                    ),
                    path('issue/', PurchaseOrderIssue.as_view(), name='api-po-issue'),
                    meta_path(models.PurchaseOrder),
                    path(
                        'receive/',
                        PurchaseOrderReceive.as_view(),
                        name='api-po-receive',
                    ),
                    # PurchaseOrder detail API endpoint
                    path('', PurchaseOrderDetail.as_view(), name='api-po-detail'),
                ]),
            ),
            # Purchase order status code information
            path(
                'status/',
                StatusView.as_view(),
                {StatusView.MODEL_REF: PurchaseOrderStatus},
                name='api-po-status-codes',
            ),
            # Purchase order list
            path('', PurchaseOrderList.as_view(), name='api-po-list'),
        ]),
    ),
    # API endpoints for purchase order line items
    path(
        'po-line/',
        include([
            path(
                '<int:pk>/',
                include([
                    meta_path(models.PurchaseOrderLineItem),
                    path(
                        '',
                        PurchaseOrderLineItemDetail.as_view(),
                        name='api-po-line-detail',
                    ),
                ]),
            ),
            path('', PurchaseOrderLineItemList.as_view(), name='api-po-line-list'),
        ]),
    ),
    # API endpoints for purchase order extra line
    path(
        'po-extra-line/',
        include([
            path(
                '<int:pk>/',
                include([
                    meta_path(models.PurchaseOrderExtraLine),
                    path(
                        '',
                        PurchaseOrderExtraLineDetail.as_view(),
                        name='api-po-extra-line-detail',
                    ),
                ]),
            ),
            path(
                '', PurchaseOrderExtraLineList.as_view(), name='api-po-extra-line-list'
            ),
        ]),
    ),
    # API endpoints for sales orders
    path(
        'so/',
        include([
            path(
                'shipment/',
                include([
                    path(
                        '<int:pk>/',
                        include([
                            path(
                                'ship/',
                                SalesOrderShipmentComplete.as_view(),
                                name='api-so-shipment-ship',
                            ),
                            meta_path(models.SalesOrderShipment),
                            path(
                                '',
                                SalesOrderShipmentDetail.as_view(),
                                name='api-so-shipment-detail',
                            ),
                        ]),
                    ),
                    path(
                        '',
                        SalesOrderShipmentList.as_view(),
                        name='api-so-shipment-list',
                    ),
                ]),
            ),
            # Sales order detail view
            path(
                '<int:pk>/',
                include([
                    path(
                        'allocate/',
                        SalesOrderAllocate.as_view(),
                        name='api-so-allocate',
                    ),
                    path(
                        'allocate-serials/',
                        SalesOrderAllocateSerials.as_view(),
                        name='api-so-allocate-serials',
                    ),
                    path('hold/', SalesOrderHold.as_view(), name='api-so-hold'),
                    path('cancel/', SalesOrderCancel.as_view(), name='api-so-cancel'),
                    path('issue/', SalesOrderIssue.as_view(), name='api-so-issue'),
                    path(
                        'complete/',
                        SalesOrderComplete.as_view(),
                        name='api-so-complete',
                    ),
                    meta_path(models.SalesOrder),
                    # SalesOrder detail endpoint
                    path('', SalesOrderDetail.as_view(), name='api-so-detail'),
                ]),
            ),
            # Sales order status code information
            path(
                'status/',
                StatusView.as_view(),
                {StatusView.MODEL_REF: SalesOrderStatus},
                name='api-so-status-codes',
            ),
            # Sales order list view
            path('', SalesOrderList.as_view(), name='api-so-list'),
        ]),
    ),
    # API endpoints for sales order line items
    path(
        'so-line/',
        include([
            path(
                '<int:pk>/',
                include([
                    meta_path(models.SalesOrderLineItem),
                    path(
                        '',
                        SalesOrderLineItemDetail.as_view(),
                        name='api-so-line-detail',
                    ),
                ]),
            ),
            path('', SalesOrderLineItemList.as_view(), name='api-so-line-list'),
        ]),
    ),
    # API endpoints for sales order extra line
    path(
        'so-extra-line/',
        include([
            path(
                '<int:pk>/',
                include([
                    meta_path(models.SalesOrderExtraLine),
                    path(
                        '',
                        SalesOrderExtraLineDetail.as_view(),
                        name='api-so-extra-line-detail',
                    ),
                ]),
            ),
            path('', SalesOrderExtraLineList.as_view(), name='api-so-extra-line-list'),
        ]),
    ),
    # API endpoints for sales order allocations
    path(
        'so-allocation/',
        include([
            path(
                '<int:pk>/',
                SalesOrderAllocationDetail.as_view(),
                name='api-so-allocation-detail',
            ),
            path('', SalesOrderAllocationList.as_view(), name='api-so-allocation-list'),
        ]),
    ),
    # API endpoints for return orders
    path(
        'ro/',
        include([
            # Return Order detail endpoints
            path(
                '<int:pk>/',
                include([
                    path(
                        'cancel/',
                        ReturnOrderCancel.as_view(),
                        name='api-return-order-cancel',
                    ),
                    path('hold/', ReturnOrderHold.as_view(), name='api-ro-hold'),
                    path(
                        'complete/',
                        ReturnOrderComplete.as_view(),
                        name='api-return-order-complete',
                    ),
                    path(
                        'issue/',
                        ReturnOrderIssue.as_view(),
                        name='api-return-order-issue',
                    ),
                    path(
                        'receive/',
                        ReturnOrderReceive.as_view(),
                        name='api-return-order-receive',
                    ),
                    meta_path(models.ReturnOrder),
                    path(
                        '', ReturnOrderDetail.as_view(), name='api-return-order-detail'
                    ),
                ]),
            ),
            # Return order status code information
            path(
                'status/',
                StatusView.as_view(),
                {StatusView.MODEL_REF: ReturnOrderStatus},
                name='api-return-order-status-codes',
            ),
            # Return Order list
            path('', ReturnOrderList.as_view(), name='api-return-order-list'),
        ]),
    ),
    # API endpoints for return order lines
    path(
        'ro-line/',
        include([
            path(
                '<int:pk>/',
                include([
                    meta_path(models.ReturnOrderLineItem),
                    path(
                        '',
                        ReturnOrderLineItemDetail.as_view(),
                        name='api-return-order-line-detail',
                    ),
                ]),
            ),
            # Return order line item status code information
            path(
                'status/',
                StatusView.as_view(),
                {StatusView.MODEL_REF: ReturnOrderLineStatus},
                name='api-return-order-line-status-codes',
            ),
            path(
                '', ReturnOrderLineItemList.as_view(), name='api-return-order-line-list'
            ),
        ]),
    ),
    # API endpoints for return order extra line
    path(
        'ro-extra-line/',
        include([
            path(
                '<int:pk>/',
                include([
                    meta_path(models.ReturnOrderExtraLine),
                    path(
                        '',
                        ReturnOrderExtraLineDetail.as_view(),
                        name='api-return-order-extra-line-detail',
                    ),
                ]),
            ),
            path(
                '',
                ReturnOrderExtraLineList.as_view(),
                name='api-return-order-extra-line-list',
            ),
        ]),
    ),
    # API endpoint for POS sales webhook
    path('pos-webhook/', PosSalesWebhook.as_view(), name='api-pos-webhook'),
    # API endpoint for subscribing to ICS calendar of purchase/sales/return orders
    re_path(
        r'^calendar/(?P<ordertype>purchase-order|sales-order|return-order)/calendar.ics',
        OrderCalendarExport(),
        name='api-po-so-calendar',
    ),
]
