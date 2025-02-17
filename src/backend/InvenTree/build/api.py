"""JSON API for the Build app."""

from __future__ import annotations

from django.contrib.auth.models import User
from django.db.models import F, Q
from django.urls import include, path
from django.utils.translation import gettext_lazy as _

from django_filters import rest_framework as rest_filters
from rest_framework.exceptions import ValidationError

import build.admin
import build.serializers
import common.models
import part.models as part_models
from build.models import Build, BuildItem, BuildLine
from build.status_codes import BuildStatus, BuildStatusGroups
from generic.states.api import StatusView
from importer.mixins import DataExportViewMixin
from InvenTree.api import BulkDeleteMixin, MetadataView
from InvenTree.filters import SEARCH_ORDER_FILTER_ALIAS, InvenTreeDateFilter
from InvenTree.helpers import isNull, str2bool
from InvenTree.mixins import CreateAPI, ListCreateAPI, RetrieveUpdateDestroyAPI
from users.models import Owner


class BuildFilter(rest_filters.FilterSet):
    """Custom filterset for BuildList API endpoint."""

    class Meta:
        """Metaclass options."""

        model = Build
        fields = ['sales_order']

    status = rest_filters.NumberFilter(label=_('Order Status'), method='filter_status')

    def filter_status(self, queryset, name, value):
        """Filter by integer status code.

        Note: Also account for the possibility of a custom status code
        """
        q1 = Q(status=value, status_custom_key__isnull=True)
        q2 = Q(status_custom_key=value)

        return queryset.filter(q1 | q2).distinct()

    active = rest_filters.BooleanFilter(label='Build is active', method='filter_active')

    # 'outstanding' is an alias for 'active' here
    outstanding = rest_filters.BooleanFilter(
        label='Build is outstanding', method='filter_active'
    )

    def filter_active(self, queryset, name, value):
        """Filter the queryset to either include or exclude orders which are active."""
        if str2bool(value):
            return queryset.filter(status__in=BuildStatusGroups.ACTIVE_CODES)
        return queryset.exclude(status__in=BuildStatusGroups.ACTIVE_CODES)

    parent = rest_filters.ModelChoiceFilter(
        queryset=Build.objects.all(), label=_('Parent Build'), field_name='parent'
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
        queryset=part_models.Part.objects.all(),
        field_name='part',
        method='filter_part',
        label=_('Part'),
    )

    def filter_part(self, queryset, name, part):
        """Filter by 'part' which is being built.

        Note:
        - If "include_variants" is True, include all variants of the selected part.
        - Otherwise, just filter by the selected part.
        """
        include_variants = str2bool(self.data.get('include_variants', False))

        if include_variants:
            return queryset.filter(part__in=part.get_descendants(include_self=True))
        else:
            return queryset.filter(part=part)

    category = rest_filters.ModelChoiceFilter(
        queryset=part_models.PartCategory.objects.all(),
        method='filter_category',
        label=_('Category'),
    )

    def filter_category(self, queryset, name, category):
        """Filter by part category (including sub-categories)."""
        categories = category.get_descendants(include_self=True)
        return queryset.filter(part__category__in=categories)

    ancestor = rest_filters.ModelChoiceFilter(
        queryset=Build.objects.all(),
        label=_('Ancestor Build'),
        method='filter_ancestor',
    )

    def filter_ancestor(self, queryset, name, parent):
        """Filter by 'parent' build order."""
        builds = parent.get_descendants(include_self=False)
        return queryset.filter(pk__in=[b.pk for b in builds])

    overdue = rest_filters.BooleanFilter(
        label='Build is overdue', method='filter_overdue'
    )

    def filter_overdue(self, queryset, name, value):
        """Filter the queryset to either include or exclude orders which are overdue."""
        if str2bool(value):
            return queryset.filter(Build.OVERDUE_FILTER)
        return queryset.exclude(Build.OVERDUE_FILTER)

    assigned_to_me = rest_filters.BooleanFilter(
        label=_('Assigned to me'), method='filter_assigned_to_me'
    )

    def filter_assigned_to_me(self, queryset, name, value):
        """Filter by orders which are assigned to the current user."""
        value = str2bool(value)

        # Work out who "me" is!
        owners = Owner.get_owners_matching_user(self.request.user)

        if value:
            return queryset.filter(responsible__in=owners)
        return queryset.exclude(responsible__in=owners)

    issued_by = rest_filters.ModelChoiceFilter(
        queryset=Owner.objects.all(), label=_('Issued By'), method='filter_issued_by'
    )

    def filter_issued_by(self, queryset, name, owner):
        """Filter by 'owner' which issued the order."""
        if owner.label() == 'user':
            user = User.objects.get(pk=owner.owner_id)
            return queryset.filter(issued_by=user)
        elif owner.label() == 'group':
            group = User.objects.filter(groups__pk=owner.owner_id)
            return queryset.filter(issued_by__in=group)
        else:
            return queryset.none()

    assigned_to = rest_filters.ModelChoiceFilter(
        queryset=Owner.objects.all(), field_name='responsible', label=_('Assigned To')
    )

    def filter_responsible(self, queryset, name, owner):
        """Filter by orders which are assigned to the specified owner."""
        owners = list(Owner.objects.filter(pk=owner))

        # if we query by a user, also find all ownerships through group memberships
        if len(owners) > 0 and owners[0].label() == 'user':
            owners = Owner.get_owners_matching_user(
                User.objects.get(pk=owners[0].owner_id)
            )

        return queryset.filter(responsible__in=owners)

    # Exact match for reference
    reference = rest_filters.CharFilter(
        label='Filter by exact reference', field_name='reference', lookup_expr='iexact'
    )

    project_code = rest_filters.ModelChoiceFilter(
        queryset=common.models.ProjectCode.objects.all(), field_name='project_code'
    )

    has_project_code = rest_filters.BooleanFilter(
        label='has_project_code', method='filter_has_project_code'
    )

    def filter_has_project_code(self, queryset, name, value):
        """Filter by whether or not the order has a project code."""
        if str2bool(value):
            return queryset.exclude(project_code=None)
        return queryset.filter(project_code=None)

    created_before = InvenTreeDateFilter(
        label=_('Created before'), field_name='creation_date', lookup_expr='lt'
    )

    created_after = InvenTreeDateFilter(
        label=_('Created after'), field_name='creation_date', lookup_expr='gt'
    )

    has_start_date = rest_filters.BooleanFilter(
        label=_('Has start date'), method='filter_has_start_date'
    )

    def filter_has_start_date(self, queryset, name, value):
        """Filter by whether or not the order has a start date."""
        return queryset.filter(start_date__isnull=not str2bool(value))

    start_date_before = InvenTreeDateFilter(
        label=_('Start date before'), field_name='start_date', lookup_expr='lt'
    )

    start_date_after = InvenTreeDateFilter(
        label=_('Start date after'), field_name='start_date', lookup_expr='gt'
    )

    has_target_date = rest_filters.BooleanFilter(
        label=_('Has target date'), method='filter_has_target_date'
    )

    def filter_has_target_date(self, queryset, name, value):
        """Filter by whether or not the order has a target date."""
        return queryset.filter(target_date__isnull=not str2bool(value))

    target_date_before = InvenTreeDateFilter(
        label=_('Target date before'), field_name='target_date', lookup_expr='lt'
    )

    target_date_after = InvenTreeDateFilter(
        label=_('Target date after'), field_name='target_date', lookup_expr='gt'
    )

    completed_before = InvenTreeDateFilter(
        label=_('Completed before'), field_name='completion_date', lookup_expr='lt'
    )

    completed_after = InvenTreeDateFilter(
        label=_('Completed after'), field_name='completion_date', lookup_expr='gt'
    )


