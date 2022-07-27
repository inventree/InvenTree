"""JSON API for the Order app."""

from django.db.models import F, Q
from django.urls import include, path, re_path

from django_filters import rest_framework as rest_filters
from django_ical.views import ICalFeed
from rest_framework import filters, status
from rest_framework.response import Response
from rest_framework.views import APIView

import order.models as models
import order.serializers as serializers
from common.models import InvenTreeSetting
from common.settings import settings
from company.models import SupplierPart
from InvenTree.api import (APIDownloadMixin, AttachmentMixin,
                           ListCreateDestroyAPIView)
from InvenTree.filters import InvenTreeOrderingFilter
from InvenTree.helpers import DownloadFile, str2bool
from InvenTree.mixins import (CreateAPI, ListAPI, ListCreateAPI,
                              RetrieveUpdateAPI, RetrieveUpdateDestroyAPI)
from InvenTree.status_codes import PurchaseOrderStatus, SalesOrderStatus
from order.admin import (PurchaseOrderLineItemResource, PurchaseOrderResource,
                         SalesOrderResource)
from part.models import Part
from plugin.serializers import MetadataSerializer
from users.models import Owner


class GeneralExtraLineList:
    """General template for ExtraLine API classes."""

    def get_serializer(self, *args, **kwargs):
        """Return the serializer instance for this endpoint"""
        try:
            params = self.request.query_params

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

    filter_backends = [
        rest_filters.DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]

    ordering_fields = [
        'title',
        'quantity',
        'note',
        'reference',
    ]

    search_fields = [
        'title',
        'quantity',
        'note',
        'reference'
    ]

    filterset_fields = [
        'order',
    ]


class PurchaseOrderFilter(rest_filters.FilterSet):
    """Custom API filters for the PurchaseOrderList endpoint."""

    assigned_to_me = rest_filters.BooleanFilter(label='assigned_to_me', method='filter_assigned_to_me')

    def filter_assigned_to_me(self, queryset, name, value):
        """Filter by orders which are assigned to the current user."""
        value = str2bool(value)

        # Work out who "me" is!
        owners = Owner.get_owners_matching_user(self.request.user)

        if value:
            queryset = queryset.filter(responsible__in=owners)
        else:
            queryset = queryset.exclude(responsible__in=owners)

        return queryset

    class Meta:
        """Metaclass options."""

        model = models.PurchaseOrder
        fields = [
            'supplier',
        ]


class PurchaseOrderList(APIDownloadMixin, ListCreateAPI):
    """API endpoint for accessing a list of PurchaseOrder objects.

    - GET: Return list of PurchaseOrder objects (with filters)
    - POST: Create a new PurchaseOrder object
    """

    queryset = models.PurchaseOrder.objects.all()
    serializer_class = serializers.PurchaseOrderSerializer
    filterset_class = PurchaseOrderFilter

    def create(self, request, *args, **kwargs):
        """Save user information on create."""
        serializer = self.get_serializer(data=self.clean_data(request.data))
        serializer.is_valid(raise_exception=True)

        item = serializer.save()
        item.created_by = request.user
        item.save()

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

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

        # Filter by 'outstanding' status
        outstanding = params.get('outstanding', None)

        if outstanding is not None:
            outstanding = str2bool(outstanding)

            if outstanding:
                queryset = queryset.filter(status__in=PurchaseOrderStatus.OPEN)
            else:
                queryset = queryset.exclude(status__in=PurchaseOrderStatus.OPEN)

        # Filter by 'overdue' status
        overdue = params.get('overdue', None)

        if overdue is not None:
            overdue = str2bool(overdue)

            if overdue:
                queryset = queryset.filter(models.PurchaseOrder.OVERDUE_FILTER)
            else:
                queryset = queryset.exclude(models.PurchaseOrder.OVERDUE_FILTER)

        # Special filtering for 'status' field
        status = params.get('status', None)

        if status is not None:
            # First attempt to filter by integer value
            queryset = queryset.filter(status=status)

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

    filter_backends = [
        rest_filters.DjangoFilterBackend,
        filters.SearchFilter,
        InvenTreeOrderingFilter,
    ]

    ordering_field_aliases = {
        'reference': ['reference_int', 'reference'],
    }

    search_fields = [
        'reference',
        'supplier__name',
        'supplier_reference',
        'description',
    ]

    ordering_fields = [
        'creation_date',
        'reference',
        'supplier__name',
        'target_date',
        'line_items',
        'status',
    ]

    ordering = '-creation_date'


