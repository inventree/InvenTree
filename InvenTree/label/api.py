"""API functionality for the 'label' app"""

from django.core.exceptions import FieldError, ValidationError
from django.http import JsonResponse
from django.urls import include, path, re_path
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page, never_cache

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import serializers
from rest_framework.exceptions import NotFound
from rest_framework.request import clone_request

import build.models
import common.models
import InvenTree.helpers
import label.models
import label.serializers
from InvenTree.api import MetadataView
from InvenTree.filters import InvenTreeSearchFilter
from InvenTree.mixins import (ListCreateAPI, RetrieveAPI,
                              RetrieveUpdateDestroyAPI)
from part.models import Part
from plugin.builtin.labels.inventree_label import InvenTreeLabelPlugin
from plugin.registry import registry
from stock.models import StockItem, StockLocation


class LabelFilterMixin:
    """Mixin for filtering a queryset by a list of object ID values.

    Each implementing class defines a database model to lookup,
    and a "key" (query parameter) for providing a list of ID (PK) values.

    This mixin defines a 'get_items' method which provides a generic
    implementation to return a list of matching database model instances.
    """

    # Database model for instances to actually be "printed" against this label template
    ITEM_MODEL = None

    # Default key for looking up database model instances
    ITEM_KEY = 'item'

    def get_items(self):
        """Return a list of database objects from query parameter"""
        ids = []

        # Construct a list of possible query parameter value options
        # e.g. if self.ITEM_KEY = 'part' -> ['part', 'part[]', 'parts', parts[]']
        for k in [self.ITEM_KEY + x for x in ['', '[]', 's', 's[]']]:
            if ids := self.request.query_params.getlist(k, []):
                # Return the first list of matches
                break

        # Next we must validate each provided object ID
        valid_ids = []

        for id in ids:
            try:
                valid_ids.append(int(id))
            except (ValueError):
                pass

        # Filter queryset by matching ID values
        return self.ITEM_MODEL.objects.filter(pk__in=valid_ids)


class LabelListView(LabelFilterMixin, ListCreateAPI):
    """Generic API class for label templates."""

    def filter_queryset(self, queryset):
        """Filter the queryset based on the provided label ID values.

        As each 'label' instance may optionally define its own filters,
        the resulting queryset is the 'union' of the two.
        """
        queryset = super().filter_queryset(queryset)

        items = self.get_items()

        if len(items) > 0:
            """
            At this point, we are basically forced to be inefficient,
            as we need to compare the 'filters' string of each label,
            and see if it matches against each of the requested items.

            TODO: In the future, if this becomes excessively slow, it
                  will need to be readdressed.
            """
            valid_label_ids = set()

            for lbl in queryset.all():
                matches = True

                try:
                    filters = InvenTree.helpers.validateFilterString(lbl.filters)
                except ValidationError:
                    continue

                for item in items:
                    item_query = self.ITEM_MODEL.objects.filter(pk=item.pk)

                    try:
                        if not item_query.filter(**filters).exists():
                            matches = False
                            break
                    except FieldError:
                        matches = False
                        break

                # Matched all items
                if matches:
                    valid_label_ids.add(lbl.pk)
                else:
                    continue

            # Reduce queryset to only valid matches
            queryset = queryset.filter(pk__in=list(valid_label_ids))

        return queryset

    filter_backends = [
        DjangoFilterBackend,
        InvenTreeSearchFilter
    ]

    filterset_fields = [
        'enabled',
    ]

    search_fields = [
        'name',
        'description',
    ]