class BuildMixin:
    """Mixin class for Build API endpoints."""

    queryset = Build.objects.all()
    serializer_class = build.serializers.BuildSerializer

    def get_queryset(self):
        """Return the queryset for the Build API endpoints."""
        queryset = super().get_queryset()

        queryset = queryset.prefetch_related(
            'responsible',
            'issued_by',
            'build_lines',
            'build_lines__bom_item',
            'build_lines__build',
            'part',
            'part__pricing_data',
        )

        return queryset


class BuildList(DataExportViewMixin, BuildMixin, ListCreateAPI):
    """API endpoint for accessing a list of Build objects.

    - GET: Return list of objects (with filters)
    - POST: Create a new Build object
    """

    filterset_class = BuildFilter

    filter_backends = SEARCH_ORDER_FILTER_ALIAS

    ordering_fields = [
        'reference',
        'part__name',
        'status',
        'creation_date',
        'start_date',
        'target_date',
        'completion_date',
        'quantity',
        'completed',
        'issued_by',
        'responsible',
        'project_code',
        'priority',
        'level',
    ]

    ordering_field_aliases = {
        'reference': ['reference_int', 'reference'],
        'project_code': ['project_code__code'],
    }

    ordering = '-reference'

    search_fields = [
        'reference',
        'title',
        'part__name',
        'part__IPN',
        'part__description',
        'project_code__code',
        'priority',
    ]

    def get_queryset(self):
        """Override the queryset filtering, as some of the fields don't natively play nicely with DRF."""
        queryset = super().get_queryset().select_related('part')

        queryset = build.serializers.BuildSerializer.annotate_queryset(queryset)

        return queryset

    def filter_queryset(self, queryset):
        """Custom query filtering for the BuildList endpoint."""
        queryset = super().filter_queryset(queryset)

        params = self.request.query_params

        # exclude parent tree
        exclude_tree = params.get('exclude_tree', None)

        if exclude_tree is not None:
            try:
                build = Build.objects.get(pk=exclude_tree)

                queryset = queryset.exclude(
                    pk__in=[bld.pk for bld in build.get_descendants(include_self=True)]
                )

            except (ValueError, Build.DoesNotExist):
                pass

        # Filter by 'date range'
        min_date = params.get('min_date', None)
        max_date = params.get('max_date', None)

        if min_date is not None and max_date is not None:
            queryset = Build.filterByDate(queryset, min_date, max_date)

        return queryset

    def get_serializer(self, *args, **kwargs):
        """Add extra context information to the endpoint serializer."""
        try:
            part_detail = str2bool(self.request.GET.get('part_detail', True))
        except AttributeError:
            part_detail = True

        kwargs['part_detail'] = part_detail
        kwargs['create'] = True

        return self.serializer_class(*args, **kwargs)


