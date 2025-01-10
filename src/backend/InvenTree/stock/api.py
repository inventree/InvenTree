"""JSON API for the Stock app."""

from collections import OrderedDict
from datetime import timedelta

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.db.models import F, Q
from django.http import JsonResponse
from django.urls import include, path
from django.utils.translation import gettext_lazy as _

from django_filters import rest_framework as rest_filters
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import permissions, status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.serializers import ValidationError

import common.models
import common.settings
import InvenTree.helpers
import stock.serializers as StockSerializers
from build.models import Build
from build.serializers import BuildSerializer
from company.models import Company, SupplierPart
from company.serializers import CompanySerializer
from generic.states.api import StatusView
from importer.mixins import DataExportViewMixin
from InvenTree.api import ListCreateDestroyAPIView, MetadataView
from InvenTree.filters import (
    ORDER_FILTER_ALIAS,
    SEARCH_ORDER_FILTER,
    SEARCH_ORDER_FILTER_ALIAS,
    InvenTreeDateFilter,
)
from InvenTree.helpers import (
    extract_serial_numbers,
    generateTestKey,
    is_ajax,
    isNull,
    str2bool,
)
from InvenTree.mixins import (
    CreateAPI,
    CustomRetrieveUpdateDestroyAPI,
    ListAPI,
    ListCreateAPI,
    RetrieveAPI,
    RetrieveUpdateDestroyAPI,
)
from order.models import PurchaseOrder, ReturnOrder, SalesOrder
from order.serializers import (
    PurchaseOrderSerializer,
    ReturnOrderSerializer,
    SalesOrderSerializer,
)
from part.models import BomItem, Part, PartCategory
from part.serializers import PartBriefSerializer
from stock.generators import generate_batch_code, generate_serial_number
from stock.models import (
    StockItem,
    StockItemTestResult,
    StockItemTracking,
    StockLocation,
    StockLocationType,
)
from stock.status_codes import StockHistoryCode, StockStatus


class GenerateBatchCode(GenericAPIView):
    """API endpoint for generating batch codes."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = StockSerializers.GenerateBatchCodeSerializer

    def post(self, request, *args, **kwargs):
        """Generate a new batch code."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = {'batch_code': generate_batch_code(**serializer.validated_data)}

        return Response(data, status=status.HTTP_201_CREATED)


class GenerateSerialNumber(GenericAPIView):
    """API endpoint for generating serial numbers."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = StockSerializers.GenerateSerialNumberSerializer

    def post(self, request, *args, **kwargs):
        """Generate a new serial number."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = {'serial_number': generate_serial_number(**serializer.validated_data)}

        return Response(data, status=status.HTTP_201_CREATED)


class StockItemContextMixin:
    """Mixin class for adding StockItem object to serializer context."""

    role_required = 'stock.change'

    queryset = StockItem.objects.none()

    def get_serializer_context(self):
        """Extend serializer context."""
        context = super().get_serializer_context()
        context['request'] = self.request

        try:
            context['item'] = StockItem.objects.get(pk=self.kwargs.get('pk', None))
        except Exception:  # pragma: no cover
            pass

        return context


class StockItemSerialize(StockItemContextMixin, CreateAPI):
    """API endpoint for serializing a stock item."""

    serializer_class = StockSerializers.SerializeStockItemSerializer


class StockItemInstall(StockItemContextMixin, CreateAPI):
    """API endpoint for installing a particular stock item into this stock item.

    - stock_item.part must be in the BOM for this part
    - stock_item must currently be "in stock"
    - stock_item must be serialized (and not belong to another item)
    """

    serializer_class = StockSerializers.InstallStockItemSerializer


class StockItemUninstall(StockItemContextMixin, CreateAPI):
    """API endpoint for removing (uninstalling) items from this item."""

    serializer_class = StockSerializers.UninstallStockItemSerializer


class StockItemConvert(StockItemContextMixin, CreateAPI):
    """API endpoint for converting a stock item to a variant part."""

    serializer_class = StockSerializers.ConvertStockItemSerializer


class StockItemReturn(StockItemContextMixin, CreateAPI):
    """API endpoint for returning a stock item from a customer."""

    serializer_class = StockSerializers.ReturnStockItemSerializer


class StockAdjustView(CreateAPI):
    """A generic class for handling stocktake actions.

    Subclasses exist for:

    - StockCount: count stock items
    - StockAdd: add stock items
    - StockRemove: remove stock items
    - StockTransfer: transfer stock items
    """

    queryset = StockItem.objects.none()

    def get_serializer_context(self):
        """Extend serializer context."""
        context = super().get_serializer_context()
        context['request'] = self.request

        return context


class StockChangeStatus(StockAdjustView):
    """API endpoint to change the status code of multiple StockItem objects."""

    serializer_class = StockSerializers.StockChangeStatusSerializer


class StockCount(StockAdjustView):
    """Endpoint for counting stock (performing a stocktake)."""

    serializer_class = StockSerializers.StockCountSerializer


class StockAdd(StockAdjustView):
    """Endpoint for adding a quantity of stock to an existing StockItem."""

    serializer_class = StockSerializers.StockAddSerializer


class StockRemove(StockAdjustView):
    """Endpoint for removing a quantity of stock from an existing StockItem."""

    serializer_class = StockSerializers.StockRemoveSerializer


class StockTransfer(StockAdjustView):
    """API endpoint for performing stock movements."""

    serializer_class = StockSerializers.StockTransferSerializer


class StockAssign(CreateAPI):
    """API endpoint for assigning stock to a particular customer."""

    queryset = StockItem.objects.all()
    serializer_class = StockSerializers.StockAssignmentSerializer

    def get_serializer_context(self):
        """Extend serializer context."""
        ctx = super().get_serializer_context()
        ctx['request'] = self.request

        return ctx


