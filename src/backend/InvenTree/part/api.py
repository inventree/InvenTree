"""Provides a JSON API for the Part app."""

import functools
import re

from django.db.models import Count, F, Q
from django.urls import include, path, re_path
from django.utils.translation import gettext_lazy as _

from django_filters import rest_framework as rest_filters
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import permissions, serializers, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

import order.models
import part.filters
from build.models import Build, BuildItem
from build.status_codes import BuildStatusGroups
from importer.mixins import DataExportViewMixin
from InvenTree.api import ListCreateDestroyAPIView, MetadataView
from InvenTree.filters import (
    ORDER_FILTER,
    ORDER_FILTER_ALIAS,
    SEARCH_ORDER_FILTER,
    SEARCH_ORDER_FILTER_ALIAS,
    InvenTreeDateFilter,
    InvenTreeSearchFilter,
)
from InvenTree.helpers import isNull, str2bool
from InvenTree.mixins import (
    CreateAPI,
    CustomRetrieveUpdateDestroyAPI,
    ListAPI,
    ListCreateAPI,
    RetrieveAPI,
    RetrieveUpdateAPI,
    RetrieveUpdateDestroyAPI,
    UpdateAPI,
)
from InvenTree.permissions import RolePermission
from InvenTree.serializers import EmptySerializer
from order.status_codes import PurchaseOrderStatusGroups, SalesOrderStatusGroups
from stock.models import StockLocation

from . import serializers as part_serializers
from .models import (
    BomItem,
    BomItemSubstitute,
    Part,
    PartCategory,
    PartCategoryParameterTemplate,
    PartInternalPriceBreak,
    PartParameter,
    PartParameterTemplate,
    PartRelated,
    PartSellPriceBreak,
    PartStocktake,
    PartStocktakeReport,
    PartTestTemplate,
)


class CategoryMixin:
    """Mixin class for PartCategory endpoints."""

    serializer_class = part_serializers.CategorySerializer
    queryset = PartCategory.objects.all()

    def get_queryset(self, *args, **kwargs):
        """Return an annotated queryset for the CategoryDetail endpoint."""
        queryset = super().get_queryset(*args, **kwargs)
        queryset = part_serializers.CategorySerializer.annotate_queryset(queryset)
        return queryset

    def get_serializer_context(self):
        """Add extra context to the serializer for the CategoryDetail endpoint."""
        ctx = super().get_serializer_context()

        try:
            ctx['starred_categories'] = [
                star.category for star in self.request.user.starred_categories.all()
            ]
        except AttributeError:
            # Error is thrown if the view does not have an associated request
            ctx['starred_categories'] = []

        return ctx


class CategoryFilter(rest_filters.FilterSet):
    """Custom filterset class for the PartCategoryList endpoint."""

    class Meta:
        """Metaclass options for this filterset."""

        model = PartCategory
        fields = ['name', 'structural']

    starred = rest_filters.BooleanFilter(
        label=_('Starred'),
        method='filter_starred',
        help_text=_('Filter by starred categories'),
    )

    def filter_starred(self, queryset, name, value):
        """Filter by whether the PartCategory is starred by the current user."""
        user = self.request.user

        starred_categories = [
            star.category.pk for star in user.starred_categories.all()
        ]

        if str2bool(value):
            return queryset.filter(pk__in=starred_categories)

        return queryset.exclude(pk__in=starred_categories)

    depth = rest_filters.NumberFilter(
        label=_('Depth'), method='filter_depth', help_text=_('Filter by category depth')
    )

    def filter_depth(self, queryset, name, value):
        """Filter by the "depth" of the PartCategory.

        - This filter is used to limit the depth of the category tree
        - If the "parent" filter is also provided, the depth is calculated from the parent category
        """
        parent = self.data.get('parent', None)

        # Only filter if the parent filter is *not* provided
        if not parent:
            queryset = queryset.filter(level__lte=value)

        return queryset

    top_level = rest_filters.BooleanFilter(
        label=_('Top Level'),
        method='filter_top_level',
        help_text=_('Filter by top-level categories'),
    )

    def filter_top_level(self, queryset, name, value):
        """Filter by top-level categories."""
        cascade = str2bool(self.data.get('cascade', False))

        if value and not cascade:
            return queryset.filter(parent=None)

        return queryset

    cascade = rest_filters.BooleanFilter(
        label=_('Cascade'),
        method='filter_cascade',
        help_text=_('Include sub-categories in filtered results'),
    )

    def filter_cascade(self, queryset, name, value):
        """Filter by whether to include sub-categories in the filtered results.

        Note: If the "parent" filter is provided, we offload the logic to that method.
        """
        parent = str2bool(self.data.get('parent', None))
        top_level = str2bool(self.data.get('top_level', None))

        # If the parent is *not* provided, update the results based on the "cascade" value
        if (not parent or top_level) and not value:
            # If "cascade" is False, only return top-level categories
            queryset = queryset.filter(parent=None)

        return queryset

    parent = rest_filters.ModelChoiceFilter(
        queryset=PartCategory.objects.all(),
        label=_('Parent'),
        method='filter_parent',
        help_text=_('Filter by parent category'),
    )

    def filter_parent(self, queryset, name, value):
        """Filter by parent category.

        Note that the filtering behaviour here varies,
        depending on whether the 'cascade' value is set.

        So, we have to check the "cascade" value here.
        """
        parent = value
        depth = self.data.get('depth', None)
        cascade = str2bool(self.data.get('cascade', False))

        if cascade:
            # Return recursive subcategories
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

    exclude_tree = rest_filters.ModelChoiceFilter(
        queryset=PartCategory.objects.all(),
        label=_('Exclude Tree'),
        method='filter_exclude_tree',
        help_text=_('Exclude sub-categories under the specified category'),
    )

    @extend_schema_field(OpenApiTypes.INT)
    def filter_exclude_tree(self, queryset, name, value):
        """Exclude all sub-categories under the specified category."""
        # Exclude the specified category
        queryset = queryset.exclude(pk=value.pk)

        # Exclude any sub-categories also
        queryset = queryset.exclude(parent__in=value.get_descendants(include_self=True))

        return queryset


class CategoryList(CategoryMixin, DataExportViewMixin, ListCreateAPI):
    """API endpoint for accessing a list of PartCategory objects.

    - GET: Return a list of PartCategory objects
    - POST: Create a new PartCategory object
    """

    filterset_class = CategoryFilter

    filter_backends = SEARCH_ORDER_FILTER

    ordering_fields = ['name', 'pathstring', 'level', 'tree_id', 'lft', 'part_count']

    # Use hierarchical ordering by default
    ordering = ['tree_id', 'lft', 'name']

    search_fields = ['name', 'description', 'pathstring']


class CategoryDetail(CategoryMixin, CustomRetrieveUpdateDestroyAPI):
    """API endpoint for detail view of a single PartCategory object."""

    def get_serializer(self, *args, **kwargs):
        """Add additional context based on query parameters."""
        try:
            params = self.request.query_params

            kwargs['path_detail'] = str2bool(params.get('path_detail', False))
        except AttributeError:
            pass

        kwargs.setdefault('context', self.get_serializer_context())

        return self.serializer_class(*args, **kwargs)

    def update(self, request, *args, **kwargs):
        """Perform 'update' function and mark this part as 'starred' (or not)."""
        # Clean up input data
        data = self.clean_data(request.data)

        if 'starred' in data:
            starred = str2bool(data.get('starred', False))

            self.get_object().set_starred(request.user, starred, include_parents=False)

        response = super().update(request, *args, **kwargs)

        return response

    def destroy(self, request, *args, **kwargs):
        """Delete a Part category instance via the API."""
        delete_parts = (
            'delete_parts' in request.data and request.data['delete_parts'] == '1'
        )
        delete_child_categories = (
            'delete_child_categories' in request.data
            and request.data['delete_child_categories'] == '1'
        )
        return super().destroy(
            request,
            *args,
            **dict(
                kwargs,
                delete_parts=delete_parts,
                delete_child_categories=delete_child_categories,
            ),
        )