class BuildDetail(BuildMixin, RetrieveUpdateDestroyAPI):
    """API endpoint for detail view of a Build object."""

    def destroy(self, request, *args, **kwargs):
        """Only allow deletion of a BuildOrder if the build status is CANCELLED."""
        build = self.get_object()

        if build.status != BuildStatus.CANCELLED:
            raise ValidationError({
                'non_field_errors': [
                    _('Build must be cancelled before it can be deleted')
                ]
            })

        return super().destroy(request, *args, **kwargs)


class BuildUnallocate(CreateAPI):
    """API endpoint for unallocating stock items from a build order.

    - The BuildOrder object is specified by the URL
    - "output" (StockItem) can optionally be specified
    - "bom_item" can optionally be specified
    """

    queryset = Build.objects.none()

    serializer_class = build.serializers.BuildUnallocationSerializer

    def get_serializer_context(self):
        """Add extra context information to the endpoint serializer."""
        ctx = super().get_serializer_context()

        try:
            ctx['build'] = Build.objects.get(pk=self.kwargs.get('pk', None))
        except Exception:
            pass

        ctx['request'] = self.request

        return ctx


class BuildLineFilter(rest_filters.FilterSet):
    """Custom filterset for the BuildLine API endpoint."""

    class Meta:
        """Meta information for the BuildLineFilter class."""

        model = BuildLine
        fields = ['build', 'bom_item']

    # Fields on related models
    consumable = rest_filters.BooleanFilter(
        label=_('Consumable'), field_name='bom_item__consumable'
    )
    optional = rest_filters.BooleanFilter(
        label=_('Optional'), field_name='bom_item__optional'
    )
    assembly = rest_filters.BooleanFilter(
        label=_('Assembly'), field_name='bom_item__sub_part__assembly'
    )
    tracked = rest_filters.BooleanFilter(
        label=_('Tracked'), field_name='bom_item__sub_part__trackable'
    )
    testable = rest_filters.BooleanFilter(
        label=_('Testable'), field_name='bom_item__sub_part__testable'
    )

    part = rest_filters.ModelChoiceFilter(
        queryset=part_models.Part.objects.all(),
        label=_('Part'),
        field_name='bom_item__sub_part',
    )

    order_outstanding = rest_filters.BooleanFilter(
        label=_('Order Outstanding'), method='filter_order_outstanding'
    )

    def filter_order_outstanding(self, queryset, name, value):
        """Filter by whether the associated BuildOrder is 'outstanding'."""
        if str2bool(value):
            return queryset.filter(build__status__in=BuildStatusGroups.ACTIVE_CODES)
        return queryset.exclude(build__status__in=BuildStatusGroups.ACTIVE_CODES)

    allocated = rest_filters.BooleanFilter(
        label=_('Allocated'), method='filter_allocated'
    )

    def filter_allocated(self, queryset, name, value):
        """Filter by whether each BuildLine is fully allocated."""
        if str2bool(value):
            return queryset.filter(allocated__gte=F('quantity'))
        return queryset.filter(allocated__lt=F('quantity'))

    available = rest_filters.BooleanFilter(
        label=_('Available'), method='filter_available'
    )

    def filter_available(self, queryset, name, value):
        """Filter by whether there is sufficient stock available for each BuildLine.

        To determine this, we need to know:

        - The quantity required for each BuildLine
        - The quantity available for each BuildLine (including variants and substitutes)
        - The quantity allocated for each BuildLine
        """
        flt = Q(
            quantity__lte=F('allocated')
            + F('available_stock')
            + F('available_substitute_stock')
            + F('available_variant_stock')
        )

        if str2bool(value):
            return queryset.filter(flt)
        return queryset.exclude(flt)