class PurchaseOrderDetail(RetrieveUpdateDestroyAPI):
    """API endpoint for detail view of a PurchaseOrder object."""

    queryset = models.PurchaseOrder.objects.all()
    serializer_class = serializers.PurchaseOrderSerializer

    def get_serializer(self, *args, **kwargs):
        """Return serializer instance for this endpoint"""
        try:
            kwargs['supplier_detail'] = str2bool(self.request.query_params.get('supplier_detail', False))
        except AttributeError:
            pass

        # Ensure the request context is passed through
        kwargs['context'] = self.get_serializer_context()

        return self.serializer_class(*args, **kwargs)

    def get_queryset(self, *args, **kwargs):
        """Return annotated queryset for this endpoint"""
        queryset = super().get_queryset(*args, **kwargs)

        queryset = queryset.prefetch_related(
            'supplier',
            'lines',
        )

        queryset = serializers.PurchaseOrderSerializer.annotate_queryset(queryset)

        return queryset


class PurchaseOrderContextMixin:
    """Mixin to add purchase order object as serializer context variable."""

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

    queryset = models.PurchaseOrder.objects.all()

    serializer_class = serializers.PurchaseOrderCancelSerializer


class PurchaseOrderComplete(PurchaseOrderContextMixin, CreateAPI):
    """API endpoint to 'complete' a purchase order."""

    queryset = models.PurchaseOrder.objects.all()

    serializer_class = serializers.PurchaseOrderCompleteSerializer


class PurchaseOrderIssue(PurchaseOrderContextMixin, CreateAPI):
    """API endpoint to 'complete' a purchase order."""

    queryset = models.PurchaseOrder.objects.all()

    serializer_class = serializers.PurchaseOrderIssueSerializer


class PurchaseOrderMetadata(RetrieveUpdateAPI):
    """API endpoint for viewing / updating PurchaseOrder metadata."""

    def get_serializer(self, *args, **kwargs):
        """Return MetadataSerializer instance for a PurchaseOrder"""
        return MetadataSerializer(models.PurchaseOrder, *args, **kwargs)

    queryset = models.PurchaseOrder.objects.all()


class PurchaseOrderReceive(PurchaseOrderContextMixin, CreateAPI):
    """API endpoint to receive stock items against a purchase order.

    - The purchase order is specified in the URL.
    - Items to receive are specified as a list called "items" with the following options:
        - supplier_part: pk value of the supplier part
        - quantity: quantity to receive
        - status: stock item status
        - location: destination for stock item (optional)
    - A global location can also be specified
    """

    queryset = models.PurchaseOrderLineItem.objects.none()

    serializer_class = serializers.PurchaseOrderReceiveSerializer


class PurchaseOrderLineItemFilter(rest_filters.FilterSet):
    """Custom filters for the PurchaseOrderLineItemList endpoint."""

    class Meta:
        """Metaclass options."""

        model = models.PurchaseOrderLineItem
        fields = [
            'order',
            'part',
        ]

    pending = rest_filters.BooleanFilter(label='pending', method='filter_pending')

    def filter_pending(self, queryset, name, value):
        """Filter by "pending" status (order status = pending)"""
        value = str2bool(value)

        if value:
            queryset = queryset.filter(order__status__in=PurchaseOrderStatus.OPEN)
        else:
            queryset = queryset.exclude(order__status__in=PurchaseOrderStatus.OPEN)

        return queryset

    order_status = rest_filters.NumberFilter(label='order_status', field_name='order__status')

    received = rest_filters.BooleanFilter(label='received', method='filter_received')

    def filter_received(self, queryset, name, value):
        """Filter by lines which are "received" (or "not" received)

        A line is considered "received" when received >= quantity
        """
        value = str2bool(value)

        q = Q(received__gte=F('quantity'))

        if value:
            queryset = queryset.filter(q)
        else:
            # Only count "pending" orders
            queryset = queryset.exclude(q).filter(order__status__in=PurchaseOrderStatus.OPEN)

        return queryset