class CategoryTree(ListAPI):
    """API endpoint for accessing a list of PartCategory objects ready for rendering a tree."""

    queryset = PartCategory.objects.all()
    serializer_class = part_serializers.CategoryTree

    filter_backends = ORDER_FILTER_ALIAS

    ordering_fields = ['level', 'name', 'subcategories']

    ordering_field_aliases = {'level': ['level', 'name'], 'name': ['name', 'level']}

    # Order by tree level (top levels first) and then name
    ordering = ['level', 'name']

    def get_queryset(self, *args, **kwargs):
        """Return an annotated queryset for the CategoryTree endpoint."""
        queryset = super().get_queryset(*args, **kwargs)
        queryset = part_serializers.CategoryTree.annotate_queryset(queryset)
        return queryset


class CategoryParameterList(DataExportViewMixin, ListCreateAPI):
    """API endpoint for accessing a list of PartCategoryParameterTemplate objects.

    - GET: Return a list of PartCategoryParameterTemplate objects
    """

    queryset = PartCategoryParameterTemplate.objects.all()
    serializer_class = part_serializers.CategoryParameterTemplateSerializer

    def get_queryset(self):
        """Custom filtering.

        Rules:
        - Allow filtering by "null" parent to retrieve all categories parameter templates
        - Allow filtering by category
        - Allow traversing all parent categories
        """
        queryset = super().get_queryset()

        params = self.request.query_params

        category = params.get('category', None)

        if category is not None:
            try:
                category = PartCategory.objects.get(pk=category)

                fetch_parent = str2bool(params.get('fetch_parent', True))

                if fetch_parent:
                    parents = category.get_ancestors(include_self=True)
                    queryset = queryset.filter(category__in=[cat.pk for cat in parents])
                else:
                    queryset = queryset.filter(category=category)

            except (ValueError, PartCategory.DoesNotExist):
                pass

        return queryset


class CategoryParameterDetail(RetrieveUpdateDestroyAPI):
    """Detail endpoint for the PartCategoryParameterTemplate model."""

    queryset = PartCategoryParameterTemplate.objects.all()
    serializer_class = part_serializers.CategoryParameterTemplateSerializer


class PartSalePriceDetail(RetrieveUpdateDestroyAPI):
    """Detail endpoint for PartSellPriceBreak model."""

    queryset = PartSellPriceBreak.objects.all()
    serializer_class = part_serializers.PartSalePriceSerializer


class PartSalePriceList(DataExportViewMixin, ListCreateAPI):
    """API endpoint for list view of PartSalePriceBreak model."""

    queryset = PartSellPriceBreak.objects.all()
    serializer_class = part_serializers.PartSalePriceSerializer

    filter_backends = SEARCH_ORDER_FILTER
    filterset_fields = ['part']
    ordering_fields = ['quantity', 'price']
    ordering = 'quantity'


class PartInternalPriceDetail(RetrieveUpdateDestroyAPI):
    """Detail endpoint for PartInternalPriceBreak model."""

    queryset = PartInternalPriceBreak.objects.all()
    serializer_class = part_serializers.PartInternalPriceSerializer


class PartInternalPriceList(DataExportViewMixin, ListCreateAPI):
    """API endpoint for list view of PartInternalPriceBreak model."""

    queryset = PartInternalPriceBreak.objects.all()
    serializer_class = part_serializers.PartInternalPriceSerializer
    permission_required = 'roles.sales_order.show'

    filter_backends = SEARCH_ORDER_FILTER
    filterset_fields = ['part']
    ordering_fields = ['quantity', 'price']
    ordering = 'quantity'


class PartTestTemplateFilter(rest_filters.FilterSet):
    """Custom filterset class for the PartTestTemplateList endpoint."""

    class Meta:
        """Metaclass options for this filterset."""

        model = PartTestTemplate
        fields = ['enabled', 'key', 'required', 'requires_attachment', 'requires_value']

    part = rest_filters.ModelChoiceFilter(
        queryset=Part.objects.filter(testable=True),
        label='Part',
        field_name='part',
        method='filter_part',
    )

    def filter_part(self, queryset, name, part):
        """Filter by the 'part' field.

        Note: If the 'include_inherited' query parameter is set,
        we also include any parts "above" the specified part.
        """
        include_inherited = str2bool(
            self.request.query_params.get('include_inherited', True)
        )

        if include_inherited:
            return queryset.filter(part__in=part.get_ancestors(include_self=True))
        else:
            return queryset.filter(part=part)

    has_results = rest_filters.BooleanFilter(
        label=_('Has Results'), method='filter_has_results'
    )

    def filter_has_results(self, queryset, name, value):
        """Filter by whether the PartTestTemplate has any associated test results."""
        if str2bool(value):
            return queryset.exclude(results=0)
        return queryset.filter(results=0)


class PartTestTemplateMixin:
    """Mixin class for the PartTestTemplate API endpoints."""

    queryset = PartTestTemplate.objects.all()
    serializer_class = part_serializers.PartTestTemplateSerializer

    def get_queryset(self, *args, **kwargs):
        """Return an annotated queryset for the PartTestTemplateDetail endpoints."""
        queryset = super().get_queryset(*args, **kwargs)
        queryset = part_serializers.PartTestTemplateSerializer.annotate_queryset(
            queryset
        )
        return queryset


class PartTestTemplateDetail(PartTestTemplateMixin, RetrieveUpdateDestroyAPI):
    """Detail endpoint for PartTestTemplate model."""


class PartTestTemplateList(PartTestTemplateMixin, DataExportViewMixin, ListCreateAPI):
    """API endpoint for listing (and creating) a PartTestTemplate."""

    filterset_class = PartTestTemplateFilter

    filter_backends = SEARCH_ORDER_FILTER

    search_fields = ['test_name', 'description']

    ordering_fields = [
        'enabled',
        'required',
        'requires_value',
        'requires_attachment',
        'results',
        'test_name',
    ]

    ordering = 'test_name'


class PartThumbs(ListAPI):
    """API endpoint for retrieving information on available Part thumbnails."""

    queryset = Part.objects.all()
    serializer_class = part_serializers.PartThumbSerializer

    def get_queryset(self):
        """Return a queryset which excludes any parts without images."""
        queryset = super().get_queryset()

        # Get all Parts which have an associated image
        queryset = queryset.exclude(image='')

        return queryset

    def list(self, request, *args, **kwargs):
        """Serialize the available Part images.

        - Images may be used for multiple parts!
        """
        queryset = self.filter_queryset(self.get_queryset())

        # Return the most popular parts first
        data = (
            queryset.values('image').annotate(count=Count('image')).order_by('-count')
        )

        page = self.paginate_queryset(data)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
        else:
            serializer = self.get_serializer(data, many=True)

        data = serializer.data

        return Response(data)

    filter_backends = [InvenTreeSearchFilter]

    search_fields = [
        'name',
        'description',
        'IPN',
        'revision',
        'keywords',
        'category__name',
    ]


class PartThumbsUpdate(RetrieveUpdateAPI):
    """API endpoint for updating Part thumbnails."""

    queryset = Part.objects.all()
    serializer_class = part_serializers.PartThumbSerializerUpdate

    filter_backends = [DjangoFilterBackend]