class BuildLineEndpoint:
    """Mixin class for BuildLine API endpoints."""

    queryset = BuildLine.objects.all()
    serializer_class = build.serializers.BuildLineSerializer

    def get_serializer(self, *args, **kwargs):
        """Return the serializer instance for this endpoint."""
        kwargs['context'] = self.get_serializer_context()

        try:
            params = self.request.query_params

            kwargs['part_detail'] = str2bool(params.get('part_detail', True))
            kwargs['build_detail'] = str2bool(params.get('build_detail', False))
        except AttributeError:
            pass

        return self.serializer_class(*args, **kwargs)

    def get_source_build(self) -> Build:
        """Return the source Build object for the BuildLine queryset.

        This source build is used to filter the available stock for each BuildLine.

        - If this is a "detail" view, use the build associated with the line
        - If this is a "list" view, use the build associated with the request
        """
        raise NotImplementedError(
            'get_source_build must be implemented in the child class'
        )

    def get_queryset(self):
        """Override queryset to select-related and annotate."""
        queryset = super().get_queryset()

        if not hasattr(self, 'source_build'):
            self.source_build = self.get_source_build()

        source_build = self.source_build

        return build.serializers.BuildLineSerializer.annotate_queryset(
            queryset, build=source_build
        )


class BuildLineList(BuildLineEndpoint, DataExportViewMixin, ListCreateAPI):
    """API endpoint for accessing a list of BuildLine objects."""

    filterset_class = BuildLineFilter
    filter_backends = SEARCH_ORDER_FILTER_ALIAS

    ordering_fields = [
        'part',
        'allocated',
        'reference',
        'quantity',
        'consumable',
        'optional',
        'unit_quantity',
        'available_stock',
        'trackable',
        'allow_variants',
        'inherited',
    ]

    ordering_field_aliases = {
        'part': 'bom_item__sub_part__name',
        'reference': 'bom_item__reference',
        'unit_quantity': 'bom_item__quantity',
        'consumable': 'bom_item__consumable',
        'optional': 'bom_item__optional',
        'trackable': 'bom_item__sub_part__trackable',
        'allow_variants': 'bom_item__allow_variants',
        'inherited': 'bom_item__inherited',
    }

    search_fields = [
        'bom_item__sub_part__name',
        'bom_item__sub_part__IPN',
        'bom_item__sub_part__description',
        'bom_item__reference',
    ]

    def get_source_build(self) -> Build | None:
        """Return the target build for the BuildLine queryset."""
        source_build = None

        try:
            build_id = self.request.query_params.get('build', None)
            if build_id:
                source_build = Build.objects.filter(pk=build_id).first()
        except (Build.DoesNotExist, AttributeError, ValueError):
            pass

        return source_build