class StockMerge(CreateAPI):
    """API endpoint for merging multiple stock items."""

    queryset = StockItem.objects.none()
    serializer_class = StockSerializers.StockMergeSerializer

    def get_serializer_context(self):
        """Extend serializer context."""
        ctx = super().get_serializer_context()
        ctx['request'] = self.request
        return ctx


class StockLocationFilter(rest_filters.FilterSet):
    """Base class for custom API filters for the StockLocation endpoint."""

    class Meta:
        """Meta class options for this filterset."""

        model = StockLocation
        fields = ['name', 'structural', 'external']

    location_type = rest_filters.ModelChoiceFilter(
        queryset=StockLocationType.objects.all(), field_name='location_type'
    )

    has_location_type = rest_filters.BooleanFilter(
        label='has_location_type', method='filter_has_location_type'
    )

    def filter_has_location_type(self, queryset, name, value):
        """Filter by whether or not the location has a location type."""
        if str2bool(value):
            return queryset.exclude(location_type=None)
        return queryset.filter(location_type=None)

    depth = rest_filters.NumberFilter(
        label=_('Depth'), method='filter_depth', help_text=_('Filter by location depth')
    )

    def filter_depth(self, queryset, name, value):
        """Filter by the "depth" of the StockLocation.

        - This filter is used to limit the depth of the location tree
        - If the "parent" filter is also provided, the depth is calculated from the parent location
        """
        parent = self.data.get('parent', None)

        # Only filter if the parent filter is *not* provided
        if not parent:
            queryset = queryset.filter(level__lte=value)

        return queryset

    top_level = rest_filters.BooleanFilter(
        label=_('Top Level'),
        method='filter_top_level',
        help_text=_('Filter by top-level locations'),
    )

    def filter_top_level(self, queryset, name, value):
        """Filter by top-level locations."""
        cascade = str2bool(self.data.get('cascade', False))

        if value and not cascade:
            return queryset.filter(parent=None)

        return queryset

    cascade = rest_filters.BooleanFilter(
        label=_('Cascade'),
        method='filter_cascade',
        help_text=_('Include sub-locations in filtered results'),
    )

    def filter_cascade(self, queryset, name, value):
        """Filter by whether to include sub-locations in the filtered results.

        Note: If the "parent" filter is provided, we offload the logic to that method.
        """
        parent = self.data.get('parent', None)
        top_level = str2bool(self.data.get('top_level', None))

        # If the parent is *not* provided, update the results based on the "cascade" value
        if (not parent or top_level) and not value:
            # If "cascade" is False, only return top-level location
            queryset = queryset.filter(parent=None)

        return queryset

    parent = rest_filters.ModelChoiceFilter(
        queryset=StockLocation.objects.all(),
        method='filter_parent',
        label=_('Parent Location'),
        help_text=_('Filter by parent location'),
    )

    def filter_parent(self, queryset, name, value):
        """Filter by parent location.

        Note that the filtering behaviour here varies,
        depending on whether the 'cascade' value is set.

        So, we have to check the "cascade" value here.
        """
        parent = value
        depth = self.data.get('depth', None)
        cascade = str2bool(self.data.get('cascade', False))

        if cascade:
            # Return recursive sub-locations
            queryset = queryset.filter(
                parent__in=parent.get_descendants(include_self=True)
            )
        else:
            # Return only direct children
            queryset = queryset.filter(parent=parent)

        if depth is not None:
            # Filter by depth from parent
            depth = int(depth)
            queryset = queryset.filter(level__lte=parent.level + depth)

        return queryset


class StockLocationList(DataExportViewMixin, ListCreateAPI):
    """API endpoint for list view of StockLocation objects.

    - GET: Return list of StockLocation objects
    - POST: Create a new StockLocation
    """

    queryset = StockLocation.objects.all().prefetch_related('tags')
    serializer_class = StockSerializers.LocationSerializer
    filterset_class = StockLocationFilter

    def get_queryset(self, *args, **kwargs):
        """Return annotated queryset for the StockLocationList endpoint."""
        queryset = super().get_queryset(*args, **kwargs)
        queryset = StockSerializers.LocationSerializer.annotate_queryset(queryset)
        return queryset

    filter_backends = SEARCH_ORDER_FILTER

    search_fields = ['name', 'description', 'pathstring', 'tags__name', 'tags__slug']

    ordering_fields = ['name', 'pathstring', 'items', 'level', 'tree_id', 'lft']

    ordering = ['tree_id', 'lft', 'name']


class StockLocationTree(ListAPI):
    """API endpoint for accessing a list of StockLocation objects, ready for rendering as a tree."""

    queryset = StockLocation.objects.all()
    serializer_class = StockSerializers.LocationTreeSerializer

    filter_backends = ORDER_FILTER_ALIAS

    ordering_fields = ['level', 'name', 'sublocations']

    # Order by tree level (top levels first) and then name
    ordering = ['level', 'name']

    ordering_field_aliases = {'level': ['level', 'name'], 'name': ['name', 'level']}

    def get_queryset(self, *args, **kwargs):
        """Return annotated queryset for the StockLocationTree endpoint."""
        queryset = super().get_queryset(*args, **kwargs)
        queryset = StockSerializers.LocationTreeSerializer.annotate_queryset(queryset)
        return queryset


class StockLocationTypeList(ListCreateAPI):
    """API endpoint for a list of StockLocationType objects.

    - GET: Return a list of all StockLocationType objects
    - POST: Create a StockLocationType
    """

    queryset = StockLocationType.objects.all()
    serializer_class = StockSerializers.StockLocationTypeSerializer

    filter_backends = SEARCH_ORDER_FILTER

    ordering_fields = ['name', 'location_count', 'icon']

    ordering = ['-location_count']

    search_fields = ['name']

    def get_queryset(self):
        """Override the queryset method to include location count."""
        queryset = super().get_queryset()
        queryset = StockSerializers.StockLocationTypeSerializer.annotate_queryset(
            queryset
        )

        return queryset