class PartScheduling(RetrieveAPI):
    """API endpoint for delivering "scheduling" information about a given part via the API.

    Returns a chronologically ordered list about future "scheduled" events,
    concerning stock levels for the part:

    - Purchase Orders (incoming stock)
    - Sales Orders (outgoing stock)
    - Build Orders (incoming completed stock)
    - Build Orders (outgoing allocated stock)
    """

    queryset = Part.objects.all()
    serializer_class = part_serializers.PartSchedulingSerializer

    def retrieve(self, request, *args, **kwargs):
        """Return scheduling information for the referenced Part instance."""
        part = self.get_object()

        schedule = []

        def add_schedule_entry(date, quantity, title, instance, speculative_quantity=0):
            """Add a new entry to the schedule list.

            Arguments:
                - date: The date of the scheduled event
                - quantity: The quantity of stock to be added or removed
                - title: The title of the scheduled event
                - instance: The associated model instance (e.g. SalesOrder object)
                - speculative_quantity: A speculative quantity to be added or removed
            """
            schedule.append({
                'date': date,
                'quantity': quantity,
                'speculative_quantity': speculative_quantity,
                'title': title,
                'label': str(instance.reference),
                'model': instance.__class__.__name__.lower(),
                'model_id': instance.pk,
            })

        # Add purchase order (incoming stock) information
        po_lines = order.models.PurchaseOrderLineItem.objects.filter(
            part__part=part, order__status__in=PurchaseOrderStatusGroups.OPEN
        )

        for line in po_lines:
            target_date = line.target_date or line.order.target_date

            line_quantity = max(line.quantity - line.received, 0)

            # Multiply by the pack quantity of the SupplierPart
            quantity = line.part.base_quantity(line_quantity)

            add_schedule_entry(
                target_date, quantity, _('Incoming Purchase Order'), line.order
            )

        # Add sales order (outgoing stock) information
        so_lines = order.models.SalesOrderLineItem.objects.filter(
            part=part, order__status__in=SalesOrderStatusGroups.OPEN
        )

        for line in so_lines:
            target_date = line.target_date or line.order.target_date

            quantity = max(line.quantity - line.shipped, 0)

            add_schedule_entry(
                target_date, -quantity, _('Outgoing Sales Order'), line.order
            )

        # Add build orders (incoming stock) information
        build_orders = Build.objects.filter(
            part=part, status__in=BuildStatusGroups.ACTIVE_CODES
        )

        for build in build_orders:
            quantity = max(build.quantity - build.completed, 0)

            add_schedule_entry(
                build.target_date, quantity, _('Stock produced by Build Order'), build
            )

        """
        Add build order allocation (outgoing stock) information.

        Here we need some careful consideration:

        - 'Tracked' stock items are removed from stock when the individual Build Output is completed
        - 'Untracked' stock items are removed from stock when the Build Order is completed

        The 'simplest' approach here is to look at existing BuildItem allocations which reference this part,
        and "schedule" them for removal at the time of build order completion.

        This assumes that the user is responsible for correctly allocating parts.

        However, it has the added benefit of side-stepping the various BOM substitution options,
        and just looking at what stock items the user has actually allocated against the Build.
        """

        # Grab a list of BomItem objects that this part might be used in
        bom_items = BomItem.objects.filter(part.get_used_in_bom_item_filter())

        # Track all outstanding build orders
        seen_builds = set()

        for bom_item in bom_items:
            # Find a list of active builds for this BomItem

            if bom_item.inherited:
                # An "inherited" BOM item filters down to variant parts also
                children = bom_item.part.get_descendants(include_self=True)
                builds = Build.objects.filter(
                    status__in=BuildStatusGroups.ACTIVE_CODES, part__in=children
                )
            else:
                builds = Build.objects.filter(
                    status__in=BuildStatusGroups.ACTIVE_CODES, part=bom_item.part
                )

            for build in builds:
                # Ensure we don't double-count any builds
                if build in seen_builds:
                    continue

                seen_builds.add(build)

                if bom_item.sub_part.trackable:
                    # Trackable parts are allocated against the outputs
                    required_quantity = build.remaining * bom_item.quantity
                else:
                    # Non-trackable parts are allocated against the build itself
                    required_quantity = build.quantity * bom_item.quantity

                # Grab all allocations against the specified BomItem
                allocations = BuildItem.objects.filter(
                    build_line__bom_item=bom_item, build_line__build=build
                )

                # Total allocated for *this* part
                part_allocated_quantity = 0

                # Total allocated for *any* part
                total_allocated_quantity = 0

                for allocation in allocations:
                    total_allocated_quantity += allocation.quantity

                    if allocation.stock_item.part == part:
                        part_allocated_quantity += allocation.quantity

                speculative_quantity = 0

                # Consider the case where the build order is *not* fully allocated
                if required_quantity > total_allocated_quantity:
                    speculative_quantity = -1 * (
                        required_quantity - total_allocated_quantity
                    )

                add_schedule_entry(
                    build.target_date,
                    -part_allocated_quantity,
                    _('Stock required for Build Order'),
                    build,
                    speculative_quantity=speculative_quantity,
                )

        def compare(entry_1, entry_2):
            """Comparison function for sorting entries by date.

            Account for the fact that either date might be None
            """
            date_1 = entry_1['date']
            date_2 = entry_2['date']

            if date_1 is None:
                return -1
            elif date_2 is None:
                return 1

            return -1 if date_1 < date_2 else 1

        # Sort by incrementing date values
        schedules = sorted(schedule, key=functools.cmp_to_key(compare))

        serializers = part_serializers.PartSchedulingSerializer(
            schedules, many=True, context={'request': request}
        )

        return Response(serializers.data)


class PartRequirements(RetrieveAPI):
    """API endpoint detailing 'requirements' information for a particular part.

    This endpoint returns information on upcoming requirements for:

    - Sales Orders
    - Build Orders
    - Total requirements

    As this data is somewhat complex to calculate, is it not included in the default API
    """

    queryset = Part.objects.all()
    serializer_class = EmptySerializer

    def retrieve(self, request, *args, **kwargs):
        """Construct a response detailing Part requirements."""
        part = self.get_object()

        data = {
            'available_stock': part.available_stock,
            'on_order': part.on_order,
            'required_build_order_quantity': part.required_build_order_quantity(),
            'allocated_build_order_quantity': part.build_order_allocation_count(),
            'required_sales_order_quantity': part.required_sales_order_quantity(),
            'allocated_sales_order_quantity': part.sales_order_allocation_count(
                pending=True
            ),
        }

        data['allocated'] = (
            data['allocated_build_order_quantity']
            + data['allocated_sales_order_quantity']
        )
        data['required'] = (
            data['required_build_order_quantity']
            + data['required_sales_order_quantity']
        )

        return Response(data)


class PartPricingDetail(RetrieveUpdateAPI):
    """API endpoint for viewing part pricing data."""

    serializer_class = part_serializers.PartPricingSerializer
    queryset = Part.objects.all()

    def get_object(self):
        """Return the PartPricing object associated with the linked Part."""
        part = super().get_object()
        return part.pricing

    def _get_serializer(self, *args, **kwargs):
        """Return a part pricing serializer object."""
        part = self.get_object()
        kwargs['instance'] = part.pricing

        return self.serializer_class(**kwargs)


class PartSerialNumberDetail(RetrieveAPI):
    """API endpoint for returning extra serial number information about a particular part."""

    queryset = Part.objects.all()
    serializer_class = EmptySerializer

    def retrieve(self, request, *args, **kwargs):
        """Return serial number information for the referenced Part instance."""
        part = self.get_object()

        # Calculate the "latest" serial number
        latest_serial = part.get_latest_serial_number()
        next_serial = part.get_next_serial_number()

        data = {'latest': latest_serial, 'next': next_serial}

        return Response(data)


class PartCopyBOM(CreateAPI):
    """API endpoint for duplicating a BOM."""

    queryset = Part.objects.all()
    serializer_class = part_serializers.PartCopyBOMSerializer

    def get_serializer_context(self):
        """Add custom information to the serializer context for this endpoint."""
        ctx = super().get_serializer_context()

        try:
            ctx['part'] = Part.objects.get(pk=self.kwargs.get('pk', None))
        except Exception:
            pass

        return ctx


class PartValidateBOM(RetrieveUpdateAPI):
    """API endpoint for 'validating' the BOM for a given Part."""

    class BOMValidateSerializer(serializers.ModelSerializer):
        """Simple serializer class for validating a single BomItem instance."""

        class Meta:
            """Metaclass defines serializer fields."""

            model = Part
            fields = ['checksum', 'valid']

        checksum = serializers.CharField(read_only=True, source='bom_checksum')

        valid = serializers.BooleanField(
            write_only=True,
            default=False,
            label=_('Valid'),
            help_text=_('Validate entire Bill of Materials'),
        )

        def validate_valid(self, valid):
            """Check that the 'valid' input was flagged."""
            if not valid:
                raise ValidationError(_('This option must be selected'))

    queryset = Part.objects.all()

    serializer_class = BOMValidateSerializer

    def update(self, request, *args, **kwargs):
        """Validate the referenced BomItem instance."""
        part = self.get_object()

        partial = kwargs.pop('partial', False)

        # Clean up input data before using it
        data = self.clean_data(request.data)

        serializer = self.get_serializer(part, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)

        part.validate_bom(request.user)

        return Response({'checksum': part.bom_checksum})