class BuildLineDetail(BuildLineEndpoint, RetrieveUpdateDestroyAPI):
    """API endpoint for detail view of a BuildLine object."""

    def get_source_build(self) -> Build | None:
        """Return the target source location for the BuildLine queryset."""
        return None


class BuildOrderContextMixin:
    """Mixin class which adds build order as serializer context variable."""

    def get_serializer_context(self):
        """Add extra context information to the endpoint serializer."""
        ctx = super().get_serializer_context()

        ctx['request'] = self.request
        ctx['to_complete'] = True

        try:
            ctx['build'] = Build.objects.get(pk=self.kwargs.get('pk', None))
        except Exception:
            pass

        return ctx


class BuildOutputCreate(BuildOrderContextMixin, CreateAPI):
    """API endpoint for creating new build output(s)."""

    queryset = Build.objects.none()

    serializer_class = build.serializers.BuildOutputCreateSerializer


class BuildOutputScrap(BuildOrderContextMixin, CreateAPI):
    """API endpoint for scrapping build output(s)."""

    queryset = Build.objects.none()
    serializer_class = build.serializers.BuildOutputScrapSerializer

    def get_serializer_context(self):
        """Add extra context information to the endpoint serializer."""
        ctx = super().get_serializer_context()
        ctx['to_complete'] = False
        return ctx


class BuildOutputComplete(BuildOrderContextMixin, CreateAPI):
    """API endpoint for completing build outputs."""

    queryset = Build.objects.none()

    serializer_class = build.serializers.BuildOutputCompleteSerializer


class BuildOutputDelete(BuildOrderContextMixin, CreateAPI):
    """API endpoint for deleting multiple build outputs."""

    def get_serializer_context(self):
        """Add extra context information to the endpoint serializer."""
        ctx = super().get_serializer_context()

        ctx['to_complete'] = False

        return ctx

    queryset = Build.objects.none()

    serializer_class = build.serializers.BuildOutputDeleteSerializer


class BuildFinish(BuildOrderContextMixin, CreateAPI):
    """API endpoint for marking a build as finished (completed)."""

    queryset = Build.objects.none()
    serializer_class = build.serializers.BuildCompleteSerializer

    def get_queryset(self):
        """Return the queryset for the BuildFinish API endpoint."""
        queryset = super().get_queryset()
        queryset = queryset.prefetch_related('build_lines', 'build_lines__allocations')

        return queryset


