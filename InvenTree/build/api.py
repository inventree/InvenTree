"""JSON API for the Build app."""

from django.urls import include, re_path

from rest_framework import filters, generics

from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as rest_filters

from InvenTree.api import AttachmentMixin, APIDownloadMixin
from InvenTree.helpers import str2bool, isNull, DownloadFile
from InvenTree.filters import InvenTreeOrderingFilter
from InvenTree.status_codes import BuildStatus

import build.admin
import build.serializers
from build.models import Build, BuildItem, BuildOrderAttachment

from users.models import Owner


class BuildFilter(rest_filters.FilterSet):
    """Custom filterset for BuildList API endpoint."""

    status = rest_filters.NumberFilter(label='Status')

    active = rest_filters.BooleanFilter(label='Build is active', method='filter_active')

    def filter_active(self, queryset, name, value):
        """Filter the queryset to either include or exclude orders which are active."""
        if str2bool(value):
            queryset = queryset.filter(status__in=BuildStatus.ACTIVE_CODES)
        else:
            queryset = queryset.exclude(status__in=BuildStatus.ACTIVE_CODES)

        return queryset

    overdue = rest_filters.BooleanFilter(label='Build is overdue', method='filter_overdue')

    def filter_overdue(self, queryset, name, value):
        """Filter the queryset to either include or exclude orders which are overdue."""
        if str2bool(value):
            queryset = queryset.filter(Build.OVERDUE_FILTER)
        else:
            queryset = queryset.exclude(Build.OVERDUE_FILTER)

        return queryset

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


