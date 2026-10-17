"""JSON API for the Build app."""

from __future__ import annotations

from django.contrib.auth.models import User
from django.db.models import DecimalField, F, OuterRef, Q, Subquery, Sum
from django.db.models.functions import Coalesce
from django.urls import include, path
from django.utils.translation import gettext_lazy as _

import django_filters.rest_framework.filters as rest_filters
from django_filters.rest_framework.filterset import FilterSet
from drf_spectacular.utils import extend_schema, extend_schema_field
from rest_framework import serializers, status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response

import build.models as build_models
import build.serializers
import common.filters
import common.models
import common.serializers
import part.models as part_models
import stock.models as stock_models
import stock.serializers
from build.models import Build, BuildItem, BuildLine
from build.status_codes import BuildStatus, BuildStatusGroups
from data_exporter.mixins import DataExportViewMixin
from generic.states.api import FSMTransitionMixin, StatusView
from InvenTree.api import BulkDeleteViewsetMixin, ParameterListMixin, meta_path
from InvenTree.fields import InvenTreeOutputOption, OutputConfiguration
from InvenTree.filters import (
    SEARCH_ORDER_FILTER,
    InvenTreeDateFilter,
    NumberOrNullFilter,
)
from InvenTree.helpers import str2bool
from InvenTree.helpers_api import (
    CleanModelViewSet,
    InvenTreeApiRouter,
    RetrieveUpdateDestroyModelViewSet,
)
from InvenTree.mixins import OutputOptionsMixin, SerializerContextMixin
from InvenTree.serializers import EmptySerializer
from users.models import Owner

build_router = InvenTreeApiRouter()


class BuildFilter(FilterSet):
    """Custom filterset for BuildList API endpoint."""

    class Meta:
        """Metaclass options."""

        model = Build
        fields = ['issued_by', 'sales_order', 'external']

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

    @extend_schema_field(serializers.IntegerField(help_text=_('Category')))
    def filter_category(self, queryset, name, category):
        """Filter by part category (including sub-categories)."""
        categories = category.get_descendants(include_self=True)
        return queryset.filter(part__category__in=categories)

    ancestor = rest_filters.ModelChoiceFilter(
        queryset=Build.objects.all(),
        label=_('Ancestor Build'),
        method='filter_ancestor',
    )

    @extend_schema_field(serializers.IntegerField(help_text=_('Ancestor Build')))
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
            return queryset.filter(Build.get_overdue_filter())
        return queryset.exclude(Build.get_overdue_filter())

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

    min_date = InvenTreeDateFilter(label=_('Min Date'), method='filter_min_date')

    def filter_min_date(self, queryset, name, value):
        """Filter the queryset to include orders *after* a specified date.

        This filter is used in combination with filter_max_date,
        to provide a queryset which matches a particular range of dates.

        In particular, this is used in the UI for the calendar view.

        So, we are interested in orders which are active *after* this date:

        - creation_date is set *after* this date (but there is no start date)
        - start_date is set *after* this date
        - target_date is set *after* this date

        """
        q1 = Q(creation_date__gte=value, start_date__isnull=True)
        q2 = Q(start_date__gte=value)
        q3 = Q(target_date__gte=value)

        return queryset.filter(q1 | q2 | q3).distinct()

    max_date = InvenTreeDateFilter(label=_('Max Date'), method='filter_max_date')

    def filter_max_date(self, queryset, name, value):
        """Filter the queryset to include orders *before* a specified date.

        This filter is used in combination with filter_min_date,
        to provide a queryset which matches a particular range of dates.

        In particular, this is used in the UI for the calendar view.

        So, we are interested in orders which are active *before* this date:

        - creation_date is set *before* this date (but there is no start date)
        - start_date is set *before* this date
        - target_date is set *before* this date
        """
        q1 = Q(creation_date__lte=value, start_date__isnull=True)
        q2 = Q(start_date__lte=value)
        q3 = Q(target_date__lte=value)

        return queryset.filter(q1 | q2 | q3).distinct()

    exclude_tree = rest_filters.ModelChoiceFilter(
        queryset=Build.objects.all(),
        method='filter_exclude_tree',
        label=_('Exclude Tree'),
    )

    @extend_schema_field(serializers.IntegerField(help_text=_('Exclude Tree')))
    def filter_exclude_tree(self, queryset, name, value):
        """Filter by excluding a tree of Build objects."""
        queryset = queryset.exclude(
            pk__in=[bld.pk for bld in value.get_descendants(include_self=True)]
        )

        return queryset

    tag_name = common.filters.TagsFilter()