class PurchaseOrderLineItemList(APIDownloadMixin, ListCreateAPI):
    """API endpoint for accessing a list of PurchaseOrderLineItem objects.

    - GET: Return a list of PurchaseOrder Line Item objects
    - POST: Create a new PurchaseOrderLineItem object
    """

    queryset = models.PurchaseOrderLineItem.objects.all()
    serializer_class = serializers.PurchaseOrderLineItemSerializer
    filterset_class = PurchaseOrderLineItemFilter

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

    filter_backends = [
        rest_filters.DjangoFilterBackend,
        filters.SearchFilter,
        InvenTreeOrderingFilter
    ]

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


class PurchaseOrderLineItemDetail(RetrieveUpdateDestroyAPI):
    """Detail API endpoint for PurchaseOrderLineItem object."""

    queryset = models.PurchaseOrderLineItem.objects.all()
    serializer_class = serializers.PurchaseOrderLineItemSerializer

    def get_queryset(self):
        """Return annotated queryset for this endpoint"""
        queryset = super().get_queryset()

        queryset = serializers.PurchaseOrderLineItemSerializer.annotate_queryset(queryset)

        return queryset


class PurchaseOrderExtraLineList(GeneralExtraLineList, ListCreateAPI):
    """API endpoint for accessing a list of PurchaseOrderExtraLine objects."""

    queryset = models.PurchaseOrderExtraLine.objects.all()
    serializer_class = serializers.PurchaseOrderExtraLineSerializer


class PurchaseOrderExtraLineDetail(RetrieveUpdateDestroyAPI):
    """API endpoint for detail view of a PurchaseOrderExtraLine object."""

    queryset = models.PurchaseOrderExtraLine.objects.all()
    serializer_class = serializers.PurchaseOrderExtraLineSerializer


class SalesOrderAttachmentList(AttachmentMixin, ListCreateDestroyAPIView):
    """API endpoint for listing (and creating) a SalesOrderAttachment (file upload)"""

    queryset = models.SalesOrderAttachment.objects.all()
    serializer_class = serializers.SalesOrderAttachmentSerializer

    filter_backends = [
        rest_filters.DjangoFilterBackend,
    ]

    filterset_fields = [
        'order',
    ]


class SalesOrderAttachmentDetail(AttachmentMixin, RetrieveUpdateDestroyAPI):
    """Detail endpoint for SalesOrderAttachment."""

    queryset = models.SalesOrderAttachment.objects.all()
    serializer_class = serializers.SalesOrderAttachmentSerializer


class SalesOrderList(APIDownloadMixin, ListCreateAPI):
    """API endpoint for accessing a list of SalesOrder objects.

    - GET: Return list of SalesOrder objects (with filters)
    - POST: Create a new SalesOrder
    """

    queryset = models.SalesOrder.objects.all()
    serializer_class = serializers.SalesOrderSerializer

    def create(self, request, *args, **kwargs):
        """Save user information on create."""
        serializer = self.get_serializer(data=self.clean_data(request.data))
        serializer.is_valid(raise_exception=True)

        item = serializer.save()
        item.created_by = request.user
        item.save()

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

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

        # Filter by 'outstanding' status
        outstanding = params.get('outstanding', None)

        if outstanding is not None:
            outstanding = str2bool(outstanding)

            if outstanding:
                queryset = queryset.filter(status__in=SalesOrderStatus.OPEN)
            else:
                queryset = queryset.exclude(status__in=SalesOrderStatus.OPEN)

        # Filter by 'overdue' status
        overdue = params.get('overdue', None)

        if overdue is not None:
            overdue = str2bool(overdue)

            if overdue:
                queryset = queryset.filter(models.SalesOrder.OVERDUE_FILTER)
            else:
                queryset = queryset.exclude(models.SalesOrder.OVERDUE_FILTER)

        status = params.get('status', None)

        if status is not None:
            queryset = queryset.filter(status=status)

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

    filter_backends = [
        rest_filters.DjangoFilterBackend,
        filters.SearchFilter,
        InvenTreeOrderingFilter,
    ]

    ordering_field_aliases = {
        'reference': ['reference_int', 'reference'],
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
    ]

    search_fields = [
        'customer__name',
        'reference',
        'description',
        'customer_reference',
    ]

    ordering = '-creation_date'


