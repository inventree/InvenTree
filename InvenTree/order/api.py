"""JSON API for the Order app."""

from django.contrib.auth import authenticate, login
from django.db import transaction
from django.db.models import F, Q
from django.http.response import JsonResponse
from django.urls import include, path, re_path
from django.utils.translation import gettext_lazy as _

from django_filters import rest_framework as rest_filters
from django_ical.views import ICalFeed
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

import common.models as common_models
from common.settings import settings
from company.models import SupplierPart
from generic.states.api import StatusView
from InvenTree.api import (APIDownloadMixin, AttachmentMixin,
                           ListCreateDestroyAPIView, MetadataView)
from InvenTree.filters import SEARCH_ORDER_FILTER, SEARCH_ORDER_FILTER_ALIAS
from InvenTree.helpers import DownloadFile, str2bool
from InvenTree.helpers_model import construct_absolute_url, get_base_url
from InvenTree.mixins import (CreateAPI, ListAPI, ListCreateAPI,
                              RetrieveUpdateDestroyAPI)
from InvenTree.status_codes import (PurchaseOrderStatus,
                                    PurchaseOrderStatusGroups,
                                    ReturnOrderLineStatus, ReturnOrderStatus,
                                    SalesOrderStatus, SalesOrderStatusGroups)
from order import models, serializers
from order.admin import (PurchaseOrderExtraLineResource,
                         PurchaseOrderLineItemResource, PurchaseOrderResource,
                         ReturnOrderResource, SalesOrderExtraLineResource,
                         SalesOrderLineItemResource, SalesOrderResource)
from part.models import Part
from users.models import Owner


class GeneralExtraLineList(APIDownloadMixin):
    """General template for ExtraLine API classes."""

    def get_serializer(self, *args, **kwargs):
        """Return the serializer instance for this endpoint"""
        try:
            params = self.request.query_params3

            kwargs['order_detail'] = str2bool(params.get('order_detail', False))
        except AttributeError:
            pass

        kwargs['context'] = self.get_serializer_context()

        return self.serializer_class(*args, **kwargs)

    def get_queryset(self, *args, **kwargs):
        """Return the annotated queryset for this endpoint"""
        queryset = super().get_queryset(*args, **kwargs)

        queryset = queryset.prefetch_related(
            'order',
        )

        return queryset

    filter_backends = SEARCH_ORDER_FILTER

    ordering_fields = [
        'quantity',
        'note',
        'reference',
    ]

    search_fields = [
        'quantity',
        'note',
        'reference',
        'description',
    ]

    filterset_fields = [
        'order',
    ]


class OrderFilter(rest_filters.FilterSet):
    """Base class for custom API filters for the OrderList endpoint."""

    # Filter against order status
    status = rest_filters.NumberFilter(label="Order Status", method='filter_status')

    def filter_status(self, queryset, name, value):
        """Filter by integer status code"""
        return queryset.filter(status=value)

    # Exact match for reference
    reference = rest_filters.CharFilter(
        label='Filter by exact reference',
        field_name='reference',
        lookup_expr="iexact"
    )

    assigned_to_me = rest_filters.BooleanFilter(label='assigned_to_me', method='filter_assigned_to_me')

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

    outstanding = rest_filters.BooleanFilter(label='outstanding', method='filter_outstanding')

    def filter_outstanding(self, queryset, name, value):
        """Generic filter for determining if an order is 'outstanding'"""
        if str2bool(value):
            return queryset.filter(status__in=self.Meta.model.get_status_class().OPEN)
        return queryset.exclude(status__in=self.Meta.model.get_status_class().OPEN)

    project_code = rest_filters.ModelChoiceFilter(
        queryset=common_models.ProjectCode.objects.all(),
        field_name='project_code'
    )

    has_project_code = rest_filters.BooleanFilter(label='has_project_code', method='filter_has_project_code')

    def filter_has_project_code(self, queryset, name, value):
        """Filter by whether or not the order has a project code"""
        if str2bool(value):
            return queryset.exclude(project_code=None)
        return queryset.filter(project_code=None)


class LineItemFilter(rest_filters.FilterSet):
    """Base class for custom API filters for order line item list(s)"""

    # Filter by order status
    order_status = rest_filters.NumberFilter(label='order_status', field_name='order__status')

    has_pricing = rest_filters.BooleanFilter(label="Has Pricing", method='filter_has_pricing')

    def filter_has_pricing(self, queryset, name, value):
        """Filter by whether or not the line item has pricing information"""
        filters = {self.Meta.price_field: None}

        if str2bool(value):
            return queryset.exclude(**filters)
        return queryset.filter(**filters)


class PurchaseOrderFilter(OrderFilter):
    """Custom API filters for the PurchaseOrderList endpoint."""

    class Meta:
        """Metaclass options."""

        model = models.PurchaseOrder
        fields = [
            'supplier',
        ]


class PurchaseOrderMixin:
    """Mixin class for PurchaseOrder endpoints"""

    queryset = models.PurchaseOrder.objects.all()
    serializer_class = serializers.PurchaseOrderSerializer

    def get_serializer(self, *args, **kwargs):
        """Return the serializer instance for this endpoint"""
        try:
            kwargs['supplier_detail'] = str2bool(self.request.query_params.get('supplier_detail', False))
        except AttributeError:
            pass

        # Ensure the request context is passed through
        kwargs['context'] = self.get_serializer_context()

        return self.serializer_class(*args, **kwargs)

    def get_queryset(self, *args, **kwargs):
        """Return the annotated queryset for this endpoint"""
        queryset = super().get_queryset(*args, **kwargs)

        queryset = queryset.prefetch_related(
            'supplier',
            'lines',
        )

        queryset = serializers.PurchaseOrderSerializer.annotate_queryset(queryset)

        return queryset


