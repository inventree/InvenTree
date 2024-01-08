"""JSON API for the Build app."""

from django.db.models import F, Q
from django.urls import include, path, re_path
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User

from rest_framework.exceptions import ValidationError

from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as rest_filters

from InvenTree.api import AttachmentMixin, APIDownloadMixin, ListCreateDestroyAPIView, MetadataView
from generic.states.api import StatusView
from InvenTree.helpers import str2bool, isNull, DownloadFile
from InvenTree.status_codes import BuildStatus, BuildStatusGroups
from InvenTree.mixins import CreateAPI, RetrieveUpdateDestroyAPI, ListCreateAPI

import common.models
import build.admin
import build.serializers
from build.models import Build, BuildLine, BuildItem, BuildOrderAttachment
import part.models
from users.models import Owner
from InvenTree.filters import SEARCH_ORDER_FILTER_ALIAS


class BuildFilter(rest_filters.FilterSet):
    """Custom filterset for BuildList API endpoint."""

    class Meta:
        """Metaclass options"""
        model = Build
        fields = [
            'parent',
            'sales_order',
            'part',
            'issued_by',
        ]

    status = rest_filters.NumberFilter(label='Status')

    active = rest_filters.BooleanFilter(label='Build is active', method='filter_active')

    def filter_active(self, queryset, name, value):
        """Filter the queryset to either include or exclude orders which are active."""
        if str2bool(value):
            return queryset.filter(status__in=BuildStatusGroups.ACTIVE_CODES)
        return queryset.exclude(status__in=BuildStatusGroups.ACTIVE_CODES)

    overdue = rest_filters.BooleanFilter(label='Build is overdue', method='filter_overdue')

    def filter_overdue(self, queryset, name, value):
        """Filter the queryset to either include or exclude orders which are overdue."""
        if str2bool(value):
            return queryset.filter(Build.OVERDUE_FILTER)
        return queryset.exclude(Build.OVERDUE_FILTER)

    assigned_to_me = rest_filters.BooleanFilter(label='assigned_to_me', method='filter_assigned_to_me')

    def filter_assigned_to_me(self, queryset, name, value):
        """Filter by orders which are assigned to the current user."""
        value = str2bool(value)

        # Work out who "me" is!
        owners = Owner.get_owners_matching_user(self.request.user)

        if value:
            return queryset.filter(responsible__in=owners)
        return queryset.exclude(responsible__in=owners)

    assigned_to = rest_filters.NumberFilter(label='responsible', method='filter_responsible')

    def filter_responsible(self, queryset, name, value):
        """Filter by orders which are assigned to the specified owner."""
        owners = list(Owner.objects.filter(pk=value))

        # if we query by a user, also find all ownerships through group memberships
        if len(owners) > 0 and owners[0].label() == 'user':
            owners = Owner.get_owners_matching_user(User.objects.get(pk=owners[0].owner_id))

        return queryset.filter(responsible__in=owners)

    # Exact match for reference
    reference = rest_filters.CharFilter(
        label='Filter by exact reference',
        field_name='reference',
        lookup_expr="iexact"
    )

    project_code = rest_filters.ModelChoiceFilter(
        queryset=common.models.ProjectCode.objects.all(),
        field_name='project_code'
    )

    has_project_code = rest_filters.BooleanFilter(label='has_project_code', method='filter_has_project_code')

    def filter_has_project_code(self, queryset, name, value):
        """Filter by whether or not the order has a project code"""
        if str2bool(value):
            return queryset.exclude(project_code=None)
        return queryset.filter(project_code=None)