class SalesOrderDetail(RetrieveUpdateDestroyAPI):
    """API endpoint for detail view of a SalesOrder object."""

    queryset = models.SalesOrder.objects.all()
    serializer_class = serializers.SalesOrderSerializer

    def get_serializer(self, *args, **kwargs):
        """Return the serializer instance for this endpoint"""
        try:
            kwargs['customer_detail'] = str2bool(self.request.query_params.get('customer_detail', False))
        except AttributeError:
            pass

        kwargs['context'] = self.get_serializer_context()

        return self.serializer_class(*args, **kwargs)

    def get_queryset(self, *args, **kwargs):
        """Return the annotated queryset for this serializer"""
        queryset = super().get_queryset(*args, **kwargs)

        queryset = queryset.prefetch_related('customer', 'lines')

        queryset = serializers.SalesOrderSerializer.annotate_queryset(queryset)

        return queryset


class SalesOrderLineItemFilter(rest_filters.FilterSet):
    """Custom filters for SalesOrderLineItemList endpoint."""

    class Meta:
        """Metaclass options."""

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
        value = str2bool(value)

        q = Q(shipped__gte=F('quantity'))

        if value:
            queryset = queryset.filter(q)
        else:
            queryset = queryset.exclude(q)

        return queryset


class SalesOrderLineItemList(ListCreateAPI):
    """API endpoint for accessing a list of SalesOrderLineItem objects."""

    queryset = models.SalesOrderLineItem.objects.all()
    serializer_class = serializers.SalesOrderLineItemSerializer
    filterset_class = SalesOrderLineItemFilter

    def get_serializer(self, *args, **kwargs):
        """Return serializer for this endpoint with extra data as requested"""
        try:
            params = self.request.query_params

            kwargs['part_detail'] = str2bool(params.get('part_detail', False))
            kwargs['order_detail'] = str2bool(params.get('order_detail', False))
            kwargs['allocations'] = str2bool(params.get('allocations', False))
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

    filter_backends = [
        rest_filters.DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]

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

    filterset_fields = [
        'order',
        'part',
    ]


class SalesOrderExtraLineList(GeneralExtraLineList, ListCreateAPI):
    """API endpoint for accessing a list of SalesOrderExtraLine objects."""

    queryset = models.SalesOrderExtraLine.objects.all()
    serializer_class = serializers.SalesOrderExtraLineSerializer


class SalesOrderExtraLineDetail(RetrieveUpdateDestroyAPI):
    """API endpoint for detail view of a SalesOrderExtraLine object."""

    queryset = models.SalesOrderExtraLine.objects.all()
    serializer_class = serializers.SalesOrderExtraLineSerializer


class SalesOrderLineItemDetail(RetrieveUpdateDestroyAPI):
    """API endpoint for detail view of a SalesOrderLineItem object."""

    queryset = models.SalesOrderLineItem.objects.all()
    serializer_class = serializers.SalesOrderLineItemSerializer

    def get_queryset(self, *args, **kwargs):
        """Return annotated queryset for this endpoint"""
        queryset = super().get_queryset(*args, **kwargs)

        queryset = serializers.SalesOrderLineItemSerializer.annotate_queryset(queryset)

        return queryset


class SalesOrderContextMixin:
    """Mixin to add sales order object as serializer context variable."""

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

    queryset = models.SalesOrder.objects.all()
    serializer_class = serializers.SalesOrderCancelSerializer