class PurchaseOrderList(PurchaseOrderMixin, APIDownloadMixin, ListCreateAPI):
    """API endpoint for accessing a list of PurchaseOrder objects.

    - GET: Return list of PurchaseOrder objects (with filters)
    - POST: Create a new PurchaseOrder object
    """

    filterset_class = PurchaseOrderFilter

    def create(self, request, *args, **kwargs):
        """Save user information on create."""
        data = self.clean_data(request.data)

        duplicate_order = data.pop('duplicate_order', None)
        duplicate_line_items = str2bool(data.pop('duplicate_line_items', False))
        duplicate_extra_lines = str2bool(data.pop('duplicate_extra_lines', False))

        if duplicate_order is not None:
            try:
                duplicate_order = models.PurchaseOrder.objects.get(pk=duplicate_order)
            except (ValueError, models.PurchaseOrder.DoesNotExist):
                raise ValidationError({
                    'duplicate_order': [_('No matching purchase order found')],
                })

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            order = serializer.save()
            order.created_by = request.user
            order.save()

            # Duplicate line items from other order if required
            if duplicate_order is not None:

                if duplicate_line_items:
                    for line in duplicate_order.lines.all():
                        # Copy the line across to the new order
                        line.pk = None
                        line.order = order
                        line.received = 0

                        line.save()

                if duplicate_extra_lines:
                    for line in duplicate_order.extra_lines.all():
                        # Copy the line across to the new order
                        line.pk = None
                        line.order = order

                        line.save()

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def download_queryset(self, queryset, export_format):
        """Download the filtered queryset as a file"""
        dataset = PurchaseOrderResource().export(queryset=queryset)

        filedata = dataset.export(export_format)

        filename = f"InvenTree_PurchaseOrders.{export_format}"

        return DownloadFile(filedata, filename)

    def filter_queryset(self, queryset):
        """Custom queryset filtering"""
        # Perform basic filtering
        queryset = super().filter_queryset(queryset)

        params = self.request.query_params

        # Attempt to filter by part
        part = params.get('part', None)

        if part is not None:
            try:
                part = Part.objects.get(pk=part)
                queryset = queryset.filter(id__in=[p.id for p in part.purchase_orders()])
            except (Part.DoesNotExist, ValueError):
                pass

        # Attempt to filter by supplier part
        supplier_part = params.get('supplier_part', None)

        if supplier_part is not None:
            try:
                supplier_part = SupplierPart.objects.get(pk=supplier_part)
                queryset = queryset.filter(id__in=[p.id for p in supplier_part.purchase_orders()])
            except (ValueError, SupplierPart.DoesNotExist):
                pass

        # Filter by 'date range'
        min_date = params.get('min_date', None)
        max_date = params.get('max_date', None)

        if min_date is not None and max_date is not None:
            queryset = models.PurchaseOrder.filterByDate(queryset, min_date, max_date)

        return queryset

    filter_backends = SEARCH_ORDER_FILTER_ALIAS

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
        'reference',
        'supplier__name',
        'target_date',
        'line_items',
        'status',
        'responsible',
        'total_price',
        'project_code',
    ]

    ordering = '-reference'


class PurchaseOrderDetail(PurchaseOrderMixin, RetrieveUpdateDestroyAPI):
    """API endpoint for detail view of a PurchaseOrder object."""
    pass


class PurchaseOrderContextMixin:
    """Mixin to add purchase order object as serializer context variable."""

    queryset = models.PurchaseOrder.objects.all()

    def get_serializer_context(self):
        """Add the PurchaseOrder object to the serializer context."""
        context = super().get_serializer_context()

        # Pass the purchase order through to the serializer for validation
        try:
            context['order'] = models.PurchaseOrder.objects.get(pk=self.kwargs.get('pk', None))
        except Exception:
            pass

        context['request'] = self.request

        return context


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


class PurchaseOrderReceive(PurchaseOrderContextMixin, CreateAPI):
    """API endpoint to receive stock items against a PurchaseOrder.

    - The purchase order is specified in the URL.
    - Items to receive are specified as a list called "items" with the following options:
        - line_item: pk of the PO Line item
        - supplier_part: pk value of the supplier part
        - quantity: quantity to receive
        - status: stock item status
        - location: destination for stock item (optional)
        - batch_code: the batch code for this stock item
        - serial_numbers: serial numbers for this stock item
    - A global location must also be specified. This is used when no locations are specified for items, and no location is given in the PO line item
    """

    queryset = models.PurchaseOrderLineItem.objects.none()

    serializer_class = serializers.PurchaseOrderReceiveSerializer


class PurchaseOrderLineItemFilter(LineItemFilter):
    """Custom filters for the PurchaseOrderLineItemList endpoint."""

    class Meta:
        """Metaclass options."""
        price_field = 'purchase_price'
        model = models.PurchaseOrderLineItem
        fields = [
            'order',
            'part',
        ]

    pending = rest_filters.BooleanFilter(label='pending', method='filter_pending')

    def filter_pending(self, queryset, name, value):
        """Filter by "pending" status (order status = pending)"""
        if str2bool(value):
            return queryset.filter(order__status__in=PurchaseOrderStatusGroups.OPEN)
        return queryset.exclude(order__status__in=PurchaseOrderStatusGroups.OPEN)

    received = rest_filters.BooleanFilter(label='received', method='filter_received')

    def filter_received(self, queryset, name, value):
        """Filter by lines which are "received" (or "not" received)

        A line is considered "received" when received >= quantity
        """
        q = Q(received__gte=F('quantity'))

        if str2bool(value):
            return queryset.filter(q)
        # Only count "pending" orders
        return queryset.exclude(q).filter(order__status__in=PurchaseOrderStatusGroups.OPEN)


class PurchaseOrderLineItemMixin:
    """Mixin class for PurchaseOrderLineItem endpoints"""

    queryset = models.PurchaseOrderLineItem.objects.all()
    serializer_class = serializers.PurchaseOrderLineItemSerializer

    def get_queryset(self, *args, **kwargs):
        """Return annotated queryset for this endpoint"""
        queryset = super().get_queryset(*args, **kwargs)

        queryset = serializers.PurchaseOrderLineItemSerializer.annotate_queryset(queryset)

        return queryset

    def get_serializer(self, *args, **kwargs):
        """Return serializer instance for this endpoint"""
        try:
            kwargs['part_detail'] = str2bool(self.request.query_params.get('part_detail', False))
            kwargs['order_detail'] = str2bool(self.request.query_params.get('order_detail', False))
        except AttributeError:
            pass

        kwargs['context'] = self.get_serializer_context()

        return self.serializer_class(*args, **kwargs)