class PartFilter(rest_filters.FilterSet):
    """Custom filters for the PartList endpoint.

    Uses the django_filters extension framework
    """

    class Meta:
        """Metaclass options for this filter set."""

        model = Part
        fields = ['revision_of']

    is_revision = rest_filters.BooleanFilter(
        label=_('Is Revision'), method='filter_is_revision'
    )

    def filter_is_revision(self, queryset, name, value):
        """Filter by whether the Part is a revision or not."""
        if str2bool(value):
            return queryset.exclude(revision_of=None)
        return queryset.filter(revision_of=None)

    has_revisions = rest_filters.BooleanFilter(
        label=_('Has Revisions'), method='filter_has_revisions'
    )

    def filter_has_revisions(self, queryset, name, value):
        """Filter by whether the Part has any revisions or not."""
        if str2bool(value):
            return queryset.exclude(revision_count=0)
        return queryset.filter(revision_count=0)

    has_units = rest_filters.BooleanFilter(label='Has units', method='filter_has_units')

    def filter_has_units(self, queryset, name, value):
        """Filter by whether the Part has units or not."""
        if str2bool(value):
            return queryset.exclude(Q(units=None) | Q(units=''))

        return queryset.filter(Q(units=None) | Q(units='')).distinct()

    # Filter by parts which have (or not) an IPN value
    has_ipn = rest_filters.BooleanFilter(label='Has IPN', method='filter_has_ipn')

    def filter_has_ipn(self, queryset, name, value):
        """Filter by whether the Part has an IPN (internal part number) or not."""
        if str2bool(value):
            return queryset.exclude(IPN='')
        return queryset.filter(IPN='')

    # Regex filter for name
    name_regex = rest_filters.CharFilter(
        label='Filter by name (regex)', field_name='name', lookup_expr='iregex'
    )

    # Exact match for IPN
    IPN = rest_filters.CharFilter(
        label='Filter by exact IPN (internal part number)',
        field_name='IPN',
        lookup_expr='iexact',
    )

    # Regex match for IPN
    IPN_regex = rest_filters.CharFilter(
        label='Filter by regex on IPN (internal part number)',
        field_name='IPN',
        lookup_expr='iregex',
    )

    # low_stock filter
    low_stock = rest_filters.BooleanFilter(label='Low stock', method='filter_low_stock')

    def filter_low_stock(self, queryset, name, value):
        """Filter by "low stock" status."""
        if str2bool(value):
            # Ignore any parts which do not have a specified 'minimum_stock' level
            # Filter items which have an 'in_stock' level lower than 'minimum_stock'
            return queryset.exclude(minimum_stock=0).filter(
                Q(total_in_stock__lt=F('minimum_stock'))
            )
        # Filter items which have an 'in_stock' level higher than 'minimum_stock'
        return queryset.filter(Q(total_in_stock__gte=F('minimum_stock')))

    # has_stock filter
    has_stock = rest_filters.BooleanFilter(label='Has stock', method='filter_has_stock')

    def filter_has_stock(self, queryset, name, value):
        """Filter by whether the Part has any stock."""
        if str2bool(value):
            return queryset.filter(Q(in_stock__gt=0))
        return queryset.filter(Q(in_stock__lte=0))

    # unallocated_stock filter
    unallocated_stock = rest_filters.BooleanFilter(
        label='Unallocated stock', method='filter_unallocated_stock'
    )

    def filter_unallocated_stock(self, queryset, name, value):
        """Filter by whether the Part has unallocated stock."""
        if str2bool(value):
            return queryset.filter(Q(unallocated_stock__gt=0))
        return queryset.filter(Q(unallocated_stock__lte=0))

    convert_from = rest_filters.ModelChoiceFilter(
        label='Can convert from',
        queryset=Part.objects.all(),
        method='filter_convert_from',
    )

    @extend_schema_field(OpenApiTypes.INT)
    def filter_convert_from(self, queryset, name, part):
        """Limit the queryset to valid conversion options for the specified part."""
        conversion_options = part.get_conversion_options()

        queryset = queryset.filter(pk__in=conversion_options)

        return queryset

    exclude_tree = rest_filters.ModelChoiceFilter(
        label='Exclude Part tree',
        queryset=Part.objects.all(),
        method='filter_exclude_tree',
    )

    @extend_schema_field(OpenApiTypes.INT)
    def filter_exclude_tree(self, queryset, name, part):
        """Exclude all parts and variants 'down' from the specified part from the queryset."""
        children = part.get_descendants(include_self=True)

        return queryset.exclude(id__in=children)

    ancestor = rest_filters.ModelChoiceFilter(
        label='Ancestor', queryset=Part.objects.all(), method='filter_ancestor'
    )

    @extend_schema_field(OpenApiTypes.INT)
    def filter_ancestor(self, queryset, name, part):
        """Limit queryset to descendants of the specified ancestor part."""
        descendants = part.get_descendants(include_self=False)
        return queryset.filter(id__in=descendants)

    variant_of = rest_filters.ModelChoiceFilter(
        label='Variant Of', queryset=Part.objects.all(), method='filter_variant_of'
    )

    def filter_variant_of(self, queryset, name, part):
        """Limit queryset to direct children (variants) of the specified part."""
        return queryset.filter(id__in=part.get_children())

    in_bom_for = rest_filters.ModelChoiceFilter(
        label='In BOM Of', queryset=Part.objects.all(), method='filter_in_bom'
    )

    @extend_schema_field(OpenApiTypes.INT)
    def filter_in_bom(self, queryset, name, part):
        """Limit queryset to parts in the BOM for the specified part."""
        bom_parts = part.get_parts_in_bom()
        return queryset.filter(id__in=[p.pk for p in bom_parts])

    has_pricing = rest_filters.BooleanFilter(
        label='Has Pricing', method='filter_has_pricing'
    )

    def filter_has_pricing(self, queryset, name, value):
        """Filter the queryset based on whether pricing information is available for the sub_part."""
        q_a = Q(pricing_data=None)
        q_b = Q(pricing_data__overall_min=None, pricing_data__overall_max=None)

        if str2bool(value):
            return queryset.exclude(q_a | q_b)

        return queryset.filter(q_a | q_b).distinct()

    stocktake = rest_filters.BooleanFilter(
        label='Has stocktake', method='filter_has_stocktake'
    )

    def filter_has_stocktake(self, queryset, name, value):
        """Filter the queryset based on whether stocktake data is available."""
        if str2bool(value):
            return queryset.exclude(last_stocktake=None)
        return queryset.filter(last_stocktake=None)

    stock_to_build = rest_filters.BooleanFilter(
        label='Required for Build Order', method='filter_stock_to_build'
    )

    def filter_stock_to_build(self, queryset, name, value):
        """Filter the queryset based on whether part stock is required for a pending BuildOrder."""
        if str2bool(value):
            # Return parts which are required for a build order, but have not yet been allocated
            return queryset.filter(
                required_for_build_orders__gt=F('allocated_to_build_orders')
            )
        # Return parts which are not required for a build order, or have already been allocated
        return queryset.filter(
            required_for_build_orders__lte=F('allocated_to_build_orders')
        )

    depleted_stock = rest_filters.BooleanFilter(
        label='Depleted Stock', method='filter_depleted_stock'
    )

    def filter_depleted_stock(self, queryset, name, value):
        """Filter the queryset based on whether the part is fully depleted of stock."""
        if str2bool(value):
            return queryset.filter(Q(in_stock=0) & ~Q(stock_item_count=0))
        return queryset.exclude(Q(in_stock=0) & ~Q(stock_item_count=0))

    default_location = rest_filters.ModelChoiceFilter(
        label='Default Location', queryset=StockLocation.objects.all()
    )

    bom_valid = rest_filters.BooleanFilter(
        label=_('BOM Valid'), method='filter_bom_valid'
    )

    def filter_bom_valid(self, queryset, name, value):
        """Filter by whether the BOM for the part is valid or not."""
        # Limit queryset to active assemblies
        queryset = queryset.filter(active=True, assembly=True).distinct()

        # Iterate through the queryset
        # TODO: We should cache BOM checksums to make this process more efficient
        pks = []

        for item in queryset:
            if item.is_bom_valid() == value:
                pks.append(item.pk)

        return queryset.filter(pk__in=pks)

    starred = rest_filters.BooleanFilter(label='Starred', method='filter_starred')

    def filter_starred(self, queryset, name, value):
        """Filter by whether the Part is 'starred' by the current user."""
        if self.request.user.is_anonymous:
            return queryset

        starred_parts = [
            star.part.pk
            for star in self.request.user.starred_parts.all().prefetch_related('part')
        ]

        if value:
            return queryset.filter(pk__in=starred_parts)
        else:
            return queryset.exclude(pk__in=starred_parts)

    is_template = rest_filters.BooleanFilter()

    assembly = rest_filters.BooleanFilter()

    component = rest_filters.BooleanFilter()

    trackable = rest_filters.BooleanFilter()

    testable = rest_filters.BooleanFilter()

    purchaseable = rest_filters.BooleanFilter()

    salable = rest_filters.BooleanFilter()

    active = rest_filters.BooleanFilter()

    locked = rest_filters.BooleanFilter()

    virtual = rest_filters.BooleanFilter()

    tags_name = rest_filters.CharFilter(field_name='tags__name', lookup_expr='iexact')

    tags_slug = rest_filters.CharFilter(field_name='tags__slug', lookup_expr='iexact')

    # Created date filters
    created_before = InvenTreeDateFilter(
        label='Updated before', field_name='creation_date', lookup_expr='lt'
    )
    created_after = InvenTreeDateFilter(
        label='Updated after', field_name='creation_date', lookup_expr='gt'
    )