class StockLocationTypeDetail(RetrieveUpdateDestroyAPI):
    """API detail endpoint for a StockLocationType object.

    - GET: return a single StockLocationType
    - PUT: update a StockLocationType
    - PATCH: partial update a StockLocationType
    - DELETE: delete a StockLocationType
    """

    queryset = StockLocationType.objects.all()
    serializer_class = StockSerializers.StockLocationTypeSerializer

    def get_queryset(self):
        """Override the queryset method to include location count."""
        queryset = super().get_queryset()
        queryset = StockSerializers.StockLocationTypeSerializer.annotate_queryset(
            queryset
        )

        return queryset


class StockFilter(rest_filters.FilterSet):
    """FilterSet for StockItem LIST API."""

    class Meta:
        """Metaclass options for this filterset."""

        model = StockItem

        # Simple filter filters
        fields = [
            'supplier_part',
            'belongs_to',
            'build',
            'customer',
            'consumed_by',
            'sales_order',
            'purchase_order',
            'tags__name',
            'tags__slug',
        ]

    # Relationship filters
    manufacturer = rest_filters.ModelChoiceFilter(
        label='Manufacturer',
        queryset=Company.objects.all(),
        method='filter_manufacturer',
    )

    @extend_schema_field(OpenApiTypes.INT)
    def filter_manufacturer(self, queryset, name, company):
        """Filter by manufacturer."""
        return queryset.filter(
            Q(supplier_part__manufacturer_part__manufacturer__is_manufacturer=True)
            & Q(supplier_part__manufacturer_part__manufacturer=company)
        )

    supplier = rest_filters.ModelChoiceFilter(
        label=_('Supplier'),
        queryset=Company.objects.filter(is_supplier=True),
        field_name='supplier_part__supplier',
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
        label=_('Part'), queryset=Part.objects.all(), method='filter_part'
    )

    def filter_part(self, queryset, name, part):
        """Filter StockItem list by provided Part instance.

        Note:
        - If "part" is a variant, include all variants of the selected part
        - Otherwise, filter by the selected part
        """
        include_variants = str2bool(self.data.get('include_variants', True))

        if include_variants:
            return queryset.filter(part__in=part.get_descendants(include_self=True))
        else:
            return queryset.filter(part=part)

    # Part name filters
    name = rest_filters.CharFilter(
        label=_('Part name (case insensitive)'),
        field_name='part__name',
        lookup_expr='iexact',
    )

    name_contains = rest_filters.CharFilter(
        label=_('Part name contains (case insensitive)'),
        field_name='part__name',
        lookup_expr='icontains',
    )

    name_regex = rest_filters.CharFilter(
        label=_('Part name (regex)'), field_name='part__name', lookup_expr='iregex'
    )

    # Part IPN filters
    IPN = rest_filters.CharFilter(
        label=_('Part IPN (case insensitive)'),
        field_name='part__IPN',
        lookup_expr='iexact',
    )

    IPN_contains = rest_filters.CharFilter(
        label=_('Part IPN contains (case insensitive)'),
        field_name='part__IPN',
        lookup_expr='icontains',
    )

    IPN_regex = rest_filters.CharFilter(
        label=_('Part IPN (regex)'), field_name='part__IPN', lookup_expr='iregex'
    )

    # Part attribute filters
    assembly = rest_filters.BooleanFilter(
        label=_('Assembly'), field_name='part__assembly'
    )

    active = rest_filters.BooleanFilter(label=_('Active'), field_name='part__active')
    salable = rest_filters.BooleanFilter(label=_('Salable'), field_name='part__salable')

    min_stock = rest_filters.NumberFilter(
        label=_('Minimum stock'), field_name='quantity', lookup_expr='gte'
    )

    max_stock = rest_filters.NumberFilter(
        label=_('Maximum stock'), field_name='quantity', lookup_expr='lte'
    )

    status = rest_filters.NumberFilter(label=_('Status Code'), method='filter_status')

    def filter_status(self, queryset, name, value):
        """Filter by integer status code.

        Note: Also account for the possibility of a custom status code.
        """
        q1 = Q(status=value, status_custom_key__isnull=True)
        q2 = Q(status_custom_key=value)

        return queryset.filter(q1 | q2).distinct()

    allocated = rest_filters.BooleanFilter(
        label='Is Allocated', method='filter_allocated'
    )

    def filter_allocated(self, queryset, name, value):
        """Filter by whether or not the stock item is 'allocated'."""
        if str2bool(value):
            # Filter StockItem with either build allocations or sales order allocations
            return queryset.filter(
                Q(sales_order_allocations__isnull=False) | Q(allocations__isnull=False)
            ).distinct()
        # Filter StockItem without build allocations or sales order allocations
        return queryset.filter(
            Q(sales_order_allocations__isnull=True) & Q(allocations__isnull=True)
        )

    expired = rest_filters.BooleanFilter(label='Expired', method='filter_expired')

    def filter_expired(self, queryset, name, value):
        """Filter by whether or not the stock item has expired."""
        if not common.settings.stock_expiry_enabled():
            return queryset

        if str2bool(value):
            return queryset.filter(StockItem.EXPIRED_FILTER)
        return queryset.exclude(StockItem.EXPIRED_FILTER)

    external = rest_filters.BooleanFilter(
        label=_('External Location'), method='filter_external'
    )

    def filter_external(self, queryset, name, value):
        """Filter by whether or not the stock item is located in an external location."""
        if str2bool(value):
            return queryset.filter(location__external=True)
        return queryset.exclude(location__external=True)

    in_stock = rest_filters.BooleanFilter(label='In Stock', method='filter_in_stock')

    def filter_in_stock(self, queryset, name, value):
        """Filter by if item is in stock."""
        if str2bool(value):
            return queryset.filter(StockItem.IN_STOCK_FILTER)
        return queryset.exclude(StockItem.IN_STOCK_FILTER)

    available = rest_filters.BooleanFilter(label='Available', method='filter_available')

    def filter_available(self, queryset, name, value):
        """Filter by whether the StockItem is "available" or not.

        Here, "available" means that the allocated quantity is less than the total quantity
        """
        if str2bool(value):
            # The 'quantity' field is greater than the calculated 'allocated' field
            # Note that the item must also be "in stock"
            return queryset.filter(StockItem.IN_STOCK_FILTER).filter(
                Q(quantity__gt=F('allocated'))
            )
        # The 'quantity' field is less than (or equal to) the calculated 'allocated' field
        return queryset.filter(Q(quantity__lte=F('allocated')))

    batch = rest_filters.CharFilter(
        label='Batch code filter (case insensitive)', lookup_expr='iexact'
    )

    batch_regex = rest_filters.CharFilter(
        label='Batch code filter (regex)', field_name='batch', lookup_expr='iregex'
    )

    is_building = rest_filters.BooleanFilter(label='In production')

    # Serial number filtering
    serial_gte = rest_filters.NumberFilter(
        label='Serial number GTE', field_name='serial_int', lookup_expr='gte'
    )
    serial_lte = rest_filters.NumberFilter(
        label='Serial number LTE', field_name='serial_int', lookup_expr='lte'
    )

    serial = rest_filters.CharFilter(
        label='Serial number', field_name='serial', lookup_expr='exact'
    )

    serialized = rest_filters.BooleanFilter(
        label='Has serial number', method='filter_serialized'
    )

    def filter_serialized(self, queryset, name, value):
        """Filter by whether the StockItem has a serial number (or not)."""
        q = Q(serial=None) | Q(serial='')

        if str2bool(value):
            return queryset.exclude(q)

        return queryset.filter(q).distinct()

    has_batch = rest_filters.BooleanFilter(
        label='Has batch code', method='filter_has_batch'
    )

    def filter_has_batch(self, queryset, name, value):
        """Filter by whether the StockItem has a batch code (or not)."""
        q = Q(batch=None) | Q(batch='')

        if str2bool(value):
            return queryset.exclude(q)

        return queryset.filter(q).distinct()

    tracked = rest_filters.BooleanFilter(label='Tracked', method='filter_tracked')

    def filter_tracked(self, queryset, name, value):
        """Filter by whether this stock item is *tracked*.

        Meaning either:
        - It has a serial number
        - It has a batch code
        """
        q_batch = Q(batch=None) | Q(batch='')
        q_serial = Q(serial=None) | Q(serial='')

        if str2bool(value):
            return queryset.exclude(q_batch & q_serial)

        return queryset.filter(q_batch).filter(q_serial).distinct()

    consumed = rest_filters.BooleanFilter(
        label=_('Consumed by Build Order'), method='filter_consumed'
    )

    def filter_consumed(self, queryset, name, value):
        """Filter by whether the stock item has been consumed by a build order."""
        if str2bool(value):
            return queryset.filter(consumed_by__isnull=False)
        return queryset.filter(consumed_by__isnull=True)

    installed = rest_filters.BooleanFilter(
        label=_('Installed in other stock item'), method='filter_installed'
    )

    def filter_installed(self, queryset, name, value):
        """Filter stock items by "belongs_to" field being empty."""
        if str2bool(value):
            return queryset.exclude(belongs_to=None)
        return queryset.filter(belongs_to=None)

    has_installed_items = rest_filters.BooleanFilter(
        label='Has installed items', method='filter_has_installed'
    )

    def filter_has_installed(self, queryset, name, value):
        """Filter stock items by "belongs_to" field being empty."""
        if str2bool(value):
            return queryset.filter(installed_items__gt=0)
        return queryset.filter(installed_items=0)

    has_child_items = rest_filters.BooleanFilter(
        label='Has child items', method='filter_has_child_items'
    )

    def filter_has_child_items(self, queryset, name, value):
        """Filter stock items by "belongs_to" field being empty."""
        if str2bool(value):
            return queryset.filter(child_items__gt=0)
        return queryset.filter(child_items=0)

    sent_to_customer = rest_filters.BooleanFilter(
        label='Sent to customer', method='filter_sent_to_customer'
    )

    def filter_sent_to_customer(self, queryset, name, value):
        """Filter by sent to customer."""
        if str2bool(value):
            return queryset.exclude(customer=None)
        return queryset.filter(customer=None)

    depleted = rest_filters.BooleanFilter(label='Depleted', method='filter_depleted')

    def filter_depleted(self, queryset, name, value):
        """Filter by depleted items."""
        if str2bool(value):
            return queryset.filter(quantity__lte=0)
        return queryset.exclude(quantity__lte=0)

    has_purchase_price = rest_filters.BooleanFilter(
        label='Has purchase price', method='filter_has_purchase_price'
    )

    def filter_has_purchase_price(self, queryset, name, value):
        """Filter by having a purchase price."""
        if str2bool(value):
            return queryset.exclude(purchase_price=None)
        return queryset.filter(purchase_price=None)

    ancestor = rest_filters.ModelChoiceFilter(
        label='Ancestor', queryset=StockItem.objects.all(), method='filter_ancestor'
    )

    @extend_schema_field(OpenApiTypes.INT)
    def filter_ancestor(self, queryset, name, ancestor):
        """Filter based on ancestor stock item."""
        return queryset.filter(parent__in=ancestor.get_descendants(include_self=True))

    category = rest_filters.ModelChoiceFilter(
        label=_('Category'),
        queryset=PartCategory.objects.all(),
        method='filter_category',
    )

    @extend_schema_field(OpenApiTypes.INT)
    def filter_category(self, queryset, name, category):
        """Filter based on part category."""
        child_categories = category.get_descendants(include_self=True)

        return queryset.filter(part__category__in=child_categories)

    bom_item = rest_filters.ModelChoiceFilter(
        label=_('BOM Item'), queryset=BomItem.objects.all(), method='filter_bom_item'
    )

    @extend_schema_field(OpenApiTypes.INT)
    def filter_bom_item(self, queryset, name, bom_item):
        """Filter based on BOM item."""
        return queryset.filter(bom_item.get_stock_filter())

    part_tree = rest_filters.ModelChoiceFilter(
        label=_('Part Tree'), queryset=Part.objects.all(), method='filter_part_tree'
    )

    @extend_schema_field(OpenApiTypes.INT)
    def filter_part_tree(self, queryset, name, part_tree):
        """Filter based on part tree."""
        return queryset.filter(part__tree_id=part_tree.tree_id)

    company = rest_filters.ModelChoiceFilter(
        label=_('Company'), queryset=Company.objects.all(), method='filter_company'
    )

    @extend_schema_field(OpenApiTypes.INT)
    def filter_company(self, queryset, name, company):
        """Filter by company (either manufacturer or supplier)."""
        return queryset.filter(
            Q(supplier_part__supplier=company)
            | Q(supplier_part__manufacturer_part__manufacturer=company)
        ).distinct()

    # Update date filters
    updated_before = InvenTreeDateFilter(
        label=_('Updated before'), field_name='updated', lookup_expr='lt'
    )

    updated_after = InvenTreeDateFilter(
        label=_('Updated after'), field_name='updated', lookup_expr='gt'
    )

    stocktake_before = InvenTreeDateFilter(
        label=_('Stocktake Before'), field_name='stocktake_date', lookup_expr='lt'
    )

    stocktake_after = InvenTreeDateFilter(
        label=_('Stocktake After'), field_name='stocktake_date', lookup_expr='gt'
    )

    # Stock "expiry" filters
    expiry_before = InvenTreeDateFilter(
        label=_('Expiry date before'), field_name='expiry_date', lookup_expr='lt'
    )

    expiry_after = InvenTreeDateFilter(
        label=_('Expiry date after'), field_name='expiry_date', lookup_expr='gt'
    )

    stale = rest_filters.BooleanFilter(label=_('Stale'), method='filter_stale')

    def filter_stale(self, queryset, name, value):
        """Filter by stale stock items."""
        stale_days = common.models.InvenTreeSetting.get_setting('STOCK_STALE_DAYS')

        if stale_days <= 0:
            # No filtering, does not make sense
            return queryset

        stale_date = InvenTree.helpers.current_date() + timedelta(days=stale_days)
        stale_filter = (
            StockItem.IN_STOCK_FILTER
            & ~Q(expiry_date=None)
            & Q(expiry_date__lt=stale_date)
        )

        if str2bool(value):
            return queryset.filter(stale_filter)
        else:
            return queryset.exclude(stale_filter)