class PurchaseOrderLineItemList(PurchaseOrderLineItemMixin, APIDownloadMixin, ListCreateDestroyAPIView):
    """API endpoint for accessing a list of PurchaseOrderLineItem objects.

    - GET: Return a list of PurchaseOrder Line Item objects
    - POST: Create a new PurchaseOrderLineItem object
    """

    filterset_class = PurchaseOrderLineItemFilter

    def filter_queryset(self, queryset):
        """Additional filtering options."""
        params = self.request.query_params

        queryset = super().filter_queryset(queryset)

        base_part = params.get('base_part', None)

        if base_part:
            try:
                base_part = Part.objects.get(pk=base_part)

                queryset = queryset.filter(part__part=base_part)

            except (ValueError, Part.DoesNotExist):
                pass

        return queryset

    def download_queryset(self, queryset, export_format):
        """Download the requested queryset as a file"""
        dataset = PurchaseOrderLineItemResource().export(queryset=queryset)

        filedata = dataset.export(export_format)

        filename = f"InvenTree_PurchaseOrderItems.{export_format}"

        return DownloadFile(filedata, filename)

    filter_backends = SEARCH_ORDER_FILTER_ALIAS

    ordering_field_aliases = {
        'MPN': 'part__manufacturer_part__MPN',
        'SKU': 'part__SKU',
        'part_name': 'part__part__name',
    }

    ordering_fields = [
        'MPN',
        'part_name',
        'purchase_price',
        'quantity',
        'received',
        'reference',
        'SKU',
        'total_price',
        'target_date',
    ]

    search_fields = [
        'part__part__name',
        'part__part__description',
        'part__manufacturer_part__MPN',
        'part__SKU',
        'reference',
    ]


class PurchaseOrderLineItemDetail(PurchaseOrderLineItemMixin, RetrieveUpdateDestroyAPI):
    """Detail API endpoint for PurchaseOrderLineItem object."""
    pass


class PurchaseOrderExtraLineList(GeneralExtraLineList, ListCreateAPI):
    """API endpoint for accessing a list of PurchaseOrderExtraLine objects."""

    queryset = models.PurchaseOrderExtraLine.objects.all()
    serializer_class = serializers.PurchaseOrderExtraLineSerializer

    def download_queryset(self, queryset, export_format):
        """Download this queryset as a file"""
        dataset = PurchaseOrderExtraLineResource().export(queryset=queryset)
        filedata = dataset.export(export_format)
        filename = f"InvenTree_ExtraPurchaseOrderLines.{export_format}"

        return DownloadFile(filedata, filename)


class PurchaseOrderExtraLineDetail(RetrieveUpdateDestroyAPI):
    """API endpoint for detail view of a PurchaseOrderExtraLine object."""

    queryset = models.PurchaseOrderExtraLine.objects.all()
    serializer_class = serializers.PurchaseOrderExtraLineSerializer


class SalesOrderAttachmentList(AttachmentMixin, ListCreateDestroyAPIView):
    """API endpoint for listing (and creating) a SalesOrderAttachment (file upload)"""

    queryset = models.SalesOrderAttachment.objects.all()
    serializer_class = serializers.SalesOrderAttachmentSerializer

    filterset_fields = [
        'order',
    ]


class SalesOrderAttachmentDetail(AttachmentMixin, RetrieveUpdateDestroyAPI):
    """Detail endpoint for SalesOrderAttachment."""

    queryset = models.SalesOrderAttachment.objects.all()
    serializer_class = serializers.SalesOrderAttachmentSerializer


class SalesOrderFilter(OrderFilter):
    """Custom API filters for the SalesOrderList endpoint."""

    class Meta:
        """Metaclass options."""

        model = models.SalesOrder
        fields = [
            'customer',
        ]


class SalesOrderMixin:
    """Mixin class for SalesOrder endpoints"""

    queryset = models.SalesOrder.objects.all()
    serializer_class = serializers.SalesOrderSerializer

    def get_serializer(self, *args, **kwargs):
        """Return serializer instance for this endpoint"""
        try:
            kwargs['customer_detail'] = str2bool(self.request.query_params.get('customer_detail', False))
        except AttributeError:
            pass

        # Ensure the context is passed through to the serializer
        kwargs['context'] = self.get_serializer_context()

        return self.serializer_class(*args, **kwargs)

    def get_queryset(self, *args, **kwargs):
        """Return annotated queryset for this endpoint"""
        queryset = super().get_queryset(*args, **kwargs)

        queryset = queryset.prefetch_related(
            'customer',
            'lines'
        )

        queryset = serializers.SalesOrderSerializer.annotate_queryset(queryset)

        return queryset


class SalesOrderList(SalesOrderMixin, APIDownloadMixin, ListCreateAPI):
    """API endpoint for accessing a list of SalesOrder objects.

    - GET: Return list of SalesOrder objects (with filters)
    - POST: Create a new SalesOrder
    """

    filterset_class = SalesOrderFilter

    def create(self, request, *args, **kwargs):
        """Save user information on create."""
        serializer = self.get_serializer(data=self.clean_data(request.data))
        serializer.is_valid(raise_exception=True)

        item = serializer.save()
        item.created_by = request.user
        item.save()

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def download_queryset(self, queryset, export_format):
        """Download this queryset as a file"""
        dataset = SalesOrderResource().export(queryset=queryset)

        filedata = dataset.export(export_format)

        filename = f"InvenTree_SalesOrders.{export_format}"

        return DownloadFile(filedata, filename)

    def filter_queryset(self, queryset):
        """Perform custom filtering operations on the SalesOrder queryset."""
        queryset = super().filter_queryset(queryset)

        params = self.request.query_params

        # Filter by "Part"
        # Only return SalesOrder which have LineItem referencing the part
        part = params.get('part', None)

        if part is not None:
            try:
                part = Part.objects.get(pk=part)
                queryset = queryset.filter(id__in=[so.id for so in part.sales_orders()])
            except (Part.DoesNotExist, ValueError):
                pass

        # Filter by 'date range'
        min_date = params.get('min_date', None)
        max_date = params.get('max_date', None)

        if min_date is not None and max_date is not None:
            queryset = models.SalesOrder.filterByDate(queryset, min_date, max_date)

        return queryset

    filter_backends = SEARCH_ORDER_FILTER_ALIAS

    ordering_field_aliases = {
        'reference': ['reference_int', 'reference'],
        'project_code': ['project_code__code'],
    }

    filterset_fields = [
        'customer',
    ]

    ordering_fields = [
        'creation_date',
        'reference',
        'customer__name',
        'customer_reference',
        'status',
        'target_date',
        'line_items',
        'shipment_date',
        'total_price',
        'project_code',
    ]

    search_fields = [
        'customer__name',
        'reference',
        'description',
        'customer_reference',
        'project_code__code',
    ]

    ordering = '-reference'