class PartMixin:
    """Mixin class for Part API endpoints."""

    serializer_class = part_serializers.PartSerializer
    queryset = Part.objects.all()

    starred_parts = None
    is_create = False

    def get_queryset(self, *args, **kwargs):
        """Return an annotated queryset object for the PartDetail endpoint."""
        queryset = super().get_queryset(*args, **kwargs)

        queryset = part_serializers.PartSerializer.annotate_queryset(queryset)

        # Annotate with parameter template data?
        if str2bool(self.request.query_params.get('parameters', False)):
            queryset = queryset.prefetch_related('parameters', 'parameters__template')

        return queryset

    def get_serializer(self, *args, **kwargs):
        """Return a serializer instance for this endpoint."""
        # Ensure the request context is passed through
        kwargs['context'] = self.get_serializer_context()

        # Indicate that we can create a new Part via this endpoint
        kwargs['create'] = self.is_create

        # Pass a list of "starred" parts to the current user to the serializer
        # We do this to reduce the number of database queries required!
        if (
            self.starred_parts is None
            and self.request is not None
            and hasattr(self.request.user, 'starred_parts')
        ):
            self.starred_parts = [
                star.part for star in self.request.user.starred_parts.all()
            ]

        kwargs['starred_parts'] = self.starred_parts

        try:
            params = self.request.query_params

            kwargs['parameters'] = str2bool(params.get('parameters', None))
            kwargs['category_detail'] = str2bool(params.get('category_detail', False))
            kwargs['location_detail'] = str2bool(params.get('location_detail', False))
            kwargs['path_detail'] = str2bool(params.get('path_detail', False))

        except AttributeError:
            pass

        return self.serializer_class(*args, **kwargs)

    def get_serializer_context(self):
        """Extend serializer context data."""
        context = super().get_serializer_context()
        context['request'] = self.request

        return context


class PartList(PartMixin, DataExportViewMixin, ListCreateAPI):
    """API endpoint for accessing a list of Part objects, or creating a new Part instance."""

    filterset_class = PartFilter
    is_create = True

    def filter_queryset(self, queryset):
        """Perform custom filtering of the queryset."""
        params = self.request.query_params

        queryset = super().filter_queryset(queryset)

        # Exclude specific part ID values?
        exclude_id = []

        for key in ['exclude_id', 'exclude_id[]']:
            if key in params:
                exclude_id += params.getlist(key, [])

        if exclude_id:
            id_values = []

            for val in exclude_id:
                try:
                    # pk values must be integer castable
                    val = int(val)
                    id_values.append(val)
                except ValueError:
                    pass

            queryset = queryset.exclude(pk__in=id_values)

        # Filter by 'related' parts?
        related = params.get('related', None)
        exclude_related = params.get('exclude_related', None)

        if related is not None or exclude_related is not None:
            try:
                pk = related if related is not None else exclude_related
                pk = int(pk)

                related_part = Part.objects.get(pk=pk)

                part_ids = set()

                # Return any relationship which points to the part in question
                relation_filter = Q(part_1=related_part) | Q(part_2=related_part)

                for relation in PartRelated.objects.filter(relation_filter).distinct():
                    if relation.part_1.pk != pk:
                        part_ids.add(relation.part_1.pk)

                    if relation.part_2.pk != pk:
                        part_ids.add(relation.part_2.pk)

                if related is not None:
                    # Only return related results
                    queryset = queryset.filter(pk__in=list(part_ids))
                elif exclude_related is not None:
                    # Exclude related results
                    queryset = queryset.exclude(pk__in=list(part_ids))

            except (ValueError, Part.DoesNotExist):
                pass

        # Cascade? (Default = True)
        cascade = str2bool(params.get('cascade', True))

        # Does the user wish to filter by category?
        cat_id = params.get('category', None)

        if cat_id is not None:
            # Category has been specified!
            if isNull(cat_id):
                # A 'null' category is the top-level category
                if not cascade:
                    # Do not cascade, only list parts in the top-level category
                    queryset = queryset.filter(category=None)

            else:
                try:
                    category = PartCategory.objects.get(pk=cat_id)

                    # If '?cascade=true' then include parts which exist in sub-categories
                    if cascade:
                        queryset = queryset.filter(
                            category__in=category.getUniqueChildren()
                        )
                    # Just return parts directly in the requested category
                    else:
                        queryset = queryset.filter(category=cat_id)
                except (ValueError, PartCategory.DoesNotExist):
                    pass

        queryset = self.filter_parametric_data(queryset)

        return queryset

    def filter_parametric_data(self, queryset):
        """Filter queryset against part parameters.

        Here we can perform a number of different functions:

        Ordering Based on Parameter Value:
        - Used if the 'ordering' query param points to a parameter
        - e.g. '&ordering=param_<id>' where <id> specifies the PartParameterTemplate
        - Only parts which have a matching parameter are returned
        - Queryset is ordered based on parameter value
        """
        # Extract "ordering" parameter from query args
        ordering = self.request.query_params.get('ordering', None)

        if ordering:
            # Ordering value must match required regex pattern
            result = re.match(r'^\-?parameter_(\d+)$', ordering)

            if result:
                template_id = result.group(1)
                ascending = not ordering.startswith('-')
                queryset = part.filters.order_by_parameter(
                    queryset, template_id, ascending
                )

        return queryset

    filter_backends = SEARCH_ORDER_FILTER_ALIAS

    ordering_fields = [
        'name',
        'creation_date',
        'IPN',
        'in_stock',
        'total_in_stock',
        'unallocated_stock',
        'category',
        'default_location',
        'last_stocktake',
        'units',
        'pricing_min',
        'pricing_max',
        'pricing_updated',
        'revision',
        'revision_count',
    ]

    ordering_field_aliases = {
        'pricing_min': 'pricing_data__overall_min',
        'pricing_max': 'pricing_data__overall_max',
        'pricing_updated': 'pricing_data__updated',
    }

    # Default ordering
    ordering = 'name'

    search_fields = [
        'name',
        'description',
        'IPN',
        'revision',
        'keywords',
        'category__name',
        'manufacturer_parts__MPN',
        'supplier_parts__SKU',
        'tags__name',
        'tags__slug',
    ]


class PartChangeCategory(CreateAPI):
    """API endpoint to change the location of multiple parts in bulk."""

    serializer_class = part_serializers.PartSetCategorySerializer
    queryset = Part.objects.none()


class PartDetail(PartMixin, RetrieveUpdateDestroyAPI):
    """API endpoint for detail view of a single Part object."""

    def update(self, request, *args, **kwargs):
        """Custom update functionality for Part instance.

        - If the 'starred' field is provided, update the 'starred' status against current user
        """
        # Clean input data
        data = self.clean_data(request.data)

        if 'starred' in data:
            starred = str2bool(data.get('starred', False))

            self.get_object().set_starred(
                request.user, starred, include_variants=False, include_categories=False
            )

        response = super().update(request, *args, **kwargs)

        return response