class StockApiMixin:
    """Mixin class for StockItem API endpoints."""

    serializer_class = StockSerializers.StockItemSerializer
    queryset = StockItem.objects.all()

    def get_queryset(self, *args, **kwargs):
        """Annotate queryset."""
        queryset = super().get_queryset(*args, **kwargs)
        queryset = StockSerializers.StockItemSerializer.annotate_queryset(queryset)

        return queryset

    def get_serializer_context(self):
        """Extend serializer context."""
        ctx = super().get_serializer_context()
        ctx['user'] = getattr(self.request, 'user', None)

        return ctx

    def get_serializer(self, *args, **kwargs):
        """Set context before returning serializer.

        Extra detail may be provided to the serializer via query parameters:

        - part_detail: Include detail about the StockItem's part
        - location_detail: Include detail about the StockItem's location
        - supplier_part_detail: Include detail about the StockItem's supplier_part
        - tests: Include detail about the StockItem's test results
        """
        try:
            params = self.request.query_params

            kwargs['part_detail'] = str2bool(params.get('part_detail', True))

            for key in [
                'path_detail',
                'location_detail',
                'supplier_part_detail',
                'tests',
            ]:
                kwargs[key] = str2bool(params.get(key, False))
        except AttributeError:  # pragma: no cover
            pass

        kwargs['context'] = self.get_serializer_context()

        return self.serializer_class(*args, **kwargs)