class BuildList(APIDownloadMixin, generics.ListCreateAPIView):
    """API endpoint for accessing a list of Build objects.

    - GET: Return list of objects (with filters)
    - POST: Create a new Build object
    """

    queryset = Build.objects.all()
    serializer_class = build.serializers.BuildSerializer
    filterset_class = BuildFilter

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        InvenTreeOrderingFilter,
    ]

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
    ]

    ordering_field_aliases = {
        'reference': ['reference_int', 'reference'],
    }

    search_fields = [
        'reference',
        'part__name',
        'title',
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

        # Filter by "parent"
        parent = params.get('parent', None)

        if parent is not None:
            queryset = queryset.filter(parent=parent)

        # Filter by sales_order
        sales_order = params.get('sales_order', None)

        if sales_order is not None:
            queryset = queryset.filter(sales_order=sales_order)

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

        # Filter by associated part?
        part = params.get('part', None)

        if part is not None:
            queryset = queryset.filter(part=part)

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


class BuildDetail(generics.RetrieveUpdateAPIView):
    """API endpoint for detail view of a Build object."""

    queryset = Build.objects.all()
    serializer_class = build.serializers.BuildSerializer


class BuildUnallocate(generics.CreateAPIView):
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
        except:
            pass

        ctx['request'] = self.request

        return ctx


class BuildOrderContextMixin:
    """Mixin class which adds build order as serializer context variable."""

    def get_serializer_context(self):
        """Add extra context information to the endpoint serializer."""
        ctx = super().get_serializer_context()

        ctx['request'] = self.request
        ctx['to_complete'] = True

        try:
            ctx['build'] = Build.objects.get(pk=self.kwargs.get('pk', None))
        except:
            pass

        return ctx


class BuildOutputCreate(BuildOrderContextMixin, generics.CreateAPIView):
    """API endpoint for creating new build output(s)."""

    queryset = Build.objects.none()

    serializer_class = build.serializers.BuildOutputCreateSerializer


class BuildOutputComplete(BuildOrderContextMixin, generics.CreateAPIView):
    """API endpoint for completing build outputs."""

    queryset = Build.objects.none()

    serializer_class = build.serializers.BuildOutputCompleteSerializer


class BuildOutputDelete(BuildOrderContextMixin, generics.CreateAPIView):
    """API endpoint for deleting multiple build outputs."""

    def get_serializer_context(self):
        """Add extra context information to the endpoint serializer."""
        ctx = super().get_serializer_context()

        ctx['to_complete'] = False

        return ctx

    queryset = Build.objects.none()

    serializer_class = build.serializers.BuildOutputDeleteSerializer


class BuildFinish(BuildOrderContextMixin, generics.CreateAPIView):
    """API endpoint for marking a build as finished (completed)."""

    queryset = Build.objects.none()

    serializer_class = build.serializers.BuildCompleteSerializer


class BuildAutoAllocate(BuildOrderContextMixin, generics.CreateAPIView):
    """API endpoint for 'automatically' allocating stock against a build order.

    - Only looks at 'untracked' parts
    - If stock exists in a single location, easy!
    - If user decides that stock items are "fungible", allocate against multiple stock items
    - If the user wants to, allocate substite parts if the primary parts are not available.
    """

    queryset = Build.objects.none()

    serializer_class = build.serializers.BuildAutoAllocationSerializer


class BuildAllocate(BuildOrderContextMixin, generics.CreateAPIView):
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


class BuildCancel(BuildOrderContextMixin, generics.CreateAPIView):
    """API endpoint for cancelling a BuildOrder."""

    queryset = Build.objects.all()
    serializer_class = build.serializers.BuildCancelSerializer


class BuildItemDetail(generics.RetrieveUpdateDestroyAPIView):
    """API endpoint for detail view of a BuildItem object."""

    queryset = BuildItem.objects.all()
    serializer_class = build.serializers.BuildItemSerializer


class BuildItemList(generics.ListCreateAPIView):
    """API endpoint for accessing a list of BuildItem objects.

    - GET: Return list of objects
    - POST: Create a new BuildItem object
    """

    serializer_class = build.serializers.BuildItemSerializer

    def get_serializer(self, *args, **kwargs):
        """Returns a BuildItemSerializer instance based on the request."""
        try:
            params = self.request.query_params

            kwargs['part_detail'] = str2bool(params.get('part_detail', False))
            kwargs['build_detail'] = str2bool(params.get('build_detail', False))
            kwargs['location_detail'] = str2bool(params.get('location_detail', False))
        except AttributeError:
            pass

        return self.serializer_class(*args, **kwargs)

    def get_queryset(self):
        """Override the queryset method, to allow filtering by stock_item.part."""
        query = BuildItem.objects.all()

        query = query.select_related('stock_item__location')
        query = query.select_related('stock_item__part')
        query = query.select_related('stock_item__part__category')

        return query

    def filter_queryset(self, queryset):
        """Customm query filtering for the BuildItem list."""
        queryset = super().filter_queryset(queryset)

        params = self.request.query_params

        # Does the user wish to filter by part?
        part_pk = params.get('part', None)

        if part_pk:
            queryset = queryset.filter(stock_item__part=part_pk)

        # Filter by "tracked" status
        # Tracked means that the item is "installed" into a build output (stock item)
        tracked = params.get('tracked', None)

        if tracked is not None:
            tracked = str2bool(tracked)

            if tracked:
                queryset = queryset.exclude(install_into=None)
            else:
                queryset = queryset.filter(install_into=None)

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

    filter_fields = [
        'build',
        'stock_item',
        'bom_item',
        'install_into',
    ]


class BuildAttachmentList(generics.ListCreateAPIView, AttachmentMixin):
    """API endpoint for listing (and creating) BuildOrderAttachment objects."""

    queryset = BuildOrderAttachment.objects.all()
    serializer_class = build.serializers.BuildAttachmentSerializer

    filter_backends = [
        DjangoFilterBackend,
    ]

    filter_fields = [
        'build',
    ]


class BuildAttachmentDetail(generics.RetrieveUpdateDestroyAPIView, AttachmentMixin):
    """Detail endpoint for a BuildOrderAttachment object."""

    queryset = BuildOrderAttachment.objects.all()
    serializer_class = build.serializers.BuildAttachmentSerializer


build_api_urls = [

    # Attachments
    re_path(r'^attachment/', include([
        re_path(r'^(?P<pk>\d+)/', BuildAttachmentDetail.as_view(), name='api-build-attachment-detail'),
        re_path(r'^.*$', BuildAttachmentList.as_view(), name='api-build-attachment-list'),
    ])),

    # Build Items
    re_path(r'^item/', include([
        re_path(r'^(?P<pk>\d+)/', BuildItemDetail.as_view(), name='api-build-item-detail'),
        re_path(r'^.*$', BuildItemList.as_view(), name='api-build-item-list'),
    ])),

    # Build Detail
    re_path(r'^(?P<pk>\d+)/', include([
        re_path(r'^allocate/', BuildAllocate.as_view(), name='api-build-allocate'),
        re_path(r'^auto-allocate/', BuildAutoAllocate.as_view(), name='api-build-auto-allocate'),
        re_path(r'^complete/', BuildOutputComplete.as_view(), name='api-build-output-complete'),
        re_path(r'^create-output/', BuildOutputCreate.as_view(), name='api-build-output-create'),
        re_path(r'^delete-outputs/', BuildOutputDelete.as_view(), name='api-build-output-delete'),
        re_path(r'^finish/', BuildFinish.as_view(), name='api-build-finish'),
        re_path(r'^cancel/', BuildCancel.as_view(), name='api-build-cancel'),
        re_path(r'^unallocate/', BuildUnallocate.as_view(), name='api-build-unallocate'),
        re_path(r'^.*$', BuildDetail.as_view(), name='api-build-detail'),
    ])),

    # Build List
    re_path(r'^.*$', BuildList.as_view(), name='api-build-list'),
]
