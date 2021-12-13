"""
JSON API for the Order app
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _
from django.conf.urls import url, include
from django.db.models import Q, F

from django.http import Http404
from django_filters import rest_framework as rest_filters
from rest_framework import generics
from rest_framework import filters, status
from rest_framework.response import Response
from rest_framework.serializers import ValidationError


from InvenTree.filters import InvenTreeOrderingFilter
from InvenTree.helpers import str2bool
from InvenTree.api import AttachmentMixin
from InvenTree.status_codes import PurchaseOrderStatus, SalesOrderStatus

from part.models import Part
from company.models import SupplierPart

from .models import PurchaseOrder, PurchaseOrderLineItem
from .models import PurchaseOrderAttachment
from .serializers import POSerializer, POLineItemSerializer, POAttachmentSerializer

from .models import SalesOrder, SalesOrderLineItem, SalesOrderAllocation
from .models import SalesOrderAttachment
from .serializers import SalesOrderSerializer, SOLineItemSerializer, SOAttachmentSerializer
from .serializers import SalesOrderAllocationSerializer
from .serializers import POReceiveSerializer


class POList(generics.ListCreateAPIView):
    """ API endpoint for accessing a list of PurchaseOrder objects

    - GET: Return list of PO objects (with filters)
    - POST: Create a new PurchaseOrder object
    """

    queryset = PurchaseOrder.objects.all()
    serializer_class = POSerializer

    def create(self, request, *args, **kwargs):
        """
        Save user information on create
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        item = serializer.save()
        item.created_by = request.user
        item.save()

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def get_serializer(self, *args, **kwargs):

        try:
            kwargs['supplier_detail'] = str2bool(self.request.query_params.get('supplier_detail', False))
        except AttributeError:
            pass

        # Ensure the request context is passed through
        kwargs['context'] = self.get_serializer_context()

        return self.serializer_class(*args, **kwargs)

    def get_queryset(self, *args, **kwargs):

        queryset = super().get_queryset(*args, **kwargs)

        queryset = queryset.prefetch_related(
            'supplier',
            'lines',
        )

        queryset = POSerializer.annotate_queryset(queryset)

        return queryset

    def filter_queryset(self, queryset):

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
                queryset = queryset.filter(PurchaseOrder.OVERDUE_FILTER)
            else:
                queryset = queryset.exclude(PurchaseOrder.OVERDUE_FILTER)

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
            queryset = PurchaseOrder.filterByDate(queryset, min_date, max_date)

        return queryset

    filter_backends = [
        rest_filters.DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filter_fields = [
        'supplier',
    ]

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


class PODetail(generics.RetrieveUpdateDestroyAPIView):
    """ API endpoint for detail view of a PurchaseOrder object """

    queryset = PurchaseOrder.objects.all()
    serializer_class = POSerializer

    def get_serializer(self, *args, **kwargs):

        try:
            kwargs['supplier_detail'] = str2bool(self.request.query_params.get('supplier_detail', False))
        except AttributeError:
            pass

        # Ensure the request context is passed through
        kwargs['context'] = self.get_serializer_context()

        return self.serializer_class(*args, **kwargs)

    def get_queryset(self, *args, **kwargs):

        queryset = super().get_queryset(*args, **kwargs)

        queryset = queryset.prefetch_related(
            'supplier',
            'lines',
        )

        queryset = POSerializer.annotate_queryset(queryset)

        return queryset


class POReceive(generics.CreateAPIView):
    """
    API endpoint to receive stock items against a purchase order.

    - The purchase order is specified in the URL.
    - Items to receive are specified as a list called "items" with the following options:
        - supplier_part: pk value of the supplier part
        - quantity: quantity to receive
        - status: stock item status
        - location: destination for stock item (optional)
    - A global location can also be specified
    """

    queryset = PurchaseOrderLineItem.objects.none()

    serializer_class = POReceiveSerializer

    def get_serializer_context(self):

        context = super().get_serializer_context()

        # Pass the purchase order through to the serializer for validation
        context['order'] = self.get_order()
        context['request'] = self.request

        return context

    def get_order(self):
        """
        Returns the PurchaseOrder associated with this API endpoint
        """

        pk = self.kwargs.get('pk', None)

        try:
            order = PurchaseOrder.objects.get(pk=pk)
        except (PurchaseOrder.DoesNotExist, ValueError):
            raise ValidationError(_("Matching purchase order does not exist"))
        
        return order


class POLineItemFilter(rest_filters.FilterSet):
    """
    Custom filters for the POLineItemList endpoint
    """

    class Meta:
        model = PurchaseOrderLineItem
        fields = [
            'order',
            'part'
        ]

    completed = rest_filters.BooleanFilter(label='completed', method='filter_completed')

    def filter_completed(self, queryset, name, value):
        """
        Filter by lines which are "completed" (or "not" completed)

        A line is completed when received >= quantity
        """

        value = str2bool(value)

        q = Q(received__gte=F('quantity'))

        if value:
            queryset = queryset.filter(q)
        else:
            queryset = queryset.exclude(q)

        return queryset


class POLineItemList(generics.ListCreateAPIView):
    """ API endpoint for accessing a list of POLineItem objects

    - GET: Return a list of PO Line Item objects
    - POST: Create a new PurchaseOrderLineItem object
    """

    queryset = PurchaseOrderLineItem.objects.all()
    serializer_class = POLineItemSerializer
    filterset_class = POLineItemFilter

    def get_queryset(self, *args, **kwargs):

        queryset = super().get_queryset(*args, **kwargs)

        queryset = POLineItemSerializer.annotate_queryset(queryset)

        return queryset

    def get_serializer(self, *args, **kwargs):

        try:
            kwargs['part_detail'] = str2bool(self.request.query_params.get('part_detail', False))
        except AttributeError:
            pass

        kwargs['context'] = self.get_serializer_context()

        return self.serializer_class(*args, **kwargs)

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
    ]

    search_fields = [
        'part__part__name',
        'part__part__description',
        'part__MPN',
        'part__SKU',
        'reference',
    ]

    filter_fields = [
        'order',
        'part'
    ]


class POLineItemDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Detail API endpoint for PurchaseOrderLineItem object
    """

    queryset = PurchaseOrderLineItem.objects.all()
    serializer_class = POLineItemSerializer

    def get_queryset(self):

        queryset = super().get_queryset()

        queryset = POLineItemSerializer.annotate_queryset(queryset)

        return queryset


class SOAttachmentList(generics.ListCreateAPIView, AttachmentMixin):
    """
    API endpoint for listing (and creating) a SalesOrderAttachment (file upload)
    """

    queryset = SalesOrderAttachment.objects.all()
    serializer_class = SOAttachmentSerializer

    filter_backends = [
        rest_filters.DjangoFilterBackend,
    ]

    filter_fields = [
        'order',
    ]


class SOAttachmentDetail(generics.RetrieveUpdateDestroyAPIView, AttachmentMixin):
    """
    Detail endpoint for SalesOrderAttachment
    """

    queryset = SalesOrderAttachment.objects.all()
    serializer_class = SOAttachmentSerializer


class SOList(generics.ListCreateAPIView):
    """
    API endpoint for accessing a list of SalesOrder objects.

    - GET: Return list of SO objects (with filters)
    - POST: Create a new SalesOrder
    """

    queryset = SalesOrder.objects.all()
    serializer_class = SalesOrderSerializer

    def create(self, request, *args, **kwargs):
        """
        Save user information on create
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        item = serializer.save()
        
        item.created_by = request.user
        item.save()

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def get_serializer(self, *args, **kwargs):

        try:
            kwargs['customer_detail'] = str2bool(self.request.query_params.get('customer_detail', False))
        except AttributeError:
            pass

        # Ensure the context is passed through to the serializer
        kwargs['context'] = self.get_serializer_context()

        return self.serializer_class(*args, **kwargs)

    def get_queryset(self, *args, **kwargs):

        queryset = super().get_queryset(*args, **kwargs)

        queryset = queryset.prefetch_related(
            'customer',
            'lines'
        )

        queryset = SalesOrderSerializer.annotate_queryset(queryset)

        return queryset

    def filter_queryset(self, queryset):
        """
        Perform custom filtering operations on the SalesOrder queryset.
        """

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
                queryset = queryset.filter(SalesOrder.OVERDUE_FILTER)
            else:
                queryset = queryset.exclude(SalesOrder.OVERDUE_FILTER)

        status = params.get('status', None)

        if status is not None:
            queryset = queryset.filter(status=status)

        basket = params.get('basket', None)
        if basket is not None:
            queryset = queryset.filter(basket=basket)
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
            queryset = SalesOrder.filterByDate(queryset, min_date, max_date)

        return queryset

    filter_backends = [
        rest_filters.DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filter_fields = [
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


class SODetail(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint for detail view of a SalesOrder object.
    """

    queryset = SalesOrder.objects.all()
    serializer_class = SalesOrderSerializer

    def get_serializer(self, *args, **kwargs):

        try:
            kwargs['customer_detail'] = str2bool(self.request.query_params.get('customer_detail', False))
        except AttributeError:
            pass

        kwargs['context'] = self.get_serializer_context()

        return self.serializer_class(*args, **kwargs)

    def get_queryset(self, *args, **kwargs):

        queryset = super().get_queryset(*args, **kwargs)

        queryset = queryset.prefetch_related('customer', 'lines')

        queryset = SalesOrderSerializer.annotate_queryset(queryset)

        return queryset


class SOLineItemList(generics.ListCreateAPIView):
    """
    API endpoint for accessing a list of SalesOrderLineItem objects.
    """

    queryset = SalesOrderLineItem.objects.all()
    serializer_class = SOLineItemSerializer
   

    def get_serializer(self, *args, **kwargs):

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

        queryset = super().get_queryset(*args, **kwargs)

        queryset = queryset.prefetch_related(
            'part',
            'part__stock_items',
            'allocations',
            'allocations__item__location',
            'order',
            'order__stock_items',
        )

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
    ]

    search_fields = [
        'part__name',
        'quantity',
        'reference',
    ]

    filter_fields = [
        'order',
        'part',
    ]


class SOLineItemDetail(generics.RetrieveUpdateDestroyAPIView):
    """ API endpoint for detail view of a SalesOrderLineItem object """

    queryset = SalesOrderLineItem.objects.all()
    serializer_class = SOLineItemSerializer


class SOAllocationDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint for detali view of a SalesOrderAllocation object
    """

    queryset = SalesOrderAllocation.objects.all()
    serializer_class = SalesOrderAllocationSerializer

class SOAllocationFulFill(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint for detali view of a SalesOrderAllocation object
    """

    queryset = SalesOrderAllocation.objects.all()
    serializer_class = SalesOrderAllocationSerializer

    def delete (self, request, *args, **kwargs):
        try:
            quantity = int(self.kwargs['quantity'])
            stock_item_pk = self.kwargs['pk']
            instance = SalesOrderAllocation.objects.filter(item=stock_item_pk).first()
            if quantity < instance.quantity:
                instance.complete_allocation(request.user, quantity=quantity)
                instance.quantity = instance.quantity - quantity
                instance.save()
            else:
                instance.complete_allocation(request.user)
                self.perform_destroy(instance)
        except Http404:
            pass
        return Response(status=status.HTTP_204_NO_CONTENT)


class SOAllocationList(generics.ListCreateAPIView):
    """
    API endpoint for listing SalesOrderAllocation objects
    """
    queryset = SalesOrderAllocation.objects.all()
    serializer_class = SalesOrderAllocationSerializer

     # Check order if_packable and fully_allocated and if so set status to WAITING TO PACKING
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = serializer.save()

        
        order = SalesOrder.objects.filter(pk=item.line.order.pk).first()
        if order.is_fully_allocated() and order.is_packable:
            order.status = SalesOrderStatus.WAITING_FOR_PACKING
            order.save()
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


    def get_serializer(self, *args, **kwargs):

        try:
            params = self.request.query_params

            kwargs['part_detail'] = str2bool(params.get('part_detail', False))
            kwargs['item_detail'] = str2bool(params.get('item_detail', False))
            kwargs['order_detail'] = str2bool(params.get('order_detail', False))
            kwargs['location_detail'] = str2bool(params.get('location_detail', False))
        except AttributeError:
            pass

        return self.serializer_class(*args, **kwargs)

    def filter_queryset(self, queryset):

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

        # Filter by "outstanding" order status
        outstanding = params.get('outstanding', None)

        if outstanding is not None:
            outstanding = str2bool(outstanding)

            if outstanding:
                queryset = queryset.filter(line__order__status__in=SalesOrderStatus.OPEN)
            else:
                queryset = queryset.exclude(line__order__status__in=SalesOrderStatus.OPEN)

        return queryset

    filter_backends = [
        rest_filters.DjangoFilterBackend,
    ]

    # Default filterable fields
    filter_fields = [
        'item',
    ]


class POAttachmentList(generics.ListCreateAPIView, AttachmentMixin):
    """
    API endpoint for listing (and creating) a PurchaseOrderAttachment (file upload)
    """

    queryset = PurchaseOrderAttachment.objects.all()
    serializer_class = POAttachmentSerializer

    filter_backends = [
        rest_filters.DjangoFilterBackend,
    ]

    filter_fields = [
        'order',
    ]


class POAttachmentDetail(generics.RetrieveUpdateDestroyAPIView, AttachmentMixin):
    """
    Detail endpoint for a PurchaseOrderAttachment
    """

    queryset = PurchaseOrderAttachment.objects.all()
    serializer_class = POAttachmentSerializer


order_api_urls = [

    # API endpoints for purchase orders
    url(r'^po/', include([

        # Purchase order attachments
        url(r'attachment/', include([
            url(r'^(?P<pk>\d+)/$', POAttachmentDetail.as_view(), name='api-po-attachment-detail'),
            url(r'^.*$', POAttachmentList.as_view(), name='api-po-attachment-list'),
        ])),

        # Individual purchase order detail URLs
        url(r'^(?P<pk>\d+)/', include([
            url(r'^receive/', POReceive.as_view(), name='api-po-receive'),
            url(r'.*$', PODetail.as_view(), name='api-po-detail'),
        ])),

        # Purchase order list
        url(r'^.*$', POList.as_view(), name='api-po-list'),
    ])),

    # API endpoints for purchase order line items
    url(r'^po-line/', include([
        url(r'^(?P<pk>\d+)/$', POLineItemDetail.as_view(), name='api-po-line-detail'),
        url(r'^.*$', POLineItemList.as_view(), name='api-po-line-list'),
    ])),

    # API endpoints for sales ordesr
    url(r'^so/', include([
        url(r'attachment/', include([
            url(r'^(?P<pk>\d+)/$', SOAttachmentDetail.as_view(), name='api-so-attachment-detail'),
            url(r'^.*$', SOAttachmentList.as_view(), name='api-so-attachment-list'),
        ])),

        url(r'^(?P<pk>\d+)/$', SODetail.as_view(), name='api-so-detail'),
        url(r'^.*$', SOList.as_view(), name='api-so-list'),
    ])),

    # API endpoints for sales order line items
    url(r'^so-line/', include([
        url(r'^(?P<pk>\d+)/$', SOLineItemDetail.as_view(), name='api-so-line-detail'),
        url(r'^$', SOLineItemList.as_view(), name='api-so-line-list'),
    ])),

    # API endpoints for sales order allocations
    url(r'^so-allocation/', include([
        url(r'^fulfill/(?P<pk>\d+)/(?P<quantity>\d+)', SOAllocationFulFill.as_view(), name='api-so-allocation-fulfill'),
        url(r'^(?P<pk>\d+)/$', SOAllocationDetail.as_view(), name='api-so-allocation-detail'),
        url(r'^.*$', SOAllocationList.as_view(), name='api-so-allocation-list'),
    ])),
]