class StockList(DataExportViewMixin, StockApiMixin, ListCreateDestroyAPIView):
    """API endpoint for list view of Stock objects.

    - GET: Return a list of all StockItem objects (with optional query filters)
    - POST: Create a new StockItem
    - DELETE: Delete multiple StockItem objects
    """

    filterset_class = StockFilter

    def create(self, request, *args, **kwargs):
        """Create a new StockItem object via the API.

        We override the default 'create' implementation.

        If a location is *not* specified, but the linked *part* has a default location,
        we can pre-fill the location automatically.
        """
        user = request.user

        # Copy the request data, to side-step "mutability" issues
        data = OrderedDict()
        # Update with cleaned input data
        data.update(self.clean_data(request.data))

        quantity = data.get('quantity', None)

        if quantity is None:
            raise ValidationError({'quantity': _('Quantity is required')})

        try:
            part = Part.objects.get(pk=data.get('part', None))
        except (ValueError, Part.DoesNotExist):
            raise ValidationError({'part': _('Valid part must be supplied')})

        location = data.get('location', None)
        # Override location if not specified
        if location is None and part.default_location:
            data['location'] = part.default_location.pk

        expiry_date = data.get('expiry_date', None)

        # An expiry date was *not* specified - try to infer it!
        if expiry_date is None and part.default_expiry > 0:
            data['expiry_date'] = InvenTree.helpers.current_date() + timedelta(
                days=part.default_expiry
            )

        # Attempt to extract serial numbers from submitted data
        serials = None

        # Check if a set of serial numbers was provided
        serial_numbers = data.pop('serial_numbers', '')

        # Check if the supplier_part has a package size defined, which is not 1
        if supplier_part_id := data.get('supplier_part', None):
            try:
                supplier_part = SupplierPart.objects.get(pk=supplier_part_id)
            except Exception:
                raise ValidationError({
                    'supplier_part': _('The given supplier part does not exist')
                })

            if supplier_part.base_quantity() != 1:
                # Skip this check if pack size is 1 - makes no difference
                # use_pack_size = True -> Multiply quantity by pack size
                # use_pack_size = False -> Use quantity as is
                if 'use_pack_size' not in data:
                    raise ValidationError({
                        'use_pack_size': _(
                            'The supplier part has a pack size defined, but flag use_pack_size not set'
                        )
                    })
                elif bool(data.get('use_pack_size')):
                    quantity = data['quantity'] = supplier_part.base_quantity(quantity)

                    # Divide purchase price by pack size, to save correct price per stock item
                    if (
                        data.get('purchase_price')
                        and supplier_part.pack_quantity_native
                    ):
                        try:
                            data['purchase_price'] = float(
                                data['purchase_price']
                            ) / float(supplier_part.pack_quantity_native)
                        except ValueError:  # pragma: no cover
                            pass

        # Now remove the flag from data, so that it doesn't interfere with saving
        # Do this regardless of results above
        data.pop('use_pack_size', None)

        # Assign serial numbers for a trackable part
        if serial_numbers:
            if not part.trackable:
                raise ValidationError({
                    'serial_numbers': [
                        _('Serial numbers cannot be supplied for a non-trackable part')
                    ]
                })

            # If serial numbers are specified, check that they match!
            try:
                serials = extract_serial_numbers(
                    serial_numbers, quantity, part.get_latest_serial_number(), part=part
                )

                # Determine if any of the specified serial numbers are invalid
                # Note "invalid" means either they already exist, or do not pass custom rules
                invalid = []
                errors = []

                try:
                    invalid = part.find_conflicting_serial_numbers(serials)
                except DjangoValidationError as exc:
                    errors.append(exc.message)

                if len(invalid) > 0:
                    msg = _('The following serial numbers already exist or are invalid')
                    msg += ' : '
                    msg += ','.join([str(e) for e in invalid])

                    errors.append(msg)

                if len(errors) > 0:
                    raise ValidationError({'serial_numbers': errors})

            except DjangoValidationError as e:
                raise ValidationError({
                    'quantity': e.messages,
                    'serial_numbers': e.messages,
                })

        if serials is not None:
            """If the stock item is going to be serialized, set the quantity to 1."""
            data['quantity'] = 1

        # De-serialize the provided data
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)

        # Extract location information
        location = serializer.validated_data.get('location', None)

        with transaction.atomic():
            if serials:
                # Create multiple serialized StockItem objects
                items = StockItem._create_serial_numbers(
                    serials, **serializer.validated_data
                )

                # Next, bulk-create stock tracking entries for the newly created items
                tracking = []

                for item in items:
                    if entry := item.add_tracking_entry(
                        StockHistoryCode.CREATED,
                        user,
                        deltas={'status': item.status},
                        location=location,
                        quantity=float(item.quantity),
                        commit=False,
                    ):
                        tracking.append(entry)

                StockItemTracking.objects.bulk_create(tracking)

                response_data = {'quantity': quantity, 'serial_numbers': serials}

            else:
                # Create a single StockItem object
                # Note: This automatically creates a tracking entry
                item = serializer.save()
                item.save(user=user)

                response_data = serializer.data

        return Response(
            response_data,
            status=status.HTTP_201_CREATED,
            headers=self.get_success_headers(serializer.data),
        )

    def filter_queryset(self, queryset):
        """Custom filtering for the StockItem queryset."""
        params = self.request.query_params

        queryset = super().filter_queryset(queryset)

        # Exclude stock item tree
        exclude_tree = params.get('exclude_tree', None)

        if exclude_tree is not None:
            try:
                item = StockItem.objects.get(pk=exclude_tree)

                queryset = queryset.exclude(
                    pk__in=[it.pk for it in item.get_descendants(include_self=True)]
                )

            except (ValueError, StockItem.DoesNotExist):  # pragma: no cover
                pass

        # Does the client wish to filter by stock location?
        loc_id = params.get('location', None)

        cascade = str2bool(params.get('cascade', True))

        if loc_id is not None:
            # Filter by 'null' location (i.e. top-level items)
            if isNull(loc_id):
                if not cascade:
                    queryset = queryset.filter(location=None)
            else:
                try:
                    # If '?cascade=true' then include items which exist in sub-locations
                    if cascade:
                        location = StockLocation.objects.get(pk=loc_id)
                        queryset = queryset.filter(
                            location__in=location.getUniqueChildren()
                        )
                    else:
                        queryset = queryset.filter(location=loc_id)

                except (ValueError, StockLocation.DoesNotExist):  # pragma: no cover
                    pass

        return queryset

    filter_backends = SEARCH_ORDER_FILTER_ALIAS

    ordering_field_aliases = {
        'location': 'location__pathstring',
        'SKU': 'supplier_part__SKU',
        'MPN': 'supplier_part__manufacturer_part__MPN',
        'stock': ['quantity', 'serial_int', 'serial'],
    }

    ordering_fields = [
        'batch',
        'location',
        'part__name',
        'part__IPN',
        'updated',
        'stocktake_date',
        'expiry_date',
        'packaging',
        'quantity',
        'stock',
        'status',
        'SKU',
        'MPN',
    ]

    ordering = ['part__name', 'quantity', 'location']

    search_fields = [
        'serial',
        'batch',
        'part__name',
        'part__IPN',
        'part__description',
        'location__name',
        'tags__name',
        'tags__slug',
    ]