class BuildListOutputOptions(OutputConfiguration):
    """Output options for the BuildList."""

    OPTIONS = [InvenTreeOutputOption('part_detail', default=True)]


def offloaded_task_response(task_id):
    """Return information about a task."""
    response = common.serializers.TaskDetailSerializer.from_task(task_id).data
    return Response(response, status=response['http_status'])


def offloaded_outputs(data):
    """Construct build outputs."""
    return [
        {
            'output_id': item['output'].pk,
            'quantity': float(item['quantity'])
            if item.get('quantity') is not None
            else None,
        }
        for item in data['outputs']
    ]


class BuildViewSet(
    SerializerContextMixin,
    DataExportViewMixin,
    OutputOptionsMixin,
    ParameterListMixin,
    FSMTransitionMixin,
    RetrieveUpdateDestroyModelViewSet,
):
    """API endpoint for accessing Build objects.

    - GET: Return list of objects (with filters)
    - POST: Create a new Build object
    """

    queryset = Build.objects.all()
    serializer_class = build.serializers.BuildSerializer
    lookup_value_regex = '[0-9]+'

    # TODO @matmair remove legacy return codes
    transition_options = {
        'cancel_build': {
            'name': 'cancel',
            'return_code': 201,
            'serializer_class': build.serializers.BuildCancelSerializer,
        },
        'complete_build': {
            'name': 'finish',
            'return_code': 201,
            'serializer_class': build.serializers.BuildCompleteSerializer,
        },
        'hold_build': {
            'name': 'hold',
            'return_code': 201,
            'serializer_class': EmptySerializer,
        },
        'issue_build': {
            'name': 'issue',
            'return_code': 201,
            'serializer_class': EmptySerializer,
        },
    }

    output_options = BuildListOutputOptions
    filterset_class = BuildFilter
    filter_backends = SEARCH_ORDER_FILTER
    ordering_fields = [
        'reference',
        'part',
        'IPN',
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
        'external',
    ]
    ordering_field_aliases = {
        'reference': ['reference_int', 'reference'],
        'project_code': ['project_code__code'],
        'part': ['part__name'],
        'IPN': ['part__IPN'],
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
        """Return the annotated queryset for this endpoint."""
        queryset = super().get_queryset()
        queryset = build.serializers.BuildSerializer.annotate_queryset(queryset)
        return queryset

    def get_serializer(self, *args, **kwargs):
        """Add extra context information to the endpoint serializer."""
        if getattr(self, 'action', 'list') in ['list', 'create']:
            kwargs['create'] = True
        return super().get_serializer(*args, **kwargs)

    def get_build(self) -> Build:
        """Return the Build object associated with this API endpoint."""
        try:
            return Build.objects.get(pk=self.kwargs.get('pk', None))
        except (ValueError, Build.DoesNotExist):
            raise NotFound(_('Build not found'))

    def get_serializer_context(self):
        """Add the Build object to the serializer context."""
        ctx = super().get_serializer_context()

        ctx['request'] = self.request
        ctx['to_complete'] = getattr(self, 'action', None) not in [
            'scrap_outputs',
            'delete_outputs',
        ]

        if self.kwargs.get('pk', None) is not None:
            try:
                ctx['build'] = self.get_build()
            except NotFound:
                pass

        return ctx

    def create(self, request, *args, **kwargs):
        """Save user information on order creation."""
        serializer = self.get_serializer(data=self.clean_data(request.data))
        serializer.is_valid(raise_exception=True)

        serializer.save(issued_by=request.user)

        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

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

    def save_action_serializer(self, request) -> Response:
        """Validate and save the action serializer against the target Build."""
        self.get_build()

        serializer = self.get_serializer(data=self.clean_data(request.data))
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def validated_action_data(self, request):
        """Validate the action serializer and return the target Build and data."""
        build = self.get_build()

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return build, serializer.validated_data

    @action(
        detail=True,
        methods=['post'],
        serializer_class=build.serializers.BuildAllocationSerializer,
        output_options=None,
    )
    def allocate(self, request, pk=None):
        """API endpoint to allocate stock items to a build order.

        - The BuildOrder object is specified by the URL
        - Items to allocate are specified as a list called "items" with the following options:
            - bom_item: pk value of a given BomItem object (must match the part associated with this build)
            - stock_item: pk value of a given StockItem object
            - quantity: quantity to allocate
            - output: StockItem (build order output) to allocate stock against (optional)
        """
        return self.save_action_serializer(request)

    @action(
        detail=True,
        methods=['post'],
        serializer_class=build.serializers.BuildUnallocationSerializer,
        output_options=None,
    )
    def unallocate(self, request, pk=None):
        """API endpoint for unallocating stock items from a build order.

        - The BuildOrder object is specified by the URL
        - "output" (StockItem) can optionally be specified
        - "bom_item" can optionally be specified
        """
        return self.save_action_serializer(request)

    @extend_schema(responses={200: common.serializers.TaskDetailSerializer})
    @action(
        detail=True,
        methods=['post'],
        serializer_class=build.serializers.BuildConsumeSerializer,
        output_options=None,
    )
    def consume(self, request, pk=None):
        """API endpoint to consume stock against a build order.

        As this is offloaded to the background task, we return information about the background task which is performing the consume operation.
        """
        from build.tasks import consume_build_stock
        from InvenTree.tasks import offload_task

        build, data = self.validated_action_data(request)

        # Extract the information we need to consume build stock
        items = data.get('items', [])
        lines = data.get('lines', [])
        notes = data.get('notes', '')

        # Offload the task to the background worker
        task_id = offload_task(
            consume_build_stock,
            build.pk,
            lines=[line['build_line'].pk for line in lines],
            items={item['build_item'].pk: item['quantity'] for item in items},
            user_id=request.user.pk,
            notes=notes,
        )

        return offloaded_task_response(task_id)

    @extend_schema(responses={200: common.serializers.TaskDetailSerializer})
    @action(
        detail=True,
        methods=['post'],
        url_path='auto-allocate',
        url_name='auto-allocate',
        serializer_class=build.serializers.BuildAutoAllocationSerializer,
        output_options=None,
    )
    def auto_allocate(self, request, pk=None):
        """API endpoint for 'automatically' allocating stock against a build order.

        - Only looks at 'untracked' parts
        - If stock exists in a single location, easy!
        - If user decides that stock items are "fungible", allocate against multiple stock items
        - If the user wants to, allocate substitute parts if the primary parts are not available.

        As this is offloaded to the background task, we return information about the background task which is performing the auto allocation operation.
        """
        from build.tasks import auto_allocate_build
        from InvenTree.tasks import offload_task

        build, data = self.validated_action_data(request)

        build_lines = data.get('build_lines', [])

        # Offload the task to the background worker
        task_id = offload_task(
            auto_allocate_build,
            build.pk,
            location=data.get('location', None),
            exclude_location=data.get('exclude_location', None),
            interchangeable=data['interchangeable'],
            substitutes=data['substitutes'],
            optional_items=data['optional_items'],
            item_type=data.get('item_type', 'untracked'),
            stock_sort_by=data['stock_sort_by'],
            line_ids=[line.pk for line in build_lines] if build_lines else None,
            group='build',
        )

        return offloaded_task_response(task_id)

    @extend_schema(responses={200: common.serializers.TaskDetailSerializer})
    @action(
        detail=True,
        methods=['post'],
        url_path='complete',
        url_name='output-complete',
        serializer_class=build.serializers.BuildOutputCompleteSerializer,
        output_options=None,
    )
    def complete_outputs(self, request, pk=None):
        """API endpoint for completing build outputs.

        Build output completion is offloaded to the background worker.
        """
        from build.tasks import complete_build_outputs
        from InvenTree.tasks import offload_task

        build, data = self.validated_action_data(request)

        location = data.get('location')

        task_id = offload_task(
            complete_build_outputs,
            build.pk,
            outputs=offloaded_outputs(data),
            location_id=location.pk if location else None,
            status=data.get('status_custom_key'),
            notes=data.get('notes', ''),
            user_id=request.user.pk,
            group='build',
        )

        return offloaded_task_response(task_id)

    @extend_schema(responses={201: stock.serializers.StockItemSerializer(many=True)})
    @action(
        detail=True,
        methods=['post'],
        url_path='create-output',
        url_name='output-create',
        serializer_class=build.serializers.BuildOutputCreateSerializer,
        pagination_class=None,
        output_options=None,
    )
    def create_output(self, request, pk=None):
        """API endpoint for creating new build output(s)."""
        self.get_build()

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Create the build output(s)
        outputs = serializer.save()

        queryset = stock.serializers.StockItemSerializer.annotate_queryset(outputs)
        response = stock.serializers.StockItemSerializer(queryset, many=True)

        # Return the created outputs
        return Response(response.data, status=status.HTTP_201_CREATED)

    @extend_schema(responses={200: common.serializers.TaskDetailSerializer})
    @action(
        detail=True,
        methods=['post'],
        url_path='delete-outputs',
        url_name='output-delete',
        serializer_class=build.serializers.BuildOutputDeleteSerializer,
        output_options=None,
    )
    def delete_outputs(self, request, pk=None):
        """API endpoint for deleting multiple build outputs.

        Build output deletion is offloaded to the background worker.
        """
        from build.tasks import delete_build_outputs
        from InvenTree.tasks import offload_task

        build, data = self.validated_action_data(request)

        task_id = offload_task(
            delete_build_outputs,
            build.pk,
            output_ids=[item['output'].pk for item in data['outputs']],
            group='build',
        )

        return offloaded_task_response(task_id)

    @extend_schema(responses={200: common.serializers.TaskDetailSerializer})
    @action(
        detail=True,
        methods=['post'],
        url_path='scrap-outputs',
        url_name='output-scrap',
        serializer_class=build.serializers.BuildOutputScrapSerializer,
        output_options=None,
    )
    def scrap_outputs(self, request, pk=None):
        """API endpoint for scrapping build output(s).

        Scrapping is offloaded to the background worker.
        """
        from build.tasks import scrap_build_outputs
        from InvenTree.tasks import offload_task

        build, data = self.validated_action_data(request)

        task_id = offload_task(
            scrap_build_outputs,
            build.pk,
            outputs=offloaded_outputs(data),
            location_id=data['location'].pk,
            notes=data.get('notes', ''),
            discard_allocations=data.get('discard_allocations', False),
            user_id=request.user.pk,
            group='build',
        )

        return offloaded_task_response(task_id)


class BuildLineFilter(FilterSet):
    """Custom filterset for the BuildLine API endpoint."""

    class Meta:
        """Meta information for the BuildLineFilter class."""

        model = BuildLine
        fields = ['build', 'bom_item']

    # Fields on related models
    consumable = rest_filters.BooleanFilter(
        label=_('Consumable'), method='filter_consumable'
    )

    def filter_consumable(self, queryset, name, value):
        """Filter the queryset based on the "effective" consumable status of the BOM item.

        A BuildLine is considered "consumable" if either the BOM item itself,
        or the underlying part, is marked as consumable.
        """
        return queryset.filter(
            part_models.BomItem.consumable_filter(
                consumable=str2bool(value), prefix='bom_item__'
            )
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
        allocated_subquery = (
            BuildItem.objects
            .filter(build_line=OuterRef('pk'))
            .values('build_line')
            .annotate(total=Sum('quantity'))
            .values('total')
        )

        queryset = queryset.alias(
            allocated_quantity=Coalesce(
                Subquery(allocated_subquery), 0, output_field=DecimalField()
            )
        )

        if str2bool(value):
            return queryset.filter(
                allocated_quantity__gte=F('quantity') - F('consumed')
            )
        return queryset.filter(allocated_quantity__lt=F('quantity') - F('consumed'))

    consumed = rest_filters.BooleanFilter(label=_('Consumed'), method='filter_consumed')

    def filter_consumed(self, queryset, name, value):
        """Filter by whether each BuildLine is fully consumed."""
        if str2bool(value):
            return queryset.filter(consumed__gte=F('quantity'))
        return queryset.filter(consumed__lt=F('quantity'))

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
        allocated_subquery = (
            BuildItem.objects
            .filter(build_line=OuterRef('pk'))
            .values('build_line')
            .annotate(total=Sum('quantity'))
            .values('total')
        )

        queryset = queryset.alias(
            allocated_quantity=Coalesce(
                Subquery(allocated_subquery), 0, output_field=DecimalField()
            )
        )

        # A query filter construct to determine the total quantity available for this BuildLine,
        # taking into account any stock which is already allocated or consumed
        available = (
            F('allocated_quantity')
            + F('consumed')
            + F('available_stock')
            + F('available_substitute_stock')
            + F('available_variant_stock')
        )

        if str2bool(value):
            return queryset.filter(quantity__lte=available)

        return queryset.filter(quantity__gt=available)

    on_order = rest_filters.BooleanFilter(label=_('On Order'), method='filter_on_order')

    def filter_on_order(self, queryset, name, value):
        """Filter by whether there is stock on order for each BuildLine."""
        if str2bool(value):
            return queryset.filter(on_order__gt=0)
        else:
            return queryset.filter(on_order=0)


class BuildLineOutputOptions(OutputConfiguration):
    """Output options for BuildLine endpoint."""

    OPTIONS = [
        InvenTreeOutputOption(
            'bom_item_detail',
            description='Include detailed information about the BOM item linked to this build line.',
            default=False,
        ),
        InvenTreeOutputOption(
            'assembly_detail',
            description='Include brief details of the assembly (parent part) related to the BOM item in this build line.',
            default=False,
        ),
        InvenTreeOutputOption(
            'part_detail',
            description='Include detailed information about the specific part being built or consumed in this build line.',
            default=False,
        ),
        InvenTreeOutputOption(
            'build_detail',
            description='Include detailed information about the associated build order.',
            default=False,
        ),
        InvenTreeOutputOption(
            'allocations',
            description='Include allocation details showing which stock items are allocated to this build line.',
            default=False,
        ),
    ]


class BuildLineViewSet(
    SerializerContextMixin, DataExportViewMixin, OutputOptionsMixin, CleanModelViewSet
):
    """API endpoint for accessing a list of BuildLine objects."""

    queryset = BuildLine.objects.all()
    serializer_class = build.serializers.BuildLineSerializer

    filterset_class = BuildLineFilter
    filter_backends = SEARCH_ORDER_FILTER
    output_options = BuildLineOutputOptions
    ordering_fields = [
        'part',
        'IPN',
        'allocated',
        'category',
        'consumed',
        'reference',
        'quantity',
        'consumable',
        'optional',
        'unit_quantity',
        'available_stock',
        'trackable',
        'allow_variants',
        'inherited',
        'on_order',
        'scheduled_to_build',
    ]

    ordering_field_aliases = {
        'part': 'bom_item__sub_part__name',
        'IPN': 'bom_item__sub_part__IPN',
        'reference': 'bom_item__reference',
        'unit_quantity': 'bom_item__quantity',
        'category': 'bom_item__sub_part__category__name',
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
        if getattr(self, 'action', 'list') != 'list':
            return None

        source_build = None

        try:
            build_id = self.request.query_params.get('build', None)
            if build_id:
                source_build = Build.objects.filter(pk=build_id).first()
        except (Build.DoesNotExist, AttributeError, ValueError):
            pass

        return source_build

    def get_queryset(self):
        """Override queryset to select-related and annotate."""
        queryset = super().get_queryset()

        if not hasattr(self, 'source_build'):
            self.source_build = self.get_source_build()

        return build.serializers.BuildLineSerializer.annotate_queryset(
            queryset, build=self.source_build
        )


class BuildItemFilter(FilterSet):
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
        queryset=build_models.Build.objects.all(),
        label=_('Build Order'),
        field_name='build_line__build',
    )

    tracked = rest_filters.BooleanFilter(label='Tracked', method='filter_tracked')

    def filter_tracked(self, queryset, name, value):
        """Filter the queryset based on whether build items are tracked."""
        if str2bool(value):
            return queryset.exclude(install_into=None)
        return queryset.filter(install_into=None)

    location = rest_filters.ModelChoiceFilter(
        queryset=stock_models.StockLocation.objects.all(),
        label=_('Location'),
        method='filter_location',
    )

    @extend_schema_field(serializers.IntegerField(help_text=_('Location')))
    def filter_location(self, queryset, name, location):
        """Filter the queryset based on the specified location."""
        locations = location.get_descendants(include_self=True)
        return queryset.filter(stock_item__location__in=locations)

    output = NumberOrNullFilter(
        field_name='install_into',
        label=_('Output'),
        help_text=_(
            "Filter by output stock item ID. Use 'null' to find uninstalled build items."
        ),
    )


class BuildItemOutputOptions(OutputConfiguration):
    """Output options for BuildItem endpoint."""

    OPTIONS = [
        InvenTreeOutputOption(
            'part_detail',
            default=False,
            description='Include detailed information about the part associated with this build item.',
        ),
        InvenTreeOutputOption(
            'location_detail',
            default=False,
            description='Include detailed information about the location of the allocated stock item.',
        ),
        InvenTreeOutputOption(
            'stock_detail',
            default=False,
            description='Include detailed information about the allocated stock item.',
        ),
        InvenTreeOutputOption(
            'build_detail',
            default=False,
            description='Include detailed information about the associated build order.',
        ),
        InvenTreeOutputOption(
            'supplier_part_detail',
            default=False,
            description='Include detailed information about the supplier part associated with this build item.',
        ),
        InvenTreeOutputOption(
            'install_into_detail',
            default=False,
            description='Include detailed information about the build output for this build item.',
        ),
    ]


class BuildItemViewSet(
    DataExportViewMixin, OutputOptionsMixin, BulkDeleteViewsetMixin, CleanModelViewSet
):
    """API endpoint for accessing BuildItem objects.

    - GET: Return list of objects
    - POST: Create a new BuildItem object
    """

    queryset = BuildItem.objects.all().prefetch_related('stock_item__location')
    serializer_class = build.serializers.BuildItemSerializer

    output_options = BuildItemOutputOptions
    filterset_class = BuildItemFilter
    filter_backends = SEARCH_ORDER_FILTER

    def get_serializer(self, *args, **kwargs):
        """Filter output options application for list endpoint."""
        if getattr(self, 'action', 'list') != 'list':
            self.output_options = None
        return super().get_serializer(*args, **kwargs)

    def get_queryset(self):
        """Override the queryset method, to perform custom prefetch."""
        queryset = super().get_queryset()

        if getattr(self, 'action', 'list') == 'list':
            queryset = queryset.select_related('install_into').prefetch_related(
                'build_line', 'build_line__build', 'build_line__bom_item'
            )

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


build_router.register('line', BuildLineViewSet, basename='api-build-line')
build_router.register('item', BuildItemViewSet, basename='api-build-item')
build_router.register('', BuildViewSet, basename='api-build')


build_api_urls = [
    # Legacy metadata redirects
    path('item/<int:pk>/', include([meta_path(BuildItem)])),
    path('<int:pk>/', include([meta_path(Build)])),
    # Build order status code information
    path(
        'status/',
        StatusView.as_view(),
        {StatusView.MODEL_REF: BuildStatus},
        name='api-build-status-codes',
    ),
    # new router apis
    path('', include(build_router.urls)),
]