class BuildList(APIDownloadMixin, ListCreateAPI):
    """API endpoint for accessing a list of Build objects.

    - GET: Return list of objects (with filters)
    - POST: Create a new Build object
    """

    queryset = Build.objects.all()
    serializer_class = build.serializers.BuildSerializer
    filterset_class = BuildFilter

    filter_backends = SEARCH_ORDER_FILTER_ALIAS

    ordering_fields = [
        'reference',
        'part__name',
        'status',
        'creation_date',
        'target_date',
        'completion_date',
        'quantity',
        'completed',
        'issued_by',
        'responsible',
        'project_code',
        'priority',
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

    def download_queryset(self, queryset, export_format):
        """Download the queryset data as a file."""
        dataset = build.admin.BuildResource().export(queryset=queryset)

        filedata = dataset.export(export_format)
        filename = f"InvenTree_BuildOrders.{export_format}"

        return DownloadFile(filedata, filename)

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

        # Filter by "ancestor" builds
        ancestor = params.get('ancestor', None)

        if ancestor is not None:
            try:
                ancestor = Build.objects.get(pk=ancestor)

                descendants = ancestor.get_descendants(include_self=True)

                queryset = queryset.filter(
                    parent__pk__in=[b.pk for b in descendants]
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
            part_detail = str2bool(self.request.GET.get('part_detail', None))
        except AttributeError:
            part_detail = None

        kwargs['part_detail'] = part_detail

        return self.serializer_class(*args, **kwargs)


class BuildDetail(RetrieveUpdateDestroyAPI):
    """API endpoint for detail view of a Build object."""

    queryset = Build.objects.all()
    serializer_class = build.serializers.BuildSerializer

    def destroy(self, request, *args, **kwargs):
        """Only allow deletion of a BuildOrder if the build status is CANCELLED"""
        build = self.get_object()

        if build.status != BuildStatus.CANCELLED:
            raise ValidationError({
                "non_field_errors": [_("Build must be cancelled before it can be deleted")]
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
        fields = [
            'build',
            'bom_item',
        ]

    # Fields on related models
    consumable = rest_filters.BooleanFilter(label=_('Consumable'), field_name='bom_item__consumable')
    optional = rest_filters.BooleanFilter(label=_('Optional'), field_name='bom_item__optional')
    tracked = rest_filters.BooleanFilter(label=_('Tracked'), field_name='bom_item__sub_part__trackable')

    allocated = rest_filters.BooleanFilter(label=_('Allocated'), method='filter_allocated')

    def filter_allocated(self, queryset, name, value):
        """Filter by whether each BuildLine is fully allocated"""
        if str2bool(value):
            return queryset.filter(allocated__gte=F('quantity'))
        return queryset.filter(allocated__lt=F('quantity'))

    available = rest_filters.BooleanFilter(label=_('Available'), method='filter_available')

    def filter_available(self, queryset, name, value):
        """Filter by whether there is sufficient stock available for each BuildLine:

        To determine this, we need to know:

        - The quantity required for each BuildLine
        - The quantity available for each BuildLine
        - The quantity allocated for each BuildLine
        """
        flt = Q(quantity__lte=F('total_available_stock') + F('allocated'))

        if str2bool(value):
            return queryset.filter(flt)
        return queryset.exclude(flt)


class BuildLineEndpoint:
    """Mixin class for BuildLine API endpoints."""

    queryset = BuildLine.objects.all()
    serializer_class = build.serializers.BuildLineSerializer

    def get_queryset(self):
        """Override queryset to select-related and annotate"""
        queryset = super().get_queryset()

        queryset = build.serializers.BuildLineSerializer.annotate_queryset(queryset)

        return queryset


class BuildLineList(BuildLineEndpoint, ListCreateAPI):
    """API endpoint for accessing a list of BuildLine objects"""

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
    ]

    ordering_field_aliases = {
        'part': 'bom_item__sub_part__name',
        'reference': 'bom_item__reference',
        'unit_quantity': 'bom_item__quantity',
        'consumable': 'bom_item__consumable',
        'optional': 'bom_item__optional',
    }

    search_fields = [
        'bom_item__sub_part__name',
        'bom_item__reference',
    ]


class BuildLineDetail(BuildLineEndpoint, RetrieveUpdateDestroyAPI):
    """API endpoint for detail view of a BuildLine object."""
    pass


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


class BuildCancel(BuildOrderContextMixin, CreateAPI):
    """API endpoint for cancelling a BuildOrder."""

    queryset = Build.objects.all()
    serializer_class = build.serializers.BuildCancelSerializer


class BuildItemDetail(RetrieveUpdateDestroyAPI):
    """API endpoint for detail view of a BuildItem object."""

    queryset = BuildItem.objects.all()
    serializer_class = build.serializers.BuildItemSerializer


class BuildItemFilter(rest_filters.FilterSet):
    """Custom filterset for the BuildItemList API endpoint"""

    class Meta:
        """Metaclass option"""
        model = BuildItem
        fields = [
            'build_line',
            'stock_item',
            'install_into',
        ]

    part = rest_filters.ModelChoiceFilter(
        queryset=part.models.Part.objects.all(),
        field_name='stock_item__part',
    )

    build = rest_filters.ModelChoiceFilter(
        queryset=build.models.Build.objects.all(),
        field_name='build_line__build',
    )

    tracked = rest_filters.BooleanFilter(label='Tracked', method='filter_tracked')

    def filter_tracked(self, queryset, name, value):
        """Filter the queryset based on whether build items are tracked"""
        if str2bool(value):
            return queryset.exclude(install_into=None)
        return queryset.filter(install_into=None)


class BuildItemList(ListCreateAPI):
    """API endpoint for accessing a list of BuildItem objects.

    - GET: Return list of objects
    - POST: Create a new BuildItem object
    """

    serializer_class = build.serializers.BuildItemSerializer
    filterset_class = BuildItemFilter

    def get_serializer(self, *args, **kwargs):
        """Returns a BuildItemSerializer instance based on the request."""
        try:
            params = self.request.query_params

            for key in ['part_detail', 'location_detail', 'stock_detail', 'build_detail']:
                if key in params:
                    kwargs[key] = str2bool(params.get(key, False))
        except AttributeError:
            pass

        return self.serializer_class(*args, **kwargs)

    def get_queryset(self):
        """Override the queryset method, to allow filtering by stock_item.part."""
        queryset = BuildItem.objects.all()

        queryset = queryset.select_related(
            'build_line',
            'build_line__build',
            'install_into',
            'stock_item',
            'stock_item__location',
            'stock_item__part',
        )

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

    filter_backends = [
        DjangoFilterBackend,
    ]


class BuildAttachmentList(AttachmentMixin, ListCreateDestroyAPIView):
    """API endpoint for listing (and creating) BuildOrderAttachment objects."""

    queryset = BuildOrderAttachment.objects.all()
    serializer_class = build.serializers.BuildAttachmentSerializer

    filterset_fields = [
        'build',
    ]


class BuildAttachmentDetail(AttachmentMixin, RetrieveUpdateDestroyAPI):
    """Detail endpoint for a BuildOrderAttachment object."""

    queryset = BuildOrderAttachment.objects.all()
    serializer_class = build.serializers.BuildAttachmentSerializer


build_api_urls = [

    # Attachments
    path('attachment/', include([
        path(r'<int:pk>/', BuildAttachmentDetail.as_view(), name='api-build-attachment-detail'),
        re_path(r'^.*$', BuildAttachmentList.as_view(), name='api-build-attachment-list'),
    ])),

    # Build lines
    path('line/', include([
        path(r'<int:pk>/', BuildLineDetail.as_view(), name='api-build-line-detail'),
        re_path(r'^.*$', BuildLineList.as_view(), name='api-build-line-list'),
    ])),

    # Build Items
    path('item/', include([
        path(r'<int:pk>/', include([
            re_path(r'^metadata/', MetadataView.as_view(), {'model': BuildItem}, name='api-build-item-metadata'),
            re_path(r'^.*$', BuildItemDetail.as_view(), name='api-build-item-detail'),
        ])),
        re_path(r'^.*$', BuildItemList.as_view(), name='api-build-item-list'),
    ])),

    # Build Detail
    path(r'<int:pk>/', include([
        re_path(r'^allocate/', BuildAllocate.as_view(), name='api-build-allocate'),
        re_path(r'^auto-allocate/', BuildAutoAllocate.as_view(), name='api-build-auto-allocate'),
        re_path(r'^complete/', BuildOutputComplete.as_view(), name='api-build-output-complete'),
        re_path(r'^create-output/', BuildOutputCreate.as_view(), name='api-build-output-create'),
        re_path(r'^delete-outputs/', BuildOutputDelete.as_view(), name='api-build-output-delete'),
        re_path(r'^scrap-outputs/', BuildOutputScrap.as_view(), name='api-build-output-scrap'),
        re_path(r'^finish/', BuildFinish.as_view(), name='api-build-finish'),
        re_path(r'^cancel/', BuildCancel.as_view(), name='api-build-cancel'),
        re_path(r'^unallocate/', BuildUnallocate.as_view(), name='api-build-unallocate'),
        re_path(r'^metadata/', MetadataView.as_view(), {'model': Build}, name='api-build-metadata'),
        re_path(r'^.*$', BuildDetail.as_view(), name='api-build-detail'),
    ])),

    # Build order status code information
    re_path(r'status/', StatusView.as_view(), {StatusView.MODEL_REF: BuildStatus}, name='api-build-status-codes'),

    # Build List
    re_path(r'^.*$', BuildList.as_view(), name='api-build-list'),
]