class StockDetail(StockApiMixin, RetrieveUpdateDestroyAPI):
    """API detail endpoint for a single StockItem instance."""


class StockItemTestResultMixin:
    """Mixin class for the StockItemTestResult API endpoints."""

    queryset = StockItemTestResult.objects.all()
    serializer_class = StockSerializers.StockItemTestResultSerializer

    def get_serializer_context(self):
        """Extend serializer context."""
        ctx = super().get_serializer_context()
        ctx['request'] = self.request
        return ctx

    def get_serializer(self, *args, **kwargs):
        """Set context before returning serializer."""
        try:
            kwargs['user_detail'] = str2bool(
                self.request.query_params.get('user_detail', False)
            )
            kwargs['template_detail'] = str2bool(
                self.request.query_params.get('template_detail', False)
            )
        except Exception:  # pragma: no cover
            pass

        kwargs['context'] = self.get_serializer_context()

        return self.serializer_class(*args, **kwargs)


class StockItemTestResultDetail(StockItemTestResultMixin, RetrieveUpdateDestroyAPI):
    """Detail endpoint for StockItemTestResult."""


class StockItemTestResultFilter(rest_filters.FilterSet):
    """API filter for the StockItemTestResult list."""

    class Meta:
        """Metaclass options."""

        model = StockItemTestResult

        # Simple filter fields
        fields = ['user', 'template', 'result', 'value']

    build = rest_filters.ModelChoiceFilter(
        label='Build', queryset=Build.objects.all(), field_name='stock_item__build'
    )

    part = rest_filters.ModelChoiceFilter(
        label='Part', queryset=Part.objects.all(), field_name='stock_item__part'
    )

    required = rest_filters.BooleanFilter(
        label='Required', field_name='template__required'
    )

    enabled = rest_filters.BooleanFilter(
        label='Enabled', field_name='template__enabled'
    )

    test = rest_filters.CharFilter(
        label='Test name (case insensitive)', method='filter_test_name'
    )

    def filter_test_name(self, queryset, name, value):
        """Filter by test name.

        This method is provided for legacy support,
        where the StockItemTestResult model had a "test" field.
        Now the "test" name is stored against the PartTestTemplate model
        """
        key = generateTestKey(value)
        return queryset.filter(template__key=key)