class SalesOrderComplete(SalesOrderContextMixin, CreateAPI):
    """API endpoint for manually marking a SalesOrder as "complete"."""

    queryset = models.SalesOrder.objects.all()
    serializer_class = serializers.SalesOrderCompleteSerializer


class SalesOrderMetadata(RetrieveUpdateAPI):
    """API endpoint for viewing / updating SalesOrder metadata."""

    def get_serializer(self, *args, **kwargs):
        """Return a metadata serializer for the SalesOrder model"""
        return MetadataSerializer(models.SalesOrder, *args, **kwargs)

    queryset = models.SalesOrder.objects.all()


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
                    line__order__status__in=SalesOrderStatus.OPEN,
                    shipment__shipment_date=None,
                )
            else:
                queryset = queryset.exclude(
                    line__order__status__in=SalesOrderStatus.OPEN,
                    shipment__shipment_date=None
                )

        return queryset

    filter_backends = [
        rest_filters.DjangoFilterBackend,
    ]

    # Default filterable fields
    filterset_fields = [
    ]


class SalesOrderShipmentFilter(rest_filters.FilterSet):
    """Custom filterset for the SalesOrderShipmentList endpoint."""

    shipped = rest_filters.BooleanFilter(label='shipped', method='filter_shipped')

    def filter_shipped(self, queryset, name, value):
        """Filter SalesOrder list by 'shipped' status (boolean)"""
        value = str2bool(value)

        if value:
            queryset = queryset.exclude(shipment_date=None)
        else:
            queryset = queryset.filter(shipment_date=None)

        return queryset

    class Meta:
        """Metaclass options."""

        model = models.SalesOrderShipment
        fields = [
            'order',
        ]


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

    filter_backends = [
        rest_filters.DjangoFilterBackend,
    ]

    filterset_fields = [
        'order',
    ]


class PurchaseOrderAttachmentDetail(AttachmentMixin, RetrieveUpdateDestroyAPI):
    """Detail endpoint for a PurchaseOrderAttachment."""

    queryset = models.PurchaseOrderAttachment.objects.all()
    serializer_class = serializers.PurchaseOrderAttachmentSerializer


class PurchaseOrderCalendarExport(ICalFeed, APIView):
    """Calendar export for Purchase Orders

    Optional parameters:
    -
    """

    role_required = "purchase_order"
    permission_class = "view"

    # Parameters for the whole calendar
    instance_url = InvenTreeSetting.get_setting("INVENTREE_BASE_URL").replace("http://", "").replace("https://", "")
    timezone = settings.TIME_ZONE
    file_name = "calendar.ics"

    def get_object(self, request, *args, **kwargs):
        """Get specific parameters for this request, check for authentication."""
        return f"Username: {str(request.user)}, logged in ({request.user.is_authenticated})"

    def title(self, obj):
        """Return calendar title."""
        return f'{InvenTreeSetting.get_setting("INVENTREE_COMPANY_NAME")} {"PurchaseOrders"} {obj}'

    def product_id(self, obj):
        """Return calendar product id."""
        return f'//{self.instance_url}//{self.title(obj)}//EN'

    def items(self):
        """Return a list of PurchaseOrders.

        Filters:
        - Only return those which have a target_date set
        """
        return models.PurchaseOrder.objects.filter(target_date__isnull=False)

    def item_title(self, item):
        """Set the event title to the purchase order reference"""
        return item.reference

    def item_description(self, item):
        """Set the event description"""
        return item.description

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
        site_url = InvenTreeSetting.get_setting("INVENTREE_BASE_URL")
        return f'{site_url}{item.get_absolute_url()}'