class BuildAutoAllocate(BuildOrderContextMixin, CreateAPI):
    """API endpoint for 'automatically' allocating stock against a build order.

    - Only looks at 'untracked' parts
    - If stock exists in a single location, easy!
    - If user decides that stock items are "fungible", allocate against multiple stock items
    - If the user wants to, allocate substite parts if the primary parts are not available.
    """

    queryset = Build.objects.none()
    serializer_class = build.serializers.BuildAutoAllocationSerializer


class BuildAllocate(BuildOrderContextMixin, CreateAPI):
    """API endpoint to allocate stock items to a build order.

    - The BuildOrder object is specified by the URL
    - Items to allocate are specified as a list called "items" with the following options:
        - bom_item: pk value of a given BomItem object (must match the part associated with this build)
        - stock_item: pk value of a given StockItem object
        - quantity: quantity to allocate
        - output: StockItem (build order output) to allocate stock against (optional)
    """

    queryset = Build.objects.none()
    serializer_class = build.serializers.BuildAllocationSerializer


class BuildIssue(BuildOrderContextMixin, CreateAPI):
    """API endpoint for issuing a BuildOrder."""

    queryset = Build.objects.all()
    serializer_class = build.serializers.BuildIssueSerializer


class BuildHold(BuildOrderContextMixin, CreateAPI):
    """API endpoint for placing a BuildOrder on hold."""

    queryset = Build.objects.all()
    serializer_class = build.serializers.BuildHoldSerializer


class BuildCancel(BuildOrderContextMixin, CreateAPI):
    """API endpoint for cancelling a BuildOrder."""

    queryset = Build.objects.all()
    serializer_class = build.serializers.BuildCancelSerializer


class BuildItemDetail(RetrieveUpdateDestroyAPI):
    """API endpoint for detail view of a BuildItem object."""

    queryset = BuildItem.objects.all()
    serializer_class = build.serializers.BuildItemSerializer


class BuildItemFilter(rest_filters.FilterSet):
    """Custom filterset for the BuildItemList API endpoint."""

    class Meta:
        """Metaclass option."""

        model = BuildItem
        fields = ['build_line', 'stock_item', 'install_into']

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
        queryset=part_models.Part.objects.all(),
        label=_('Part'),
        method='filter_part',
        field_name='stock_item__part',
    )

    def filter_part(self, queryset, name, part):
        """Filter by 'part' which is being built.

        Note:
        - If "include_variants" is True, include all variants of the selected part.
        - Otherwise, just filter by the selected part.
        """
        include_variants = str2bool(self.data.get('include_variants', False))

        if include_variants:
            return queryset.filter(
                stock_item__part__in=part.get_descendants(include_self=True)
            )
        else:
            return queryset.filter(stock_item__part=part)

    build = rest_filters.ModelChoiceFilter(
        queryset=build.models.Build.objects.all(),
        label=_('Build Order'),
        field_name='build_line__build',
    )

    tracked = rest_filters.BooleanFilter(label='Tracked', method='filter_tracked')

    def filter_tracked(self, queryset, name, value):
        """Filter the queryset based on whether build items are tracked."""
        if str2bool(value):
            return queryset.exclude(install_into=None)
        return queryset.filter(install_into=None)