class SalesOrderDetail(SalesOrderMixin, RetrieveUpdateDestroyAPI):
    """API endpoint for detail view of a SalesOrder object."""
    pass


class SalesOrderLineItemFilter(LineItemFilter):
    """Custom filters for SalesOrderLineItemList endpoint."""

    class Meta:
        """Metaclass options."""
        price_field = 'sale_price'
        model = models.SalesOrderLineItem
        fields = [
            'order',
            'part',
        ]

    completed = rest_filters.BooleanFilter(label='completed', method='filter_completed')

    def filter_completed(self, queryset, name, value):
        """Filter by lines which are "completed".

        A line is completed when shipped >= quantity
        """
        q = Q(shipped__gte=F('quantity'))

        if str2bool(value):
            return queryset.filter(q)
        return queryset.exclude(q)


class SalesOrderLineItemMixin:
    """Mixin class for SalesOrderLineItem endpoints"""

    queryset = models.SalesOrderLineItem.objects.all()
    serializer_class = serializers.SalesOrderLineItemSerializer

    def get_serializer(self, *args, **kwargs):
        """Return serializer for this endpoint with extra data as requested"""
        try:
            params = self.request.query_params

            kwargs['part_detail'] = str2bool(params.get('part_detail', False))
            kwargs['order_detail'] = str2bool(params.get('order_detail', False))
            kwargs['allocations'] = str2bool(params.get('allocations', False))
            kwargs['customer_detail'] = str2bool(params.get('customer_detail', False))

        except AttributeError:
            pass

        kwargs['context'] = self.get_serializer_context()

        return self.serializer_class(*args, **kwargs)

    def get_queryset(self, *args, **kwargs):
        """Return annotated queryset for this endpoint"""
        queryset = super().get_queryset(*args, **kwargs)

        queryset = queryset.prefetch_related(
            'part',
            'part__stock_items',
            'allocations',
            'allocations__item__location',
            'order',
            'order__stock_items',
        )

        queryset = serializers.SalesOrderLineItemSerializer.annotate_queryset(queryset)

        return queryset


class SalesOrderLineItemList(SalesOrderLineItemMixin, APIDownloadMixin, ListCreateAPI):
    """API endpoint for accessing a list of SalesOrderLineItem objects."""

    filterset_class = SalesOrderLineItemFilter

    def download_queryset(self, queryset, export_format):
        """Download the requested queryset as a file"""
        dataset = SalesOrderLineItemResource().export(queryset=queryset)
        filedata = dataset.export(export_format)

        filename = f"InvenTree_SalesOrderItems.{export_format}"

        return DownloadFile(filedata, filename)

    filter_backends = SEARCH_ORDER_FILTER

    ordering_fields = [
        'part__name',
        'quantity',
        'reference',
        'target_date',
    ]

    search_fields = [
        'part__name',
        'quantity',
        'reference',
    ]


class SalesOrderLineItemDetail(SalesOrderLineItemMixin, RetrieveUpdateDestroyAPI):
    """API endpoint for detail view of a SalesOrderLineItem object."""
    pass


class SalesOrderExtraLineList(GeneralExtraLineList, ListCreateAPI):
    """API endpoint for accessing a list of SalesOrderExtraLine objects."""

    queryset = models.SalesOrderExtraLine.objects.all()
    serializer_class = serializers.SalesOrderExtraLineSerializer

    def download_queryset(self, queryset, export_format):
        """Download this queryset as a file"""
        dataset = SalesOrderExtraLineResource().export(queryset=queryset)
        filedata = dataset.export(export_format)
        filename = f"InvenTree_ExtraSalesOrderLines.{export_format}"

        return DownloadFile(filedata, filename)


class SalesOrderExtraLineDetail(RetrieveUpdateDestroyAPI):
    """API endpoint for detail view of a SalesOrderExtraLine object."""

    queryset = models.SalesOrderExtraLine.objects.all()
    serializer_class = serializers.SalesOrderExtraLineSerializer


class SalesOrderContextMixin:
    """Mixin to add sales order object as serializer context variable."""

    queryset = models.SalesOrder.objects.all()

    def get_serializer_context(self):
        """Add the 'order' reference to the serializer context for any classes which inherit this mixin"""
        ctx = super().get_serializer_context()

        ctx['request'] = self.request

        try:
            ctx['order'] = models.SalesOrder.objects.get(pk=self.kwargs.get('pk', None))
        except Exception:
            pass

        return ctx


class SalesOrderCancel(SalesOrderContextMixin, CreateAPI):
    """API endpoint to cancel a SalesOrder"""
    serializer_class = serializers.SalesOrderCancelSerializer


class SalesOrderIssue(SalesOrderContextMixin, CreateAPI):
    """API endpoint to issue a SalesOrder"""
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


class SalesOrderAllocationDetail(RetrieveUpdateDestroyAPI):
    """API endpoint for detali view of a SalesOrderAllocation object."""

    queryset = models.SalesOrderAllocation.objects.all()
    serializer_class = serializers.SalesOrderAllocationSerializer