class StockItemTestResultList(StockItemTestResultMixin, ListCreateDestroyAPIView):
    """API endpoint for listing (and creating) a StockItemTestResult object."""

    filterset_class = StockItemTestResultFilter
    filter_backends = SEARCH_ORDER_FILTER

    filterset_fields = ['user', 'template', 'result', 'value']
    ordering_fields = ['date', 'result']

    ordering = 'date'

    def filter_queryset(self, queryset):
        """Filter by build or stock_item."""
        params = self.request.query_params

        queryset = super().filter_queryset(queryset)

        # Filter by stock item
        item = params.get('stock_item', None)

        if item is not None:
            try:
                item = StockItem.objects.get(pk=item)

                items = [item]

                # Do we wish to also include test results for 'installed' items?
                include_installed = str2bool(params.get('include_installed', False))

                if include_installed:
                    # Include items which are installed "underneath" this item
                    # Note that this function is recursive!
                    installed_items = item.get_installed_items(cascade=True)

                    items += list(installed_items)

                queryset = queryset.filter(stock_item__in=items)

            except (ValueError, StockItem.DoesNotExist):  # pragma: no cover
                pass

        return queryset

    def perform_create(self, serializer):
        """Create a new test result object.

        Also, check if an attachment was uploaded alongside the test result,
        and save it to the database if it were.
        """
        # Capture the user information
        test_result = serializer.save()
        test_result.user = self.request.user
        test_result.save()


class StockTrackingDetail(RetrieveAPI):
    """Detail API endpoint for StockItemTracking model."""

    queryset = StockItemTracking.objects.all()
    serializer_class = StockSerializers.StockTrackingSerializer


class StockTrackingList(DataExportViewMixin, ListAPI):
    """API endpoint for list view of StockItemTracking objects.

    StockItemTracking objects are read-only
    (they are created by internal model functionality)

    - GET: Return list of StockItemTracking objects
    """

    queryset = StockItemTracking.objects.all()
    serializer_class = StockSerializers.StockTrackingSerializer

    def get_serializer(self, *args, **kwargs):
        """Set context before returning serializer."""
        try:
            kwargs['item_detail'] = str2bool(
                self.request.query_params.get('item_detail', False)
            )
        except Exception:  # pragma: no cover
            pass

        try:
            kwargs['user_detail'] = str2bool(
                self.request.query_params.get('user_detail', False)
            )
        except Exception:  # pragma: no cover
            pass

        kwargs['context'] = self.get_serializer_context()

        return self.serializer_class(*args, **kwargs)

    def get_delta_model_map(self) -> dict:
        """Return a mapping of delta models to their respective models and serializers.

        This is used to generate additional context information for the historical data,
        with some attempt at caching so that we can reduce the number of database hits.
        """
        return {
            'part': (Part, PartBriefSerializer),
            'location': (StockLocation, StockSerializers.LocationSerializer),
            'customer': (Company, CompanySerializer),
            'purchaseorder': (PurchaseOrder, PurchaseOrderSerializer),
            'salesorder': (SalesOrder, SalesOrderSerializer),
            'returnorder': (ReturnOrder, ReturnOrderSerializer),
            'buildorder': (Build, BuildSerializer),
            'item': (StockItem, StockSerializers.StockItemSerializer),
            'stockitem': (StockItem, StockSerializers.StockItemSerializer),
        }

    def list(self, request, *args, **kwargs):
        """List all stock tracking entries."""
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
        else:
            serializer = self.get_serializer(queryset, many=True)

        data = serializer.data

        delta_models = self.get_delta_model_map()

        # Construct a set of related models we need to lookup for later
        related_model_lookups = {key: set() for key in delta_models}

        # Run a first pass through the data to determine which related models we need to lookup
        for item in data:
            deltas = item['deltas'] or {}

            for key in delta_models:
                if key in deltas:
                    related_model_lookups[key].add(deltas[key])

        for key in delta_models:
            model, serializer = delta_models[key]

            # Fetch all related models in one go
            related_models = model.objects.filter(pk__in=related_model_lookups[key])

            # Construct a mapping of pk -> serialized data
            related_data = {obj.pk: serializer(obj).data for obj in related_models}

            # Now, update the data with the serialized data
            for item in data:
                deltas = item['deltas'] or {}

                if key in deltas:
                    item['deltas'][f'{key}_detail'] = related_data.get(
                        deltas[key], None
                    )

        if page is not None:
            return self.get_paginated_response(data)
        if is_ajax(request):
            return JsonResponse(data, safe=False)
        return Response(data)

    def create(self, request, *args, **kwargs):
        """Create a new StockItemTracking object.

        Here we override the default 'create' implementation,
        to save the user information associated with the request object.
        """
        # Clean up input data
        data = self.clean_data(request.data)

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)

        # Record the user who created this Part object
        item = serializer.save()
        item.user = request.user
        item.system = False

        # quantity field cannot be explicitly adjusted  here
        item.quantity = item.item.quantity
        item.save()

        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    filter_backends = SEARCH_ORDER_FILTER

    filterset_fields = ['item', 'user']

    ordering = '-date'

    ordering_fields = ['date']

    search_fields = ['title', 'notes']