class PartRelatedFilter(rest_filters.FilterSet):
    """FilterSet for PartRelated objects."""

    class Meta:
        """Metaclass options."""

        model = PartRelated
        fields = ['part_1', 'part_2']

    part = rest_filters.ModelChoiceFilter(
        queryset=Part.objects.all(), method='filter_part', label=_('Part')
    )

    def filter_part(self, queryset, name, part):
        """Filter queryset to include only PartRelated objects which reference the specified part."""
        return queryset.filter(Q(part_1=part) | Q(part_2=part)).distinct()


class PartRelatedMixin:
    """Mixin class for PartRelated API endpoints."""

    queryset = PartRelated.objects.all()
    serializer_class = part_serializers.PartRelationSerializer

    def get_queryset(self, *args, **kwargs):
        """Return an annotated queryset for the PartRelatedDetail endpoint."""
        queryset = super().get_queryset(*args, **kwargs)

        queryset = queryset.prefetch_related('part_1', 'part_2')

        return queryset


class PartRelatedList(PartRelatedMixin, ListCreateAPI):
    """API endpoint for accessing a list of PartRelated objects."""

    filterset_class = PartRelatedFilter
    filter_backends = SEARCH_ORDER_FILTER

    search_fields = ['part_1__name', 'part_2__name']


class PartRelatedDetail(PartRelatedMixin, RetrieveUpdateDestroyAPI):
    """API endpoint for accessing detail view of a PartRelated object."""


class PartParameterTemplateFilter(rest_filters.FilterSet):
    """FilterSet for PartParameterTemplate objects."""

    class Meta:
        """Metaclass options."""

        model = PartParameterTemplate

        # Simple filter fields
        fields = ['name', 'units', 'checkbox']

    has_choices = rest_filters.BooleanFilter(
        method='filter_has_choices', label='Has Choice'
    )

    def filter_has_choices(self, queryset, name, value):
        """Filter queryset to include only PartParameterTemplates with choices."""
        if str2bool(value):
            return queryset.exclude(Q(choices=None) | Q(choices=''))

        return queryset.filter(Q(choices=None) | Q(choices='')).distinct()

    has_units = rest_filters.BooleanFilter(method='filter_has_units', label='Has Units')

    def filter_has_units(self, queryset, name, value):
        """Filter queryset to include only PartParameterTemplates with units."""
        if str2bool(value):
            return queryset.exclude(Q(units=None) | Q(units=''))

        return queryset.filter(Q(units=None) | Q(units='')).distinct()

    part = rest_filters.ModelChoiceFilter(
        queryset=Part.objects.all(), method='filter_part', label=_('Part')
    )

    @extend_schema_field(OpenApiTypes.INT)
    def filter_part(self, queryset, name, part):
        """Filter queryset to include only PartParameterTemplates which are referenced by a part."""
        parameters = PartParameter.objects.filter(part=part)
        template_ids = parameters.values_list('template').distinct()
        return queryset.filter(pk__in=[el[0] for el in template_ids])

    # Filter against a "PartCategory" - return only parameter templates which are referenced by parts in this category
    category = rest_filters.ModelChoiceFilter(
        queryset=PartCategory.objects.all(),
        method='filter_category',
        label=_('Category'),
    )

    @extend_schema_field(OpenApiTypes.INT)
    def filter_category(self, queryset, name, category):
        """Filter queryset to include only PartParameterTemplates which are referenced by parts in this category."""
        cats = category.get_descendants(include_self=True)
        parameters = PartParameter.objects.filter(part__category__in=cats)
        template_ids = parameters.values_list('template').distinct()
        return queryset.filter(pk__in=[el[0] for el in template_ids])


class PartParameterTemplateMixin:
    """Mixin class for PartParameterTemplate API endpoints."""

    queryset = PartParameterTemplate.objects.all()
    serializer_class = part_serializers.PartParameterTemplateSerializer

    def get_queryset(self, *args, **kwargs):
        """Return an annotated queryset for the PartParameterTemplateDetail endpoint."""
        queryset = super().get_queryset(*args, **kwargs)

        queryset = part_serializers.PartParameterTemplateSerializer.annotate_queryset(
            queryset
        )

        return queryset


class PartParameterTemplateList(
    PartParameterTemplateMixin, DataExportViewMixin, ListCreateAPI
):
    """API endpoint for accessing a list of PartParameterTemplate objects.

    - GET: Return list of PartParameterTemplate objects
    - POST: Create a new PartParameterTemplate object
    """

    filterset_class = PartParameterTemplateFilter

    filter_backends = SEARCH_ORDER_FILTER

    search_fields = ['name', 'description']

    ordering_fields = ['name', 'units', 'checkbox', 'parts']


class PartParameterTemplateDetail(PartParameterTemplateMixin, RetrieveUpdateDestroyAPI):
    """API endpoint for accessing the detail view for a PartParameterTemplate object."""


class PartParameterAPIMixin:
    """Mixin class for PartParameter API endpoints."""

    queryset = PartParameter.objects.all()
    serializer_class = part_serializers.PartParameterSerializer

    def get_queryset(self, *args, **kwargs):
        """Override get_queryset method to prefetch related fields."""
        queryset = super().get_queryset(*args, **kwargs)
        queryset = queryset.prefetch_related('part', 'template')
        return queryset

    def get_serializer(self, *args, **kwargs):
        """Return the serializer instance for this API endpoint.

        If requested, extra detail fields are annotated to the queryset:
        - part_detail
        - template_detail
        """
        try:
            kwargs['part_detail'] = str2bool(self.request.GET.get('part_detail', False))
            kwargs['template_detail'] = str2bool(
                self.request.GET.get('template_detail', True)
            )
        except AttributeError:
            pass

        return self.serializer_class(*args, **kwargs)


class PartParameterFilter(rest_filters.FilterSet):
    """Custom filters for the PartParameterList API endpoint."""

    class Meta:
        """Metaclass options for the filterset."""

        model = PartParameter
        fields = ['template']

    part = rest_filters.ModelChoiceFilter(
        queryset=Part.objects.all(), method='filter_part'
    )

    def filter_part(self, queryset, name, part):
        """Filter against the provided part.

        If 'include_variants' query parameter is provided, filter against variant parts also
        """
        try:
            include_variants = str2bool(self.request.GET.get('include_variants', False))
        except AttributeError:
            include_variants = False

        if include_variants:
            return queryset.filter(part__in=part.get_descendants(include_self=True))
        else:
            return queryset.filter(part=part)


class PartParameterList(PartParameterAPIMixin, DataExportViewMixin, ListCreateAPI):
    """API endpoint for accessing a list of PartParameter objects.

    - GET: Return list of PartParameter objects
    - POST: Create a new PartParameter object
    """

    filterset_class = PartParameterFilter

    filter_backends = SEARCH_ORDER_FILTER_ALIAS

    ordering_fields = ['name', 'data', 'part', 'template']

    ordering_field_aliases = {
        'name': 'template__name',
        'units': 'template__units',
        'data': ['data_numeric', 'data'],
        'part': 'part__name',
    }

    search_fields = [
        'data',
        'template__name',
        'template__description',
        'template__units',
    ]


class PartParameterDetail(PartParameterAPIMixin, RetrieveUpdateDestroyAPI):
    """API endpoint for detail view of a single PartParameter object."""


class PartStocktakeFilter(rest_filters.FilterSet):
    """Custom filter for the PartStocktakeList endpoint."""

    class Meta:
        """Metaclass options."""

        model = PartStocktake
        fields = ['part', 'user']


class PartStocktakeList(ListCreateAPI):
    """API endpoint for listing part stocktake information."""

    queryset = PartStocktake.objects.all()
    serializer_class = part_serializers.PartStocktakeSerializer
    filterset_class = PartStocktakeFilter

    def get_serializer_context(self):
        """Extend serializer context data."""
        context = super().get_serializer_context()
        context['request'] = self.request

        return context

    filter_backends = ORDER_FILTER

    ordering_fields = ['part', 'item_count', 'quantity', 'date', 'user', 'pk']

    # Reverse date ordering by default
    ordering = '-pk'