class SalesOrderAllocationList(ListAPI):
    """API endpoint for listing SalesOrderAllocation objects."""

    queryset = models.SalesOrderAllocation.objects.all()
    serializer_class = serializers.SalesOrderAllocationSerializer

    def get_serializer(self, *args, **kwargs):
        """Return the serializer instance for this endpoint.

        Adds extra detail serializers if requested
        """
        try:
            params = self.request.query_params

            kwargs['part_detail'] = str2bool(params.get('part_detail', False))
            kwargs['item_detail'] = str2bool(params.get('item_detail', False))
            kwargs['order_detail'] = str2bool(params.get('order_detail', False))
            kwargs['location_detail'] = str2bool(params.get('location_detail', False))
            kwargs['customer_detail'] = str2bool(params.get('customer_detail', False))
        except AttributeError:
            pass

        return self.serializer_class(*args, **kwargs)

    def filter_queryset(self, queryset):
        """Custom queryset filtering"""
        queryset = super().filter_queryset(queryset)

        # Filter by order
        params = self.request.query_params

        # Filter by "part" reference
        part = params.get('part', None)

        if part is not None:
            queryset = queryset.filter(item__part=part)

        # Filter by "order" reference
        order = params.get('order', None)

        if order is not None:
            queryset = queryset.filter(line__order=order)

        # Filter by "stock item"
        item = params.get('item', params.get('stock_item', None))

        if item is not None:
            queryset = queryset.filter(item=item)

        # Filter by "outstanding" order status
        outstanding = params.get('outstanding', None)

        if outstanding is not None:
            outstanding = str2bool(outstanding)

            if outstanding:
                # Filter only "open" orders
                # Filter only allocations which have *not* shipped
                queryset = queryset.filter(
                    line__order__status__in=SalesOrderStatusGroups.OPEN,
                    shipment__shipment_date=None,
                )
            else:
                queryset = queryset.exclude(
                    line__order__status__in=SalesOrderStatusGroups.OPEN,
                    shipment__shipment_date=None
                )

        return queryset

    filter_backends = [
        rest_filters.DjangoFilterBackend,
    ]


class SalesOrderShipmentFilter(rest_filters.FilterSet):
    """Custom filterset for the SalesOrderShipmentList endpoint."""

    class Meta:
        """Metaclass options."""

        model = models.SalesOrderShipment
        fields = [
            'order',
        ]

    shipped = rest_filters.BooleanFilter(label='shipped', method='filter_shipped')

    def filter_shipped(self, queryset, name, value):
        """Filter SalesOrder list by 'shipped' status (boolean)"""
        if str2bool(value):
            return queryset.exclude(shipment_date=None)
        return queryset.filter(shipment_date=None)

    delivered = rest_filters.BooleanFilter(label='delivered', method='filter_delivered')

    def filter_delivered(self, queryset, name, value):
        """Filter SalesOrder list by 'delivered' status (boolean)"""
        if str2bool(value):
            return queryset.exclude(delivery_date=None)
        return queryset.filter(delivery_date=None)


class SalesOrderShipmentList(ListCreateAPI):
    """API list endpoint for SalesOrderShipment model."""

    queryset = models.SalesOrderShipment.objects.all()
    serializer_class = serializers.SalesOrderShipmentSerializer
    filterset_class = SalesOrderShipmentFilter

    filter_backends = [
        rest_filters.DjangoFilterBackend,
    ]


class SalesOrderShipmentDetail(RetrieveUpdateDestroyAPI):
    """API detail endpooint for SalesOrderShipment model."""

    queryset = models.SalesOrderShipment.objects.all()
    serializer_class = serializers.SalesOrderShipmentSerializer


class SalesOrderShipmentComplete(CreateAPI):
    """API endpoint for completing (shipping) a SalesOrderShipment."""

    queryset = models.SalesOrderShipment.objects.all()
    serializer_class = serializers.SalesOrderShipmentCompleteSerializer

    def get_serializer_context(self):
        """Pass the request object to the serializer."""
        ctx = super().get_serializer_context()
        ctx['request'] = self.request

        try:
            ctx['shipment'] = models.SalesOrderShipment.objects.get(
                pk=self.kwargs.get('pk', None)
            )
        except Exception:
            pass

        return ctx


class PurchaseOrderAttachmentList(AttachmentMixin, ListCreateDestroyAPIView):
    """API endpoint for listing (and creating) a PurchaseOrderAttachment (file upload)"""

    queryset = models.PurchaseOrderAttachment.objects.all()
    serializer_class = serializers.PurchaseOrderAttachmentSerializer

    filterset_fields = [
        'order',
    ]


class PurchaseOrderAttachmentDetail(AttachmentMixin, RetrieveUpdateDestroyAPI):
    """Detail endpoint for a PurchaseOrderAttachment."""

    queryset = models.PurchaseOrderAttachment.objects.all()
    serializer_class = serializers.PurchaseOrderAttachmentSerializer


class ReturnOrderFilter(OrderFilter):
    """Custom API filters for the ReturnOrderList endpoint"""

    class Meta:
        """Metaclass options"""

        model = models.ReturnOrder
        fields = [
            'customer',
        ]


class ReturnOrderMixin:
    """Mixin class for ReturnOrder endpoints"""

    queryset = models.ReturnOrder.objects.all()
    serializer_class = serializers.ReturnOrderSerializer

    def get_serializer(self, *args, **kwargs):
        """Return serializer instance for this endpoint"""
        try:
            kwargs['customer_detail'] = str2bool(
                self.request.query_params.get('customer_detail', False)
            )
        except AttributeError:
            pass

        # Ensure the context is passed through to the serializer
        kwargs['context'] = self.get_serializer_context()

        return self.serializer_class(*args, **kwargs)

    def get_queryset(self, *args, **kwargs):
        """Return annotated queryset for this endpoint"""
        queryset = super().get_queryset(*args, **kwargs)

        queryset = queryset.prefetch_related(
            'customer',
        )

        queryset = serializers.ReturnOrderSerializer.annotate_queryset(queryset)

        return queryset