@method_decorator(cache_page(5), name='dispatch')
class LabelPrintMixin(LabelFilterMixin):
    """Mixin for printing labels."""

    rolemap = {
        "GET": "view",
        "POST": "view",
    }

    def check_permissions(self, request):
        """Override request method to GET so that also non superusers can print using a post request."""
        if request.method == "POST":
            request = clone_request(request, "GET")
        return super().check_permissions(request)

    @method_decorator(never_cache)
    def dispatch(self, *args, **kwargs):
        """Prevent caching when printing report templates"""
        return super().dispatch(*args, **kwargs)

    def get_serializer(self, *args, **kwargs):
        """Define a get_serializer method to be discoverable by the OPTIONS request."""
        # Check the request to determine if the user has selected a label printing plugin
        plugin = self.get_plugin(self.request)

        kwargs.setdefault('context', self.get_serializer_context())
        serializer = plugin.get_printing_options_serializer(self.request, *args, **kwargs)

        # if no serializer is defined, return an empty serializer
        if not serializer:
            return serializers.Serializer()

        return serializer

    def get(self, request, *args, **kwargs):
        """Perform a GET request against this endpoint to print labels"""
        common.models.InvenTreeUserSetting.set_setting('DEFAULT_' + self.ITEM_KEY.upper() + '_LABEL_TEMPLATE',
                                                       self.get_object().pk, None, user=request.user)
        return self.print(request, self.get_items())

    def post(self, request, *args, **kwargs):
        """Perform a GET request against this endpoint to print labels"""
        return self.get(request, *args, **kwargs)

    def get_plugin(self, request):
        """Return the label printing plugin associated with this request.

        This is provided in the url, e.g. ?plugin=myprinter

        Requires:
        - settings.PLUGINS_ENABLED is True
        - matching plugin can be found
        - matching plugin implements the 'labels' mixin
        - matching plugin is enabled
        """
        plugin_key = request.query_params.get('plugin', None)

        # No plugin provided!
        if plugin_key is None:
            # Default to the builtin label printing plugin
            plugin_key = InvenTreeLabelPlugin.NAME.lower()

        plugin = registry.get_plugin(plugin_key)

        if not plugin:
            raise NotFound(f"Plugin '{plugin_key}' not found")

        if not plugin.is_active():
            raise ValidationError(f"Plugin '{plugin_key}' is not enabled")

        if not plugin.mixin_enabled("labels"):
            raise ValidationError(f"Plugin '{plugin_key}' is not a label printing plugin")

        # Only return the plugin if it is enabled and has the label printing mixin
        return plugin

    def print(self, request, items_to_print):
        """Print this label template against a number of pre-validated items."""
        # Check the request to determine if the user has selected a label printing plugin
        plugin = self.get_plugin(request)

        if len(items_to_print) == 0:
            # No valid items provided, return an error message
            raise ValidationError('No valid objects provided to label template')

        # Label template
        label = self.get_object()

        # Check the label dimensions
        if label.width <= 0 or label.height <= 0:
            raise ValidationError('Label has invalid dimensions')

        # if the plugin returns a serializer, validate the data
        if serializer := plugin.get_printing_options_serializer(request, data=request.data, context=self.get_serializer_context()):
            serializer.is_valid(raise_exception=True)

        # At this point, we offload the label(s) to the selected plugin.
        # The plugin is responsible for handling the request and returning a response.

        result = plugin.print_labels(label, items_to_print, request, printing_options=request.data)

        if isinstance(result, JsonResponse):
            result['plugin'] = plugin.plugin_slug()
            return result
        raise ValidationError(f"Plugin '{plugin.plugin_slug()}' returned invalid response type '{type(result)}'")


class StockItemLabelMixin:
    """Mixin for StockItemLabel endpoints"""

    queryset = label.models.StockItemLabel.objects.all()
    serializer_class = label.serializers.StockItemLabelSerializer

    ITEM_MODEL = StockItem
    ITEM_KEY = 'item'


class StockItemLabelList(StockItemLabelMixin, LabelListView):
    """API endpoint for viewing list of StockItemLabel objects.

    Filterable by:

    - enabled: Filter by enabled / disabled status
    - item: Filter by single stock item
    - items: Filter by list of stock items
    """
    pass


class StockItemLabelDetail(StockItemLabelMixin, RetrieveUpdateDestroyAPI):
    """API endpoint for a single StockItemLabel object."""
    pass


class StockItemLabelPrint(StockItemLabelMixin, LabelPrintMixin, RetrieveAPI):
    """API endpoint for printing a StockItemLabel object."""
    pass


class StockLocationLabelMixin:
    """Mixin for StockLocationLabel endpoints"""

    queryset = label.models.StockLocationLabel.objects.all()
    serializer_class = label.serializers.StockLocationLabelSerializer

    ITEM_MODEL = StockLocation
    ITEM_KEY = 'location'


class StockLocationLabelList(StockLocationLabelMixin, LabelListView):
    """API endpoint for viewiing list of StockLocationLabel objects.

    Filterable by:

    - enabled: Filter by enabled / disabled status
    - location: Filter by a single stock location
    - locations: Filter by list of stock locations
    """
    pass