class BuildItemList(DataExportViewMixin, BulkDeleteMixin, ListCreateAPI):
    """API endpoint for accessing a list of BuildItem objects.

    - GET: Return list of objects
    - POST: Create a new BuildItem object
    """

    queryset = BuildItem.objects.all()
    serializer_class = build.serializers.BuildItemSerializer
    filterset_class = BuildItemFilter
    filter_backends = SEARCH_ORDER_FILTER_ALIAS

    def get_serializer(self, *args, **kwargs):
        """Returns a BuildItemSerializer instance based on the request."""
        try:
            params = self.request.query_params

            for key in [
                'part_detail',
                'location_detail',
                'stock_detail',
                'build_detail',
            ]:
                if key in params:
                    kwargs[key] = str2bool(params.get(key, False))
        except AttributeError:
            pass

        return self.serializer_class(*args, **kwargs)

    def get_queryset(self):
        """Override the queryset method, to perform custom prefetch."""
        queryset = super().get_queryset()

        queryset = queryset.select_related(
            'build_line',
            'build_line__build',
            'build_line__bom_item',
            'build_line__bom_item__part',
            'build_line__bom_item__sub_part',
            'install_into',
            'stock_item',
            'stock_item__location',
            'stock_item__part',
            'stock_item__supplier_part__part',
            'stock_item__supplier_part__supplier',
            'stock_item__supplier_part__manufacturer_part',
            'stock_item__supplier_part__manufacturer_part__manufacturer',
        ).prefetch_related('stock_item__location__tags')

        return queryset

    def filter_queryset(self, queryset):
        """Custom query filtering for the BuildItem list."""
        queryset = super().filter_queryset(queryset)

        params = self.request.query_params

        # Filter by output target
        output = params.get('output', None)

        if output:
            if isNull(output):
                queryset = queryset.filter(install_into=None)
            else:
                queryset = queryset.filter(install_into=output)

        return queryset

    ordering_fields = ['part', 'sku', 'quantity', 'location', 'reference', 'IPN']

    ordering_field_aliases = {
        'part': 'stock_item__part__name',
        'IPN': 'stock_item__part__IPN',
        'sku': 'stock_item__supplier_part__SKU',
        'location': 'stock_item__location__name',
        'reference': 'build_line__bom_item__reference',
    }

    search_fields = [
        'stock_item__supplier_part__SKU',
        'stock_item__part__name',
        'stock_item__part__IPN',
        'build_line__bom_item__reference',
    ]


build_api_urls = [
    # Build lines
    path(
        'line/',
        include([
            path('<int:pk>/', BuildLineDetail.as_view(), name='api-build-line-detail'),
            path('', BuildLineList.as_view(), name='api-build-line-list'),
        ]),
    ),
    # Build Items
    path(
        'item/',
        include([
            path(
                '<int:pk>/',
                include([
                    path(
                        'metadata/',
                        MetadataView.as_view(),
                        {'model': BuildItem},
                        name='api-build-item-metadata',
                    ),
                    path('', BuildItemDetail.as_view(), name='api-build-item-detail'),
                ]),
            ),
            path('', BuildItemList.as_view(), name='api-build-item-list'),
        ]),
    ),
    # Build Detail
    path(
        '<int:pk>/',
        include([
            path('allocate/', BuildAllocate.as_view(), name='api-build-allocate'),
            path(
                'auto-allocate/',
                BuildAutoAllocate.as_view(),
                name='api-build-auto-allocate',
            ),
            path(
                'complete/',
                BuildOutputComplete.as_view(),
                name='api-build-output-complete',
            ),
            path(
                'create-output/',
                BuildOutputCreate.as_view(),
                name='api-build-output-create',
            ),
            path(
                'delete-outputs/',
                BuildOutputDelete.as_view(),
                name='api-build-output-delete',
            ),
            path(
                'scrap-outputs/',
                BuildOutputScrap.as_view(),
                name='api-build-output-scrap',
            ),
            path('issue/', BuildIssue.as_view(), name='api-build-issue'),
            path('hold/', BuildHold.as_view(), name='api-build-hold'),
            path('finish/', BuildFinish.as_view(), name='api-build-finish'),
            path('cancel/', BuildCancel.as_view(), name='api-build-cancel'),
            path('unallocate/', BuildUnallocate.as_view(), name='api-build-unallocate'),
            path(
                'metadata/',
                MetadataView.as_view(),
                {'model': Build},
                name='api-build-metadata',
            ),
            path('', BuildDetail.as_view(), name='api-build-detail'),
        ]),
    ),
    # Build order status code information
    path(
        'status/',
        StatusView.as_view(),
        {StatusView.MODEL_REF: BuildStatus},
        name='api-build-status-codes',
    ),
    # Build List
    path('', BuildList.as_view(), name='api-build-list'),
]