class ReturnOrderList(ReturnOrderMixin, APIDownloadMixin, ListCreateAPI):
    """API endpoint for accessing a list of ReturnOrder objects"""

    filterset_class = ReturnOrderFilter

    def create(self, request, *args, **kwargs):
        """Save user information on create."""
        serializer = self.get_serializer(data=self.clean_data(request.data))
        serializer.is_valid(raise_exception=True)

        item = serializer.save()
        item.created_by = request.user
        item.save()

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def download_queryset(self, queryset, export_format):
        """Download this queryset as a file"""
        dataset = ReturnOrderResource().export(queryset=queryset)
        filedata = dataset.export(export_format)
        filename = f"InvenTree_ReturnOrders.{export_format}"

        return DownloadFile(filedata, filename)

    filter_backends = SEARCH_ORDER_FILTER_ALIAS

    ordering_field_aliases = {
        'reference': ['reference_int', 'reference'],
        'project_code': ['project_code__code'],
    }

    ordering_fields = [
        'creation_date',
        'reference',
        'customer__name',
        'customer_reference',
        'line_items',
        'status',
        'target_date',
        'project_code',
    ]

    search_fields = [
        'customer__name',
        'reference',
        'description',
        'customer_reference',
        'project_code__code',
    ]

    ordering = '-reference'


class ReturnOrderDetail(ReturnOrderMixin, RetrieveUpdateDestroyAPI):
    """API endpoint for detail view of a single ReturnOrder object"""
    pass


class ReturnOrderContextMixin:
    """Simple mixin class to add a ReturnOrder to the serializer context"""

    queryset = models.ReturnOrder.objects.all()

    def get_serializer_context(self):
        """Add the PurchaseOrder object to the serializer context."""
        context = super().get_serializer_context()

        # Pass the ReturnOrder instance through to the serializer for validation
        try:
            context['order'] = models.ReturnOrder.objects.get(pk=self.kwargs.get('pk', None))
        except Exception:
            pass

        context['request'] = self.request

        return context


class ReturnOrderCancel(ReturnOrderContextMixin, CreateAPI):
    """API endpoint to cancel a ReturnOrder"""
    serializer_class = serializers.ReturnOrderCancelSerializer


class ReturnOrderComplete(ReturnOrderContextMixin, CreateAPI):
    """API endpoint to complete a ReturnOrder"""
    serializer_class = serializers.ReturnOrderCompleteSerializer


class ReturnOrderIssue(ReturnOrderContextMixin, CreateAPI):
    """API endpoint to issue (place) a ReturnOrder"""
    serializer_class = serializers.ReturnOrderIssueSerializer


class ReturnOrderReceive(ReturnOrderContextMixin, CreateAPI):
    """API endpoint to receive items against a ReturnOrder"""

    queryset = models.ReturnOrder.objects.none()
    serializer_class = serializers.ReturnOrderReceiveSerializer


class ReturnOrderLineItemFilter(LineItemFilter):
    """Custom filters for the ReturnOrderLineItemList endpoint"""

    class Meta:
        """Metaclass options"""
        price_field = 'price'
        model = models.ReturnOrderLineItem
        fields = [
            'order',
            'item',
        ]

    outcome = rest_filters.NumberFilter(label='outcome')

    received = rest_filters.BooleanFilter(label='received', method='filter_received')

    def filter_received(self, queryset, name, value):
        """Filter by 'received' field"""
        if str2bool(value):
            return queryset.exclude(received_date=None)
        return queryset.filter(received_date=None)


class ReturnOrderLineItemMixin:
    """Mixin class for ReturnOrderLineItem endpoints"""

    queryset = models.ReturnOrderLineItem.objects.all()
    serializer_class = serializers.ReturnOrderLineItemSerializer

    def get_serializer(self, *args, **kwargs):
        """Return serializer for this endpoint with extra data as requested"""
        try:
            params = self.request.query_params

            kwargs['order_detail'] = str2bool(params.get('order_detail', False))
            kwargs['item_detail'] = str2bool(params.get('item_detail', True))
            kwargs['part_detail'] = str2bool(params.get('part_detail', False))
        except AttributeError:
            pass

        kwargs['context'] = self.get_serializer_context()

        return self.serializer_class(*args, **kwargs)

    def get_queryset(self, *args, **kwargs):
        """Return annotated queryset for this endpoint"""
        queryset = super().get_queryset(*args, **kwargs)

        queryset = queryset.prefetch_related(
            'order',
            'item',
            'item__part',
        )

        return queryset


class ReturnOrderLineItemList(ReturnOrderLineItemMixin, APIDownloadMixin, ListCreateAPI):
    """API endpoint for accessing a list of ReturnOrderLineItemList objects"""

    filterset_class = ReturnOrderLineItemFilter

    def download_queryset(self, queryset, export_format):
        """Download the requested queryset as a file"""
        raise NotImplementedError("download_queryset not yet implemented for this endpoint")

    filter_backends = SEARCH_ORDER_FILTER

    ordering_fields = [
        'reference',
        'target_date',
        'received_date',
    ]

    search_fields = [
        'item_serial',
        'item__part__name',
        'item__part__description',
        'reference',
    ]


class ReturnOrderLineItemDetail(ReturnOrderLineItemMixin, RetrieveUpdateDestroyAPI):
    """API endpoint for detail view of a ReturnOrderLineItem object"""
    pass


class ReturnOrderExtraLineList(GeneralExtraLineList, ListCreateAPI):
    """API endpoint for accessing a list of ReturnOrderExtraLine objects"""

    queryset = models.ReturnOrderExtraLine.objects.all()
    serializer_class = serializers.ReturnOrderExtraLineSerializer

    def download_queryset(self, queryset, export_format):
        """Download this queryset as a file"""
        raise NotImplementedError("download_queryset not yet implemented")


class ReturnOrderExtraLineDetail(RetrieveUpdateDestroyAPI):
    """API endpoint for detail view of a ReturnOrderExtraLine object"""

    queryset = models.ReturnOrderExtraLine.objects.all()
    serializer_class = serializers.ReturnOrderExtraLineSerializer


class ReturnOrderAttachmentList(AttachmentMixin, ListCreateDestroyAPIView):
    """API endpoint for listing (and creating) a ReturnOrderAttachment (file upload)"""

    queryset = models.ReturnOrderAttachment.objects.all()
    serializer_class = serializers.ReturnOrderAttachmentSerializer

    filterset_fields = [
        'order',
    ]


class ReturnOrderAttachmentDetail(AttachmentMixin, RetrieveUpdateDestroyAPI):
    """Detail endpoint for the ReturnOrderAttachment model"""

    queryset = models.ReturnOrderAttachment.objects.all()
    serializer_class = serializers.ReturnOrderAttachmentSerializer