class StockLocationLabelDetail(StockLocationLabelMixin, RetrieveUpdateDestroyAPI):
    """API endpoint for a single StockLocationLabel object."""
    pass


class StockLocationLabelPrint(StockLocationLabelMixin, LabelPrintMixin, RetrieveAPI):
    """API endpoint for printing a StockLocationLabel object."""
    pass


class PartLabelMixin:
    """Mixin for PartLabel endpoints"""
    queryset = label.models.PartLabel.objects.all()
    serializer_class = label.serializers.PartLabelSerializer

    ITEM_MODEL = Part
    ITEM_KEY = 'part'


class PartLabelList(PartLabelMixin, LabelListView):
    """API endpoint for viewing list of PartLabel objects."""
    pass


class PartLabelDetail(PartLabelMixin, RetrieveUpdateDestroyAPI):
    """API endpoint for a single PartLabel object."""
    pass


class PartLabelPrint(PartLabelMixin, LabelPrintMixin, RetrieveAPI):
    """API endpoint for printing a PartLabel object."""
    pass


class BuildLineLabelMixin:
    """Mixin class for BuildLineLabel endpoints"""

    queryset = label.models.BuildLineLabel.objects.all()
    serializer_class = label.serializers.BuildLineLabelSerializer

    ITEM_MODEL = build.models.BuildLine
    ITEM_KEY = 'line'


class BuildLineLabelList(BuildLineLabelMixin, LabelListView):
    """API endpoint for viewing a list of BuildLineLabel objects"""
    pass


class BuildLineLabelDetail(BuildLineLabelMixin, RetrieveUpdateDestroyAPI):
    """API endpoint for a single BuildLineLabel object"""
    pass


class BuildLineLabelPrint(BuildLineLabelMixin, LabelPrintMixin, RetrieveAPI):
    """API endpoint for printing a BuildLineLabel object"""
    pass


label_api_urls = [

    # Stock item labels
    re_path(r'stock/', include([
        # Detail views
        path(r'<int:pk>/', include([
            re_path(r'print/?', StockItemLabelPrint.as_view(), name='api-stockitem-label-print'),
            re_path(r'metadata/', MetadataView.as_view(), {'model': label.models.StockItemLabel}, name='api-stockitem-label-metadata'),
            re_path(r'^.*$', StockItemLabelDetail.as_view(), name='api-stockitem-label-detail'),
        ])),

        # List view
        re_path(r'^.*$', StockItemLabelList.as_view(), name='api-stockitem-label-list'),
    ])),

    # Stock location labels
    re_path(r'location/', include([
        # Detail views
        path(r'<int:pk>/', include([
            re_path(r'print/?', StockLocationLabelPrint.as_view(), name='api-stocklocation-label-print'),
            re_path(r'metadata/', MetadataView.as_view(), {'model': label.models.StockLocationLabel}, name='api-stocklocation-label-metadata'),
            re_path(r'^.*$', StockLocationLabelDetail.as_view(), name='api-stocklocation-label-detail'),
        ])),

        # List view
        re_path(r'^.*$', StockLocationLabelList.as_view(), name='api-stocklocation-label-list'),
    ])),

    # Part labels
    re_path(r'^part/', include([
        # Detail views
        path(r'<int:pk>/', include([
            re_path(r'^print/', PartLabelPrint.as_view(), name='api-part-label-print'),
            re_path(r'^metadata/', MetadataView.as_view(), {'model': label.models.PartLabel}, name='api-part-label-metadata'),
            re_path(r'^.*$', PartLabelDetail.as_view(), name='api-part-label-detail'),
        ])),

        # List view
        re_path(r'^.*$', PartLabelList.as_view(), name='api-part-label-list'),
    ])),

    # BuildLine labels
    re_path(r'^buildline/', include([
        # Detail views
        path(r'<int:pk>/', include([
            re_path(r'^print/', BuildLineLabelPrint.as_view(), name='api-buildline-label-print'),
            re_path(r'^metadata/', MetadataView.as_view(), {'model': label.models.BuildLineLabel}, name='api-buildline-label-metadata'),
            re_path(r'^.*$', BuildLineLabelDetail.as_view(), name='api-buildline-label-detail'),
        ])),

        # List view
        re_path(r'^.*$', BuildLineLabelList.as_view(), name='api-buildline-label-list'),
    ])),
]