order_api_urls = [

    # API endpoints for purchase orders
    re_path(r'^po/', include([

        # Purchase order attachments
        re_path(r'attachment/', include([
            path('<int:pk>/', PurchaseOrderAttachmentDetail.as_view(), name='api-po-attachment-detail'),
            re_path(r'^.*$', PurchaseOrderAttachmentList.as_view(), name='api-po-attachment-list'),
        ])),

        # Calendar view
        re_path(r'^calendar.ics', PurchaseOrderCalendarExport(), name='po-calendar'),

        # Individual purchase order detail URLs
        re_path(r'^(?P<pk>\d+)/', include([
            re_path(r'^cancel/', PurchaseOrderCancel.as_view(), name='api-po-cancel'),
            re_path(r'^complete/', PurchaseOrderComplete.as_view(), name='api-po-complete'),
            re_path(r'^issue/', PurchaseOrderIssue.as_view(), name='api-po-issue'),
            re_path(r'^metadata/', PurchaseOrderMetadata.as_view(), name='api-po-metadata'),
            re_path(r'^receive/', PurchaseOrderReceive.as_view(), name='api-po-receive'),

            # PurchaseOrder detail API endpoint
            re_path(r'.*$', PurchaseOrderDetail.as_view(), name='api-po-detail'),
        ])),

        # Purchase order list
        re_path(r'^.*$', PurchaseOrderList.as_view(), name='api-po-list'),
    ])),

    # API endpoints for purchase order line items
    re_path(r'^po-line/', include([
        path('<int:pk>/', PurchaseOrderLineItemDetail.as_view(), name='api-po-line-detail'),
        re_path(r'^.*$', PurchaseOrderLineItemList.as_view(), name='api-po-line-list'),
    ])),

    # API endpoints for purchase order extra line
    re_path(r'^po-extra-line/', include([
        path('<int:pk>/', PurchaseOrderExtraLineDetail.as_view(), name='api-po-extra-line-detail'),
        path('', PurchaseOrderExtraLineList.as_view(), name='api-po-extra-line-list'),
    ])),

    # API endpoints for sales ordesr
    re_path(r'^so/', include([
        re_path(r'attachment/', include([
            path('<int:pk>/', SalesOrderAttachmentDetail.as_view(), name='api-so-attachment-detail'),
            re_path(r'^.*$', SalesOrderAttachmentList.as_view(), name='api-so-attachment-list'),
        ])),

        re_path(r'^shipment/', include([
            re_path(r'^(?P<pk>\d+)/', include([
                path('ship/', SalesOrderShipmentComplete.as_view(), name='api-so-shipment-ship'),
                re_path(r'^.*$', SalesOrderShipmentDetail.as_view(), name='api-so-shipment-detail'),
            ])),
            re_path(r'^.*$', SalesOrderShipmentList.as_view(), name='api-so-shipment-list'),
        ])),

        # Sales order detail view
        re_path(r'^(?P<pk>\d+)/', include([
            re_path(r'^allocate/', SalesOrderAllocate.as_view(), name='api-so-allocate'),
            re_path(r'^allocate-serials/', SalesOrderAllocateSerials.as_view(), name='api-so-allocate-serials'),
            re_path(r'^cancel/', SalesOrderCancel.as_view(), name='api-so-cancel'),
            re_path(r'^complete/', SalesOrderComplete.as_view(), name='api-so-complete'),
            re_path(r'^metadata/', SalesOrderMetadata.as_view(), name='api-so-metadata'),

            # SalesOrder detail endpoint
            re_path(r'^.*$', SalesOrderDetail.as_view(), name='api-so-detail'),
        ])),

        # Sales order list view
        re_path(r'^.*$', SalesOrderList.as_view(), name='api-so-list'),
    ])),

    # API endpoints for sales order line items
    re_path(r'^so-line/', include([
        path('<int:pk>/', SalesOrderLineItemDetail.as_view(), name='api-so-line-detail'),
        path('', SalesOrderLineItemList.as_view(), name='api-so-line-list'),
    ])),

    # API endpoints for sales order extra line
    re_path(r'^so-extra-line/', include([
        path('<int:pk>/', SalesOrderExtraLineDetail.as_view(), name='api-so-extra-line-detail'),
        path('', SalesOrderExtraLineList.as_view(), name='api-so-extra-line-list'),
    ])),

    # API endpoints for sales order allocations
    re_path(r'^so-allocation/', include([
        path('<int:pk>/', SalesOrderAllocationDetail.as_view(), name='api-so-allocation-detail'),
        re_path(r'^.*$', SalesOrderAllocationList.as_view(), name='api-so-allocation-list'),
    ])),
]