class OrderCalendarExport(ICalFeed):
    """Calendar export for Purchase/Sales Orders

    Optional parameters:
    - include_completed: true/false
        whether or not to show completed orders. Defaults to false
    """

    instance_url = get_base_url()

    instance_url = instance_url.replace("http://", "").replace("https://", "")
    timezone = settings.TIME_ZONE
    file_name = "calendar.ics"

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
                if auth[0].lower() == "basic":
                    uname, passwd = base64.b64decode(auth[1]).decode("ascii").split(':')
                    user = authenticate(username=uname, password=passwd)
                    if user is not None:
                        if user.is_active:
                            login(request, user)
                            request.user = user

        # Check again
        if request.user.is_authenticated:
            # Authenticated after second try
            return super().__call__(request, *args, **kwargs)

        # Still nothing - return Unauth. header with info on how to authenticate
        # Information is needed by client, eg Thunderbird
        response = JsonResponse({"detail": "Authentication credentials were not provided."})
        response['WWW-Authenticate'] = 'Basic realm="api"'
        response.status_code = 401
        return response

    def get_object(self, request, *args, **kwargs):
        """This is where settings from the URL etc will be obtained"""
        # Help:
        # https://django.readthedocs.io/en/stable/ref/contrib/syndication.html

        obj = {}
        obj['ordertype'] = kwargs['ordertype']
        obj['include_completed'] = bool(request.GET.get('include_completed', False))

        return obj

    def title(self, obj):
        """Return calendar title."""
        if obj["ordertype"] == 'purchase-order':
            ordertype_title = _('Purchase Order')
        elif obj["ordertype"] == 'sales-order':
            ordertype_title = _('Sales Order')
        elif obj["ordertype"] == 'return-order':
            ordertype_title = _('Return Order')
        else:
            ordertype_title = _('Unknown')

        return f'{common_models.InvenTreeSetting.get_setting("INVENTREE_COMPANY_NAME")} {ordertype_title}'

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
                outlist = models.PurchaseOrder.objects.filter(target_date__isnull=False).filter(status__lt=PurchaseOrderStatus.COMPLETE.value)
            else:
                outlist = models.PurchaseOrder.objects.filter(target_date__isnull=False)
        elif obj["ordertype"] == 'sales-order':
            if obj['include_completed'] is False:
                # Do not include completed (=shipped) orders from list in this case
                # Shipped status = 20
                outlist = models.SalesOrder.objects.filter(target_date__isnull=False).filter(status__lt=SalesOrderStatus.SHIPPED.value)
            else:
                outlist = models.SalesOrder.objects.filter(target_date__isnull=False)
        elif obj["ordertype"] == 'return-order':
            if obj['include_completed'] is False:
                # Do not include completed orders from list in this case
                # Complete status = 30
                outlist = models.ReturnOrder.objects.filter(target_date__isnull=False).filter(status__lt=ReturnOrderStatus.COMPLETE.value)
            else:
                outlist = models.ReturnOrder.objects.filter(target_date__isnull=False)
        else:
            outlist = []

        return outlist

    def item_title(self, item):
        """Set the event title to the order reference"""
        return f"{item.reference}"

    def item_description(self, item):
        """Set the event description"""
        return f"Company: {item.company.name}\nStatus: {item.get_status_display()}\nDescription: {item.description}"

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
        """Set item class to PUBLIC"""
        return 'PUBLIC'

    def item_guid(self, item):
        """Return globally unique UID for event"""
        return f'po_{item.pk}_{item.reference.replace(" ","-")}@{self.instance_url}'

    def item_link(self, item):
        """Set the item link."""
        return construct_absolute_url(item.get_absolute_url())