class PartStocktakeDetail(RetrieveUpdateDestroyAPI):
    """Detail API endpoint for a single PartStocktake instance.

    Note: Only staff (admin) users can access this endpoint.
    """

    queryset = PartStocktake.objects.all()
    serializer_class = part_serializers.PartStocktakeSerializer


class PartStocktakeReportList(ListAPI):
    """API endpoint for listing part stocktake report information."""

    queryset = PartStocktakeReport.objects.all()
    serializer_class = part_serializers.PartStocktakeReportSerializer

    filter_backends = ORDER_FILTER

    ordering_fields = ['date', 'pk']

    # Newest first, by default
    ordering = '-pk'


class PartStocktakeReportDetail(RetrieveUpdateDestroyAPI):
    """API endpoint for detail view of a single PartStocktakeReport object."""

    queryset = PartStocktakeReport.objects.all()
    serializer_class = part_serializers.PartStocktakeReportSerializer


class PartStocktakeReportGenerate(CreateAPI):
    """API endpoint for manually generating a new PartStocktakeReport."""

    serializer_class = part_serializers.PartStocktakeReportGenerateSerializer

    permission_classes = [permissions.IsAuthenticated, RolePermission]

    role_required = 'stocktake'

    def get_serializer_context(self):
        """Extend serializer context data."""
        context = super().get_serializer_context()
        context['request'] = self.request

        return context


class BomFilter(rest_filters.FilterSet):
    """Custom filters for the BOM list."""

    class Meta:
        """Metaclass options."""

        model = BomItem
        fields = ['optional', 'consumable', 'inherited', 'allow_variants', 'validated']

    # Filters for linked 'part'
    part_active = rest_filters.BooleanFilter(
        label='Assembly part is active', field_name='part__active'
    )

    part_trackable = rest_filters.BooleanFilter(
        label='Assembly part is trackable', field_name='part__trackable'
    )

    part_testable = rest_filters.BooleanFilter(
        label=_('Assembly part is testable'), field_name='part__testable'
    )

    # Filters for linked 'sub_part'
    sub_part_trackable = rest_filters.BooleanFilter(
        label='Component part is trackable', field_name='sub_part__trackable'
    )

    sub_part_testable = rest_filters.BooleanFilter(
        label=_('Component part is testable'), field_name='sub_part__testable'
    )

    sub_part_assembly = rest_filters.BooleanFilter(
        label='Component part is an assembly', field_name='sub_part__assembly'
    )

    available_stock = rest_filters.BooleanFilter(
        label='Has available stock', method='filter_available_stock'
    )

    def filter_available_stock(self, queryset, name, value):
        """Filter the queryset based on whether each line item has any available stock."""
        if str2bool(value):
            return queryset.filter(available_stock__gt=0)
        return queryset.filter(available_stock=0)

    on_order = rest_filters.BooleanFilter(label='On order', method='filter_on_order')

    def filter_on_order(self, queryset, name, value):
        """Filter the queryset based on whether each line item has any stock on order."""
        if str2bool(value):
            return queryset.filter(on_order__gt=0)
        return queryset.filter(on_order=0)

    has_pricing = rest_filters.BooleanFilter(
        label='Has Pricing', method='filter_has_pricing'
    )

    def filter_has_pricing(self, queryset, name, value):
        """Filter the queryset based on whether pricing information is available for the sub_part."""
        q_a = Q(sub_part__pricing_data=None)
        q_b = Q(
            sub_part__pricing_data__overall_min=None,
            sub_part__pricing_data__overall_max=None,
        )

        if str2bool(value):
            return queryset.exclude(q_a | q_b)

        return queryset.filter(q_a | q_b).distinct()

    part = rest_filters.ModelChoiceFilter(
        queryset=Part.objects.all(), method='filter_part', label=_('Part')
    )

    def filter_part(self, queryset, name, part):
        """Filter the queryset based on the specified part."""
        return queryset.filter(part.get_bom_item_filter())

    uses = rest_filters.ModelChoiceFilter(
        queryset=Part.objects.all(), method='filter_uses', label=_('Uses')
    )

    @extend_schema_field(OpenApiTypes.INT)
    def filter_uses(self, queryset, name, part):
        """Filter the queryset based on the specified part."""
        return queryset.filter(part.get_used_in_bom_item_filter())


class BomMixin:
    """Mixin class for BomItem API endpoints."""

    serializer_class = part_serializers.BomItemSerializer
    queryset = BomItem.objects.all()

    def get_serializer(self, *args, **kwargs):
        """Return the serializer instance for this API endpoint.

        If requested, extra detail fields are annotated to the queryset:
        - part_detail
        - sub_part_detail
        """
        # Do we wish to include extra detail?
        try:
            kwargs['part_detail'] = str2bool(self.request.GET.get('part_detail', None))
        except AttributeError:
            pass

        try:
            kwargs['sub_part_detail'] = str2bool(
                self.request.GET.get('sub_part_detail', None)
            )
        except AttributeError:
            pass

        # Ensure the request context is passed through!
        kwargs['context'] = self.get_serializer_context()

        return self.serializer_class(*args, **kwargs)

    def get_queryset(self, *args, **kwargs):
        """Return the queryset object for this endpoint."""
        queryset = super().get_queryset(*args, **kwargs)

        queryset = self.get_serializer_class().setup_eager_loading(queryset)
        queryset = self.get_serializer_class().annotate_queryset(queryset)

        return queryset


class BomList(BomMixin, DataExportViewMixin, ListCreateDestroyAPIView):
    """API endpoint for accessing a list of BomItem objects.

    - GET: Return list of BomItem objects
    - POST: Create a new BomItem object
    """

    filterset_class = BomFilter
    filter_backends = SEARCH_ORDER_FILTER_ALIAS

    search_fields = [
        'reference',
        'sub_part__name',
        'sub_part__description',
        'sub_part__IPN',
        'sub_part__revision',
        'sub_part__keywords',
        'sub_part__category__name',
    ]

    ordering_fields = [
        'can_build',
        'quantity',
        'sub_part',
        'available_stock',
        'allow_variants',
        'inherited',
        'optional',
        'consumable',
        'reference',
        'validated',
        'pricing_min',
        'pricing_max',
        'pricing_min_total',
        'pricing_max_total',
        'pricing_updated',
    ]

    ordering_field_aliases = {
        'sub_part': 'sub_part__name',
        'pricing_min': 'sub_part__pricing_data__overall_min',
        'pricing_max': 'sub_part__pricing_data__overall_max',
        'pricing_updated': 'sub_part__pricing_data__updated',
    }

    def validate_delete(self, queryset, request) -> None:
        """Ensure that there are no 'locked' items."""
        for bom_item in queryset:
            # Note: Calling check_part_lock may raise a ValidationError
            bom_item.check_part_lock(bom_item.part)


class BomDetail(BomMixin, RetrieveUpdateDestroyAPI):
    """API endpoint for detail view of a single BomItem object."""


class BomImportUpload(CreateAPI):
    """API endpoint for uploading a complete Bill of Materials.

    It is assumed that the BOM has been extracted from a file using the BomExtract endpoint.
    """

    queryset = Part.objects.all()
    serializer_class = part_serializers.BomImportUploadSerializer

    def create(self, request, *args, **kwargs):
        """Custom create function to return the extracted data."""
        # Clean up input data
        data = self.clean_data(request.data)

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)

        data = serializer.extract_data()

        return Response(data, status=status.HTTP_201_CREATED, headers=headers)


class BomImportExtract(CreateAPI):
    """API endpoint for extracting BOM data from a BOM file."""

    queryset = Part.objects.none()
    serializer_class = part_serializers.BomImportExtractSerializer


class BomImportSubmit(CreateAPI):
    """API endpoint for submitting BOM data from a BOM file."""

    queryset = BomItem.objects.none()
    serializer_class = part_serializers.BomImportSubmitSerializer