class LocationDetail(CustomRetrieveUpdateDestroyAPI):
    """API endpoint for detail view of StockLocation object.

    - GET: Return a single StockLocation object
    - PATCH: Update a StockLocation object
    - DELETE: Remove a StockLocation object
    """

    queryset = StockLocation.objects.all()
    serializer_class = StockSerializers.LocationSerializer

    def get_serializer(self, *args, **kwargs):
        """Add extra context to serializer based on provided query parameters."""
        try:
            params = self.request.query_params

            kwargs['path_detail'] = str2bool(params.get('path_detail', False))
        except AttributeError:
            pass

        kwargs['context'] = self.get_serializer_context()

        return self.serializer_class(*args, **kwargs)

    def get_queryset(self, *args, **kwargs):
        """Return annotated queryset for the StockLocationList endpoint."""
        queryset = super().get_queryset(*args, **kwargs)
        queryset = StockSerializers.LocationSerializer.annotate_queryset(queryset)
        return queryset

    def destroy(self, request, *args, **kwargs):
        """Delete a Stock location instance via the API."""
        delete_stock_items = str(request.data.get('delete_stock_items', 0)) == '1'
        delete_sub_locations = str(request.data.get('delete_sub_locations', 0)) == '1'

        return super().destroy(
            request,
            *args,
            **dict(
                kwargs,
                delete_sub_locations=delete_sub_locations,
                delete_stock_items=delete_stock_items,
            ),
        )


stock_api_urls = [
    path(
        'location/',
        include([
            path('tree/', StockLocationTree.as_view(), name='api-location-tree'),
            # Stock location detail endpoints
            path(
                '<int:pk>/',
                include([
                    path(
                        'metadata/',
                        MetadataView.as_view(),
                        {'model': StockLocation},
                        name='api-location-metadata',
                    ),
                    path('', LocationDetail.as_view(), name='api-location-detail'),
                ]),
            ),
            path('', StockLocationList.as_view(), name='api-location-list'),
        ]),
    ),
    # Stock location type endpoints
    path(
        'location-type/',
        include([
            path(
                '<int:pk>/',
                include([
                    path(
                        'metadata/',
                        MetadataView.as_view(),
                        {'model': StockLocationType},
                        name='api-location-type-metadata',
                    ),
                    path(
                        '',
                        StockLocationTypeDetail.as_view(),
                        name='api-location-type-detail',
                    ),
                ]),
            ),
            path('', StockLocationTypeList.as_view(), name='api-location-type-list'),
        ]),
    ),
    # Endpoints for bulk stock adjustment actions
    path('count/', StockCount.as_view(), name='api-stock-count'),
    path('add/', StockAdd.as_view(), name='api-stock-add'),
    path('remove/', StockRemove.as_view(), name='api-stock-remove'),
    path('transfer/', StockTransfer.as_view(), name='api-stock-transfer'),
    path('assign/', StockAssign.as_view(), name='api-stock-assign'),
    path('merge/', StockMerge.as_view(), name='api-stock-merge'),
    path('change_status/', StockChangeStatus.as_view(), name='api-stock-change-status'),
    # StockItemTestResult API endpoints
    path(
        'test/',
        include([
            path(
                '<int:pk>/',
                include([
                    path(
                        'metadata/',
                        MetadataView.as_view(),
                        {'model': StockItemTestResult},
                        name='api-stock-test-result-metadata',
                    ),
                    path(
                        '',
                        StockItemTestResultDetail.as_view(),
                        name='api-stock-test-result-detail',
                    ),
                ]),
            ),
            path(
                '', StockItemTestResultList.as_view(), name='api-stock-test-result-list'
            ),
        ]),
    ),
    # StockItemTracking API endpoints
    path(
        'track/',
        include([
            path(
                '<int:pk>/',
                StockTrackingDetail.as_view(),
                name='api-stock-tracking-detail',
            ),
            # Stock tracking status code information
            path(
                'status/',
                StatusView.as_view(),
                {StatusView.MODEL_REF: StockHistoryCode},
                name='api-stock-tracking-status-codes',
            ),
            path('', StockTrackingList.as_view(), name='api-stock-tracking-list'),
        ]),
    ),
    # Detail views for a single stock item
    path(
        '<int:pk>/',
        include([
            path('convert/', StockItemConvert.as_view(), name='api-stock-item-convert'),
            path('install/', StockItemInstall.as_view(), name='api-stock-item-install'),
            path(
                'metadata/',
                MetadataView.as_view(),
                {'model': StockItem},
                name='api-stock-item-metadata',
            ),
            path('return/', StockItemReturn.as_view(), name='api-stock-item-return'),
            path(
                'serialize/',
                StockItemSerialize.as_view(),
                name='api-stock-item-serialize',
            ),
            path(
                'uninstall/',
                StockItemUninstall.as_view(),
                name='api-stock-item-uninstall',
            ),
            path('', StockDetail.as_view(), name='api-stock-detail'),
        ]),
    ),
    # Stock item status code information
    path(
        'status/',
        StatusView.as_view(),
        {StatusView.MODEL_REF: StockStatus},
        name='api-stock-status-codes',
    ),
    # Anything else
    path('', StockList.as_view(), name='api-stock-list'),
]
