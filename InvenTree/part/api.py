"""Provides a JSON API for the Part app."""

import functools
import re

from django.db.models import Count, F, Q
from django.http import JsonResponse
from django.urls import include, path, re_path
from django.utils.translation import gettext_lazy as _

from django_filters import rest_framework as rest_filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, serializers, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

import order.models
import part.filters
from build.models import Build, BuildItem
from InvenTree.api import (
    APIDownloadMixin,
    AttachmentMixin,
    ListCreateDestroyAPIView,
    MetadataView,
)
from InvenTree.filters import (
    ORDER_FILTER,
    SEARCH_ORDER_FILTER,
    SEARCH_ORDER_FILTER_ALIAS,
    InvenTreeDateFilter,
    InvenTreeSearchFilter,
)
from InvenTree.helpers import (
    DownloadFile,
    increment_serial_number,
    is_ajax,
    isNull,
    str2bool,
    str2int,
)
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
from InvenTree.status_codes import (
    BuildStatusGroups,
    PurchaseOrderStatusGroups,
    SalesOrderStatusGroups,
)
from part.admin import PartCategoryResource, PartResource
from stock.models import StockLocation

from . import serializers as part_serializers
from . import views
from .models import (
    BomItem,
    BomItemSubstitute,
    Part,
    PartAttachment,
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


class CategoryList(CategoryMixin, APIDownloadMixin, ListCreateAPI):
    """API endpoint for accessing a list of PartCategory objects.

    - GET: Return a list of PartCategory objects
    - POST: Create a new PartCategory object
    """

    def download_queryset(self, queryset, export_format):
        """Download the filtered queryset as a data file."""
        dataset = PartCategoryResource().export(queryset=queryset)
        filedata = dataset.export(export_format)
        filename = f'InvenTree_Categories.{export_format}'

        return DownloadFile(filedata, filename)

    def filter_queryset(self, queryset):
        """Custom filtering.

        Rules:
        - Allow filtering by "null" parent to retrieve top-level part categories
        """
        queryset = super().filter_queryset(queryset)

        params = self.request.query_params

        cat_id = params.get('parent', None)

        cascade = str2bool(params.get('cascade', False))

        depth = str2int(params.get('depth', None))

        # Do not filter by category
        if cat_id is None:
            pass
        # Look for top-level categories
        elif isNull(cat_id):
            if not cascade:
                queryset = queryset.filter(parent=None)

            if cascade and depth is not None:
                queryset = queryset.filter(level__lte=depth)

        else:
            try:
                category = PartCategory.objects.get(pk=cat_id)

                if cascade:
                    parents = category.get_descendants(include_self=True)
                    if depth is not None:
                        parents = parents.filter(level__lte=category.level + depth)

                    parent_ids = [p.id for p in parents]

                    queryset = queryset.filter(parent__in=parent_ids)
                else:
                    queryset = queryset.filter(parent=category)

            except (ValueError, PartCategory.DoesNotExist):
                pass

        # Exclude PartCategory tree
        exclude_tree = params.get('exclude_tree', None)

        if exclude_tree is not None:
            try:
                cat = PartCategory.objects.get(pk=exclude_tree)

                queryset = queryset.exclude(
                    pk__in=[c.pk for c in cat.get_descendants(include_self=True)]
                )

            except (ValueError, PartCategory.DoesNotExist):
                pass

        # Filter by "starred" status
        starred = params.get('starred', None)

        if starred is not None:
            starred = str2bool(starred)
            starred_categories = [
                star.category.pk for star in self.request.user.starred_categories.all()
            ]

            if starred:
                queryset = queryset.filter(pk__in=starred_categories)
            else:
                queryset = queryset.exclude(pk__in=starred_categories)

        return queryset

    filter_backends = SEARCH_ORDER_FILTER

    filterset_fields = ['name', 'description', 'structural']

    ordering_fields = ['name', 'pathstring', 'level', 'tree_id', 'lft', 'part_count']

    # Use hierarchical ordering by default
    ordering = ['tree_id', 'lft', 'name']

    search_fields = ['name', 'description']


class CategoryDetail(CategoryMixin, CustomRetrieveUpdateDestroyAPI):
    """API endpoint for detail view of a single PartCategory object."""

    def get_serializer(self, *args, **kwargs):
        """Add additional context based on query parameters."""
        try:
            params = self.request.query_params

            kwargs['path_detail'] = str2bool(params.get('path_detail', False))
        except AttributeError:
            pass

        return self.serializer_class(*args, **kwargs)

    def update(self, request, *args, **kwargs):
        """Perform 'update' function and mark this part as 'starred' (or not)."""
        # Clean up input data
        data = self.clean_data(request.data)

        if 'starred' in data:
            starred = str2bool(data.get('starred', False))

            self.get_object().set_starred(request.user, starred)

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

    filter_backends = ORDER_FILTER

    # Order by tree level (top levels first) and then name
    ordering = ['level', 'name']


class CategoryParameterList(ListCreateAPI):
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


class PartSalePriceList(ListCreateAPI):
    """API endpoint for list view of PartSalePriceBreak model."""

    queryset = PartSellPriceBreak.objects.all()
    serializer_class = part_serializers.PartSalePriceSerializer

    filter_backends = [DjangoFilterBackend]

    filterset_fields = ['part']


class PartInternalPriceDetail(RetrieveUpdateDestroyAPI):
    """Detail endpoint for PartInternalPriceBreak model."""

    queryset = PartInternalPriceBreak.objects.all()
    serializer_class = part_serializers.PartInternalPriceSerializer


class PartInternalPriceList(ListCreateAPI):
    """API endpoint for list view of PartInternalPriceBreak model."""

    queryset = PartInternalPriceBreak.objects.all()
    serializer_class = part_serializers.PartInternalPriceSerializer
    permission_required = 'roles.sales_order.show'

    filter_backends = [DjangoFilterBackend]

    filterset_fields = ['part']


class PartAttachmentList(AttachmentMixin, ListCreateDestroyAPIView):
    """API endpoint for listing (and creating) a PartAttachment (file upload)."""

    queryset = PartAttachment.objects.all()
    serializer_class = part_serializers.PartAttachmentSerializer

    filterset_fields = ['part']


class PartAttachmentDetail(AttachmentMixin, RetrieveUpdateDestroyAPI):
    """Detail endpoint for PartAttachment model."""

    queryset = PartAttachment.objects.all()
    serializer_class = part_serializers.PartAttachmentSerializer


class PartTestTemplateFilter(rest_filters.FilterSet):
    """Custom filterset class for the PartTestTemplateList endpoint."""

    class Meta:
        """Metaclass options for this filterset."""

        model = PartTestTemplate
        fields = ['required', 'requires_value', 'requires_attachment']

    part = rest_filters.ModelChoiceFilter(
        queryset=Part.objects.filter(trackable=True),
        label='Part',
        field_name='part',
        method='filter_part',
    )

    def filter_part(self, queryset, name, part):
        """Filter by the 'part' field.

        Note that for the 'part' field, we also include any parts "above" the specified part.
        """
        include_inherited = str2bool(
            self.request.query_params.get('include_inherited', True)
        )

        if include_inherited:
            return queryset.filter(part__in=part.get_ancestors(include_self=True))
        else:
            return queryset.filter(part=part)


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

    pass


class PartTestTemplateList(PartTestTemplateMixin, ListCreateAPI):
    """API endpoint for listing (and creating) a PartTestTemplate."""

    filterset_class = PartTestTemplateFilter

    filter_backends = SEARCH_ORDER_FILTER

    search_fields = ['test_name', 'description']

    ordering_fields = ['test_name', 'required', 'requires_value', 'requires_attachment']

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

    def retrieve(self, request, *args, **kwargs):
        """Return scheduling information for the referenced Part instance."""
        part = self.get_object()

        schedule = []

        def add_schedule_entry(
            date, quantity, title, label, url, speculative_quantity=0
        ):
            """Check if a scheduled entry should be added.

            Rules:
            - date must be non-null
            - date cannot be in the "past"
            - quantity must not be zero
            """
            schedule.append({
                'date': date,
                'quantity': quantity,
                'speculative_quantity': speculative_quantity,
                'title': title,
                'label': label,
                'url': url,
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
                target_date,
                quantity,
                _('Incoming Purchase Order'),
                str(line.order),
                line.order.get_absolute_url(),
            )

        # Add sales order (outgoing stock) information
        so_lines = order.models.SalesOrderLineItem.objects.filter(
            part=part, order__status__in=SalesOrderStatusGroups.OPEN
        )

        for line in so_lines:
            target_date = line.target_date or line.order.target_date

            quantity = max(line.quantity - line.shipped, 0)

            add_schedule_entry(
                target_date,
                -quantity,
                _('Outgoing Sales Order'),
                str(line.order),
                line.order.get_absolute_url(),
            )

        # Add build orders (incoming stock) information
        build_orders = Build.objects.filter(
            part=part, status__in=BuildStatusGroups.ACTIVE_CODES
        )

        for build in build_orders:
            quantity = max(build.quantity - build.completed, 0)

            add_schedule_entry(
                build.target_date,
                quantity,
                _('Stock produced by Build Order'),
                str(build),
                build.get_absolute_url(),
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
                    str(build),
                    build.get_absolute_url(),
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
        schedule = sorted(schedule, key=functools.cmp_to_key(compare))

        return Response(schedule)


class PartRequirements(RetrieveAPI):
    """API endpoint detailing 'requirements' information for a particular part.

    This endpoint returns information on upcoming requirements for:

    - Sales Orders
    - Build Orders
    - Total requirements

    As this data is somewhat complex to calculate, is it not included in the default API
    """

    queryset = Part.objects.all()

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

    def retrieve(self, request, *args, **kwargs):
        """Return serial number information for the referenced Part instance."""
        part = self.get_object()

        # Calculate the "latest" serial number
        latest = part.get_latest_serial_number()

        data = {'latest': latest}

        if latest is not None:
            next_serial = increment_serial_number(latest)

            if next_serial != latest:
                data['next'] = next_serial

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
        fields = []

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

    def filter_exclude_tree(self, queryset, name, part):
        """Exclude all parts and variants 'down' from the specified part from the queryset."""
        children = part.get_descendants(include_self=True)

        return queryset.exclude(id__in=children)

    ancestor = rest_filters.ModelChoiceFilter(
        label='Ancestor', queryset=Part.objects.all(), method='filter_ancestor'
    )

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

    is_template = rest_filters.BooleanFilter()

    assembly = rest_filters.BooleanFilter()

    component = rest_filters.BooleanFilter()

    trackable = rest_filters.BooleanFilter()

    purchaseable = rest_filters.BooleanFilter()

    salable = rest_filters.BooleanFilter()

    active = rest_filters.BooleanFilter()

    virtual = rest_filters.BooleanFilter()

    tags_name = rest_filters.CharFilter(field_name='tags__name', lookup_expr='iexact')

    tags_slug = rest_filters.CharFilter(field_name='tags__slug', lookup_expr='iexact')

    # Created date filters
    created_before = InvenTreeDateFilter(
        label='Updated before', field_name='creation_date', lookup_expr='lte'
    )
    created_after = InvenTreeDateFilter(
        label='Updated after', field_name='creation_date', lookup_expr='gte'
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

        return queryset

    def get_serializer(self, *args, **kwargs):
        """Return a serializer instance for this endpoint."""
        # Ensure the request context is passed through
        kwargs['context'] = self.get_serializer_context()

        # Indicate that we can create a new Part via this endpoint
        kwargs['create'] = self.is_create

        # Pass a list of "starred" parts to the current user to the serializer
        # We do this to reduce the number of database queries required!
        if self.starred_parts is None and self.request is not None:
            self.starred_parts = [
                star.part for star in self.request.user.starred_parts.all()
            ]

        kwargs['starred_parts'] = self.starred_parts

        try:
            params = self.request.query_params

            kwargs['parameters'] = str2bool(params.get('parameters', None))
            kwargs['category_detail'] = str2bool(params.get('category_detail', False))
            kwargs['path_detail'] = str2bool(params.get('path_detail', False))

        except AttributeError:
            pass

        return self.serializer_class(*args, **kwargs)

    def get_serializer_context(self):
        """Extend serializer context data."""
        context = super().get_serializer_context()
        context['request'] = self.request

        return context


class PartList(PartMixin, APIDownloadMixin, ListCreateAPI):
    """API endpoint for accessing a list of Part objects, or creating a new Part instance."""

    filterset_class = PartFilter
    is_create = True

    def download_queryset(self, queryset, export_format):
        """Download the filtered queryset as a data file."""
        dataset = PartResource().export(queryset=queryset)

        filedata = dataset.export(export_format)
        filename = f'InvenTree_Parts.{export_format}'

        return DownloadFile(filedata, filename)

    def list(self, request, *args, **kwargs):
        """Override the 'list' method, as the PartCategory objects are very expensive to serialize!

        So we will serialize them first, and keep them in memory, so that they do not have to be serialized multiple times...
        """
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
        else:
            serializer = self.get_serializer(queryset, many=True)

        data = serializer.data

        """
        Determine the response type based on the request.
        a) For HTTP requests (e.g. via the browsable API) return a DRF response
        b) For AJAX requests, simply return a JSON rendered response.
        """
        if page is not None:
            return self.get_paginated_response(data)
        elif is_ajax(request):
            return JsonResponse(data, safe=False)
        return Response(data)

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

        # Filter by whether the BOM has been validated (or not)
        bom_valid = params.get('bom_valid', None)

        # TODO: Querying bom_valid status may be quite expensive
        # TODO: (It needs to be profiled!)
        # TODO: It might be worth caching the bom_valid status to a database column
        if bom_valid is not None:
            bom_valid = str2bool(bom_valid)

            # Limit queryset to active assemblies
            queryset = queryset.filter(active=True, assembly=True)

            pks = []

            for prt in queryset:
                if prt.is_bom_valid() == bom_valid:
                    pks.append(prt.pk)

            queryset = queryset.filter(pk__in=pks)

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

        # Filter by 'starred' parts?
        starred = params.get('starred', None)

        if starred is not None:
            starred = str2bool(starred)
            starred_parts = [
                star.part.pk for star in self.request.user.starred_parts.all()
            ]

            if starred:
                queryset = queryset.filter(pk__in=starred_parts)
            else:
                queryset = queryset.exclude(pk__in=starred_parts)

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
        'last_stocktake',
        'units',
    ]

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

    def destroy(self, request, *args, **kwargs):
        """Delete a Part instance via the API.

        - If the part is 'active' it cannot be deleted
        - It must first be marked as 'inactive'
        """
        part = Part.objects.get(pk=int(kwargs['pk']))
        # Check if inactive
        if not part.active:
            # Delete
            return super(PartDetail, self).destroy(request, *args, **kwargs)
        # Return 405 error
        message = 'Part is active: cannot delete'
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED, data=message)

    def update(self, request, *args, **kwargs):
        """Custom update functionality for Part instance.

        - If the 'starred' field is provided, update the 'starred' status against current user
        """
        # Clean input data
        data = self.clean_data(request.data)

        if 'starred' in data:
            starred = str2bool(data.get('starred', False))

            self.get_object().set_starred(request.user, starred)

        response = super().update(request, *args, **kwargs)

        return response


class PartRelatedList(ListCreateAPI):
    """API endpoint for accessing a list of PartRelated objects."""

    queryset = PartRelated.objects.all()
    serializer_class = part_serializers.PartRelationSerializer

    def filter_queryset(self, queryset):
        """Custom queryset filtering."""
        queryset = super().filter_queryset(queryset)

        params = self.request.query_params

        # Add a filter for "part" - we can filter either part_1 or part_2
        part = params.get('part', None)

        if part is not None:
            try:
                part = Part.objects.get(pk=part)
                queryset = queryset.filter(Q(part_1=part) | Q(part_2=part)).distinct()

            except (ValueError, Part.DoesNotExist):
                pass

        return queryset


class PartRelatedDetail(RetrieveUpdateDestroyAPI):
    """API endpoint for accessing detail view of a PartRelated object."""

    queryset = PartRelated.objects.all()
    serializer_class = part_serializers.PartRelationSerializer


class PartParameterTemplateFilter(rest_filters.FilterSet):
    """FilterSet for PartParameterTemplate objects."""

    class Meta:
        """Metaclass options."""

        model = PartParameterTemplate

        # Simple filter fields
        fields = ['units', 'checkbox']

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


class PartParameterTemplateList(ListCreateAPI):
    """API endpoint for accessing a list of PartParameterTemplate objects.

    - GET: Return list of PartParameterTemplate objects
    - POST: Create a new PartParameterTemplate object
    """

    queryset = PartParameterTemplate.objects.all()
    serializer_class = part_serializers.PartParameterTemplateSerializer
    filterset_class = PartParameterTemplateFilter

    filter_backends = SEARCH_ORDER_FILTER

    filterset_fields = ['name']

    search_fields = ['name', 'description']

    ordering_fields = ['name', 'units', 'checkbox']

    def filter_queryset(self, queryset):
        """Custom filtering for the PartParameterTemplate API."""
        queryset = super().filter_queryset(queryset)

        params = self.request.query_params

        # Filtering against a "Part" - return only parameter templates which are referenced by a part
        part = params.get('part', None)

        if part is not None:
            try:
                part = Part.objects.get(pk=part)
                parameters = PartParameter.objects.filter(part=part)
                template_ids = parameters.values_list('template').distinct()
                queryset = queryset.filter(pk__in=[el[0] for el in template_ids])
            except (ValueError, Part.DoesNotExist):
                pass

        # Filtering against a "PartCategory" - return only parameter templates which are referenced by parts in this category
        category = params.get('category', None)

        if category is not None:
            try:
                category = PartCategory.objects.get(pk=category)
                cats = category.get_descendants(include_self=True)
                parameters = PartParameter.objects.filter(part__category__in=cats)
                template_ids = parameters.values_list('template').distinct()
                queryset = queryset.filter(pk__in=[el[0] for el in template_ids])
            except (ValueError, PartCategory.DoesNotExist):
                pass

        return queryset


class PartParameterTemplateDetail(RetrieveUpdateDestroyAPI):
    """API endpoint for accessing the detail view for a PartParameterTemplate object."""

    queryset = PartParameterTemplate.objects.all()
    serializer_class = part_serializers.PartParameterTemplateSerializer


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


class PartParameterList(PartParameterAPIMixin, ListCreateAPI):
    """API endpoint for accessing a list of PartParameter objects.

    - GET: Return list of PartParameter objects
    - POST: Create a new PartParameter object
    """

    filterset_class = PartParameterFilter

    filter_backends = SEARCH_ORDER_FILTER_ALIAS

    ordering_fields = ['name', 'data', 'part', 'template']

    ordering_field_aliases = {
        'name': 'template__name',
        'data': ['data_numeric', 'data'],
    }

    search_fields = [
        'data',
        'template__name',
        'template__description',
        'template__units',
    ]


class PartParameterDetail(PartParameterAPIMixin, RetrieveUpdateDestroyAPI):
    """API endpoint for detail view of a single PartParameter object."""

    pass


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
        label='Master part is active', field_name='part__active'
    )
    part_trackable = rest_filters.BooleanFilter(
        label='Master part is trackable', field_name='part__trackable'
    )

    # Filters for linked 'sub_part'
    sub_part_trackable = rest_filters.BooleanFilter(
        label='Sub part is trackable', field_name='sub_part__trackable'
    )
    sub_part_assembly = rest_filters.BooleanFilter(
        label='Sub part is an assembly', field_name='sub_part__assembly'
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


class BomList(BomMixin, ListCreateDestroyAPIView):
    """API endpoint for accessing a list of BomItem objects.

    - GET: Return list of BomItem objects
    - POST: Create a new BomItem object
    """

    filterset_class = BomFilter

    def list(self, request, *args, **kwargs):
        """Return serialized list response for this endpoint."""
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
        else:
            serializer = self.get_serializer(queryset, many=True)

        data = serializer.data

        """
        Determine the response type based on the request.
        a) For HTTP requests (e.g. via the browsable API) return a DRF response
        b) For AJAX requests, simply return a JSON rendered response.
        """
        if page is not None:
            return self.get_paginated_response(data)
        elif is_ajax(request):
            return JsonResponse(data, safe=False)
        return Response(data)

    def filter_queryset(self, queryset):
        """Custom query filtering for the BomItem list API."""
        queryset = super().filter_queryset(queryset)

        params = self.request.query_params

        # Filter by part?
        part = params.get('part', None)

        if part is not None:
            """
            If we are filtering by "part", there are two cases to consider:

            a) Bom items which are defined for *this* part
            b) Inherited parts which are defined for a *parent* part

            So we need to construct two queries!
            """

            # First, check that the part is actually valid!
            try:
                part = Part.objects.get(pk=part)

                queryset = queryset.filter(part.get_bom_item_filter())

            except (ValueError, Part.DoesNotExist):
                pass

        """
        Filter by 'uses'?

        Here we pass a part ID and return BOM items for any assemblies which "use" (or "require") that part.

        There are multiple ways that an assembly can "use" a sub-part:

        A) Directly specifying the sub_part in a BomItem field
        B) Specifying a "template" part with inherited=True
        C) Allowing variant parts to be substituted
        D) Allowing direct substitute parts to be specified

        - BOM items which are "inherited" by parts which are variants of the master BomItem
        """
        uses = params.get('uses', None)

        if uses is not None:
            try:
                # Extract the part we are interested in
                uses_part = Part.objects.get(pk=uses)

                queryset = queryset.filter(uses_part.get_used_in_bom_item_filter())

            except (ValueError, Part.DoesNotExist):
                pass

        return queryset

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
        'quantity',
        'sub_part',
        'available_stock',
        'allow_variants',
        'inherited',
        'optional',
        'consumable',
    ]

    ordering_field_aliases = {'sub_part': 'sub_part__name'}


class BomDetail(BomMixin, RetrieveUpdateDestroyAPI):
    """API endpoint for detail view of a single BomItem object."""

    pass


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
    # Base URL for PartAttachment API endpoints
    path(
        'attachment/',
        include([
            path(
                '<int:pk>/',
                PartAttachmentDetail.as_view(),
                name='api-part-attachment-detail',
            ),
            path('', PartAttachmentList.as_view(), name='api-part-attachment-list'),
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
    # BOM template
    path(
        'bom_template/',
        views.BomUploadTemplate.as_view(),
        name='api-bom-upload-template',
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
            # BOM download
            path('bom-download/', views.BomDownload.as_view(), name='api-bom-download'),
            # Old pricing endpoint
            path('pricing2/', views.PartPricing.as_view(), name='part-pricing'),
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