class BomItemValidate(UpdateAPI):
    """API endpoint for validating a BomItem."""

    class BomItemValidationSerializer(serializers.Serializer):
        """Simple serializer for passing a single boolean field."""

        valid = serializers.BooleanField(default=False)

    queryset = BomItem.objects.all()
    serializer_class = BomItemValidationSerializer

    def update(self, request, *args, **kwargs):
        """Perform update request."""
        partial = kwargs.pop('partial', False)

        # Clean up input data
        data = self.clean_data(request.data)
        valid = data.get('valid', False)

        instance = self.get_object()

        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)

        if isinstance(instance, BomItem):
            instance.validate_hash(valid)

        return Response(serializer.data)


class BomItemSubstituteList(ListCreateAPI):
    """API endpoint for accessing a list of BomItemSubstitute objects."""

    serializer_class = part_serializers.BomItemSubstituteSerializer
    queryset = BomItemSubstitute.objects.all()

    filter_backends = SEARCH_ORDER_FILTER

    filterset_fields = ['part', 'bom_item']


class BomItemSubstituteDetail(RetrieveUpdateDestroyAPI):
    """API endpoint for detail view of a single BomItemSubstitute object."""

    queryset = BomItemSubstitute.objects.all()
    serializer_class = part_serializers.BomItemSubstituteSerializer


part_api_urls = [
    # Base URL for PartCategory API endpoints
    path(
        'category/',
        include([
            path('tree/', CategoryTree.as_view(), name='api-part-category-tree'),
            path(
                'parameters/',
                include([
                    path(
                        '<int:pk>/',
                        include([
                            path(
                                'metadata/',
                                MetadataView.as_view(),
                                {'model': PartCategoryParameterTemplate},
                                name='api-part-category-parameter-metadata',
                            ),
                            path(
                                '',
                                CategoryParameterDetail.as_view(),
                                name='api-part-category-parameter-detail',
                            ),
                        ]),
                    ),
                    path(
                        '',
                        CategoryParameterList.as_view(),
                        name='api-part-category-parameter-list',
                    ),
                ]),
            ),
            # Category detail endpoints
            path(
                '<int:pk>/',
                include([
                    path(
                        'metadata/',
                        MetadataView.as_view(),
                        {'model': PartCategory},
                        name='api-part-category-metadata',
                    ),
                    # PartCategory detail endpoint
                    path('', CategoryDetail.as_view(), name='api-part-category-detail'),
                ]),
            ),
            path('', CategoryList.as_view(), name='api-part-category-list'),
        ]),
    ),
    # Base URL for PartTestTemplate API endpoints
    path(
        'test-template/',
        include([
            path(
                '<int:pk>/',
                include([
                    path(
                        'metadata/',
                        MetadataView.as_view(),
                        {'model': PartTestTemplate},
                        name='api-part-test-template-metadata',
                    ),
                    path(
                        '',
                        PartTestTemplateDetail.as_view(),
                        name='api-part-test-template-detail',
                    ),
                ]),
            ),
            path(
                '', PartTestTemplateList.as_view(), name='api-part-test-template-list'
            ),
        ]),
    ),
    # Base URL for part sale pricing
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
    # Base URL for part internal pricing
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
    # Base URL for PartRelated API endpoints
    path(
        'related/',
        include([
            path(
                '<int:pk>/',
                include([
                    path(
                        'metadata/',
                        MetadataView.as_view(),
                        {'model': PartRelated},
                        name='api-part-related-metadata',
                    ),
                    path(
                        '', PartRelatedDetail.as_view(), name='api-part-related-detail'
                    ),
                ]),
            ),
            path('', PartRelatedList.as_view(), name='api-part-related-list'),
        ]),
    ),
    # Base URL for PartParameter API endpoints
    path(
        'parameter/',
        include([
            path(
                'template/',
                include([
                    path(
                        '<int:pk>/',
                        include([
                            path(
                                'metadata/',
                                MetadataView.as_view(),
                                {'model': PartParameterTemplate},
                                name='api-part-parameter-template-metadata',
                            ),
                            path(
                                '',
                                PartParameterTemplateDetail.as_view(),
                                name='api-part-parameter-template-detail',
                            ),
                        ]),
                    ),
                    path(
                        '',
                        PartParameterTemplateList.as_view(),
                        name='api-part-parameter-template-list',
                    ),
                ]),
            ),
            path(
                '<int:pk>/',
                include([
                    path(
                        'metadata/',
                        MetadataView.as_view(),
                        {'model': PartParameter},
                        name='api-part-parameter-metadata',
                    ),
                    path(
                        '',
                        PartParameterDetail.as_view(),
                        name='api-part-parameter-detail',
                    ),
                ]),
            ),
            path('', PartParameterList.as_view(), name='api-part-parameter-list'),
        ]),
    ),
    # Part stocktake data
    path(
        'stocktake/',
        include([
            path(
                r'report/',
                include([
                    path(
                        'generate/',
                        PartStocktakeReportGenerate.as_view(),
                        name='api-part-stocktake-report-generate',
                    ),
                    path(
                        '<int:pk>/',
                        PartStocktakeReportDetail.as_view(),
                        name='api-part-stocktake-report-detail',
                    ),
                    path(
                        '',
                        PartStocktakeReportList.as_view(),
                        name='api-part-stocktake-report-list',
                    ),
                ]),
            ),
            path(
                '<int:pk>/',
                PartStocktakeDetail.as_view(),
                name='api-part-stocktake-detail',
            ),
            path('', PartStocktakeList.as_view(), name='api-part-stocktake-list'),
        ]),
    ),
    path(
        'thumbs/',
        include([
            path('', PartThumbs.as_view(), name='api-part-thumbs'),
            re_path(
                r'^(?P<pk>\d+)/?',
                PartThumbsUpdate.as_view(),
                name='api-part-thumbs-update',
            ),
        ]),
    ),
    path(
        '<int:pk>/',
        include([
            # Endpoint for extra serial number information
            path(
                'serial-numbers/',
                PartSerialNumberDetail.as_view(),
                name='api-part-serial-number-detail',
            ),
            # Endpoint for future scheduling information
            path('scheduling/', PartScheduling.as_view(), name='api-part-scheduling'),
            path(
                'requirements/',
                PartRequirements.as_view(),
                name='api-part-requirements',
            ),
            # Endpoint for duplicating a BOM for the specific Part
            path('bom-copy/', PartCopyBOM.as_view(), name='api-part-bom-copy'),
            # Endpoint for validating a BOM for the specific Part
            path(
                'bom-validate/', PartValidateBOM.as_view(), name='api-part-bom-validate'
            ),
            # Part metadata
            path(
                'metadata/',
                MetadataView.as_view(),
                {'model': Part},
                name='api-part-metadata',
            ),
            # Part pricing
            path('pricing/', PartPricingDetail.as_view(), name='api-part-pricing'),
            # Part detail endpoint
            path('', PartDetail.as_view(), name='api-part-detail'),
        ]),
    ),
    path(
        'change_category/',
        PartChangeCategory.as_view(),
        name='api-part-change-category',
    ),
    path('', PartList.as_view(), name='api-part-list'),
]

bom_api_urls = [
    path(
        'substitute/',
        include([
            # Detail view
            path(
                '<int:pk>/',
                include([
                    path(
                        'metadata/',
                        MetadataView.as_view(),
                        {'model': BomItemSubstitute},
                        name='api-bom-substitute-metadata',
                    ),
                    path(
                        '',
                        BomItemSubstituteDetail.as_view(),
                        name='api-bom-substitute-detail',
                    ),
                ]),
            ),
            # Catch all
            path('', BomItemSubstituteList.as_view(), name='api-bom-substitute-list'),
        ]),
    ),
    # BOM Item Detail
    path(
        '<int:pk>/',
        include([
            path('validate/', BomItemValidate.as_view(), name='api-bom-item-validate'),
            path(
                'metadata/',
                MetadataView.as_view(),
                {'model': BomItem},
                name='api-bom-item-metadata',
            ),
            path('', BomDetail.as_view(), name='api-bom-item-detail'),
        ]),
    ),
    # API endpoint URLs for importing BOM data
    path('import/upload/', BomImportUpload.as_view(), name='api-bom-import-upload'),
    path('import/extract/', BomImportExtract.as_view(), name='api-bom-import-extract'),
    path('import/submit/', BomImportSubmit.as_view(), name='api-bom-import-submit'),
    # Catch-all
    path('', BomList.as_view(), name='api-bom-list'),
]