order_api_urls = [

    # API endpoints for purchase orders
    path('po/', include([

        # Purchase order attachments
        path('attachment/', include([
            path('<int:pk>/', PurchaseOrderAttachmentDetail.as_view(), name='api-po-attachment-detail'),
            re_path(r'^.*$', PurchaseOrderAttachmentList.as_view(), name='api-po-attachment-list'),
        ])),

        # Individual purchase order detail URLs
        path(r'<int:pk>/', include([
            re_path(r'^cancel/', PurchaseOrderCancel.as_view(), name='api-po-cancel'),
            re_path(r'^complete/', PurchaseOrderComplete.as_view(), name='api-po-complete'),
            re_path(r'^issue/', PurchaseOrderIssue.as_view(), name='api-po-issue'),
            re_path(r'^metadata/', MetadataView.as_view(), {'model': models.PurchaseOrder}, name='api-po-metadata'),
            re_path(r'^receive/', PurchaseOrderReceive.as_view(), name='api-po-receive'),

            # PurchaseOrder detail API endpoint
            re_path(r'.*$', PurchaseOrderDetail.as_view(), name='api-po-detail'),
        ])),

        # Purchase order status code information
        re_path(r'status/', StatusView.as_view(), {StatusView.MODEL_REF: PurchaseOrderStatus}, name='api-po-status-codes'),

        # Purchase order list
        re_path(r'^.*$', PurchaseOrderList.as_view(), name='api-po-list'),
    ])),

    # API endpoints for purchase order line items
    path('po-line/', include([
        path('<int:pk>/', include([
            re_path(r'^metadata/', MetadataView.as_view(), {'model': models.PurchaseOrderLineItem}, name='api-po-line-metadata'),
            re_path(r'^.*$', PurchaseOrderLineItemDetail.as_view(), name='api-po-line-detail'),
        ])),
        re_path(r'^.*$', PurchaseOrderLineItemList.as_view(), name='api-po-line-list'),
    ])),

    # API endpoints for purchase order extra line
    path('po-extra-line/', include([
        path('<int:pk>/', include([
            re_path(r'^metadata/', MetadataView.as_view(), {'model': models.PurchaseOrderExtraLine}, name='api-po-extra-line-metadata'),
            re_path(r'^.*$', PurchaseOrderExtraLineDetail.as_view(), name='api-po-extra-line-detail'),
        ])),
        path('', PurchaseOrderExtraLineList.as_view(), name='api-po-extra-line-list'),
    ])),

    # API endpoints for sales ordesr
    path('so/', include([
        path('attachment/', include([
            path('<int:pk>/', SalesOrderAttachmentDetail.as_view(), name='api-so-attachment-detail'),
            re_path(r'^.*$', SalesOrderAttachmentList.as_view(), name='api-so-attachment-list'),
        ])),

        path('shipment/', include([
            path(r'<int:pk>/', include([
                path('ship/', SalesOrderShipmentComplete.as_view(), name='api-so-shipment-ship'),
                re_path(r'^metadata/', MetadataView.as_view(), {'model': models.SalesOrderShipment}, name='api-so-shipment-metadata'),
                re_path(r'^.*$', SalesOrderShipmentDetail.as_view(), name='api-so-shipment-detail'),
            ])),
            re_path(r'^.*$', SalesOrderShipmentList.as_view(), name='api-so-shipment-list'),
        ])),

        # Sales order detail view
        path(r'<int:pk>/', include([
            re_path(r'^allocate/', SalesOrderAllocate.as_view(), name='api-so-allocate'),
            re_path(r'^allocate-serials/', SalesOrderAllocateSerials.as_view(), name='api-so-allocate-serials'),
            re_path(r'^cancel/', SalesOrderCancel.as_view(), name='api-so-cancel'),
            re_path(r'^issue/', SalesOrderIssue.as_view(), name='api-so-issue'),
            re_path(r'^complete/', SalesOrderComplete.as_view(), name='api-so-complete'),
            re_path(r'^metadata/', MetadataView.as_view(), {'model': models.SalesOrder}, name='api-so-metadata'),

            # SalesOrder detail endpoint
            re_path(r'^.*$', SalesOrderDetail.as_view(), name='api-so-detail'),
        ])),

        # Sales order status code information
        re_path(r'status/', StatusView.as_view(), {StatusView.MODEL_REF: SalesOrderStatus}, name='api-so-status-codes'),

        # Sales order list view
        re_path(r'^.*$', SalesOrderList.as_view(), name='api-so-list'),
    ])),

    # API endpoints for sales order line items
    path('so-line/', include([
        path('<int:pk>/', include([
            re_path(r'^metadata/', MetadataView.as_view(), {'model': models.SalesOrderLineItem}, name='api-so-line-metadata'),
            re_path(r'^.*$', SalesOrderLineItemDetail.as_view(), name='api-so-line-detail'),
        ])),
        path('', SalesOrderLineItemList.as_view(), name='api-so-line-list'),
    ])),

    # API endpoints for sales order extra line
    path('so-extra-line/', include([
        path('<int:pk>/', include([
            re_path(r'^metadata/', MetadataView.as_view(), {'model': models.SalesOrderExtraLine}, name='api-so-extra-line-metadata'),
            re_path(r'^.*$', SalesOrderExtraLineDetail.as_view(), name='api-so-extra-line-detail'),
        ])),
        path('', SalesOrderExtraLineList.as_view(), name='api-so-extra-line-list'),
    ])),

    # API endpoints for sales order allocations
    path('so-allocation/', include([
        path('<int:pk>/', SalesOrderAllocationDetail.as_view(), name='api-so-allocation-detail'),
        re_path(r'^.*$', SalesOrderAllocationList.as_view(), name='api-so-allocation-list'),
    ])),

    # API endpoints for return orders
    path('ro/', include([

        path('attachment/', include([
            path('<int:pk>/', ReturnOrderAttachmentDetail.as_view(), name='api-return-order-attachment-detail'),
            re_path(r'^.*$', ReturnOrderAttachmentList.as_view(), name='api-return-order-attachment-list'),
        ])),

        # Return Order detail endpoints
        path('<int:pk>/', include([
            re_path(r'cancel/', ReturnOrderCancel.as_view(), name='api-return-order-cancel'),
            re_path(r'complete/', ReturnOrderComplete.as_view(), name='api-return-order-complete'),
            re_path(r'issue/', ReturnOrderIssue.as_view(), name='api-return-order-issue'),
            re_path(r'receive/', ReturnOrderReceive.as_view(), name='api-return-order-receive'),
            re_path(r'metadata/', MetadataView.as_view(), {'model': models.ReturnOrder}, name='api-return-order-metadata'),
            re_path(r'.*$', ReturnOrderDetail.as_view(), name='api-return-order-detail'),
        ])),

        # Return order status code information
        re_path(r'status/', StatusView.as_view(), {StatusView.MODEL_REF: ReturnOrderStatus}, name='api-return-order-status-codes'),

        # Return Order list
        re_path(r'^.*$', ReturnOrderList.as_view(), name='api-return-order-list'),
    ])),

    # API endpoints for return order lines
    path('ro-line/', include([
        path('<int:pk>/', include([
            re_path(r'^metadata/', MetadataView.as_view(), {'model': models.ReturnOrderLineItem}, name='api-return-order-line-metadata'),
            re_path(r'^.*$', ReturnOrderLineItemDetail.as_view(), name='api-return-order-line-detail'),
        ])),

        # Return order line item status code information
        re_path(r'status/', StatusView.as_view(), {StatusView.MODEL_REF: ReturnOrderLineStatus}, name='api-return-order-line-status-codes'),

        path('', ReturnOrderLineItemList.as_view(), name='api-return-order-line-list'),
    ])),

    # API endpoints for return order extra line
    path('ro-extra-line/', include([
        path('<int:pk>/', include([
            re_path(r'^metadata/', MetadataView.as_view(), {'model': models.ReturnOrderExtraLine}, name='api-return-order-extra-line-metadata'),
            re_path(r'^.*$', ReturnOrderExtraLineDetail.as_view(), name='api-return-order-extra-line-detail'),
        ])),
        path('', ReturnOrderExtraLineList.as_view(), name='api-return-order-extra-line-list'),
    ])),

    # API endpoint for subscribing to ICS calendar of purchase/sales/return orders
    re_path(r'^calendar/(?P<ordertype>purchase-order|sales-order|return-order)/calendar.ics', OrderCalendarExport(), name='api-po-so-calendar'),
]
