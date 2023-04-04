"""API functionality for the 'label' app"""

from django.conf import settings
from django.core.exceptions import FieldError, ValidationError
from django.http import HttpResponse, JsonResponse
from django.urls import include, path, re_path
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page, never_cache

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.exceptions import NotFound

import common.models
import InvenTree.helpers
from InvenTree.api import MetadataView
from InvenTree.filters import InvenTreeSearchFilter
from InvenTree.mixins import ListAPI, RetrieveAPI, RetrieveUpdateDestroyAPI
from InvenTree.tasks import offload_task
from part.models import Part
from plugin.base.label import label as plugin_label
from plugin.registry import registry
from stock.models import StockItem, StockLocation

from .models import PartLabel, StockItemLabel, StockLocationLabel
from .serializers import (PartLabelSerializer, StockItemLabelSerializer,
                          StockLocationLabelSerializer)


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


class LabelListView(LabelFilterMixin, ListAPI):
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

            for label in queryset.all():
                matches = True

                try:
                    filters = InvenTree.helpers.validateFilterString(label.filters)
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
                    valid_label_ids.add(label.pk)
                else:
                    continue

            # Reduce queryset to only valid matches
            queryset = queryset.filter(pk__in=[pk for pk in valid_label_ids])

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

    @method_decorator(never_cache)
    def dispatch(self, *args, **kwargs):
        """Prevent caching when printing report templates"""
        return super().dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        """Perform a GET request against this endpoint to print labels"""
        return self.print(request, self.get_items())

    def get_plugin(self, request):
        """Return the label printing plugin associated with this request.

        This is provided in the url, e.g. ?plugin=myprinter

        Requires:
        - settings.PLUGINS_ENABLED is True
        - matching plugin can be found
        - matching plugin implements the 'labels' mixin
        - matching plugin is enabled
        """
        if not settings.PLUGINS_ENABLED:
            return None  # pragma: no cover

        plugin_key = request.query_params.get('plugin', None)

        # No plugin provided, and that's OK
        if plugin_key is None:
            return None

        plugin = registry.get_plugin(plugin_key)

        if plugin:
            if plugin.is_active():
                # Only return the plugin if it is enabled!
                return plugin
            else:
                raise ValidationError(f"Plugin '{plugin_key}' is not enabled")
        else:
            raise NotFound(f"Plugin '{plugin_key}' not found")

    def print(self, request, items_to_print):
        """Print this label template against a number of pre-validated items."""
        # Check the request to determine if the user has selected a label printing plugin
        plugin = self.get_plugin(request)

        if len(items_to_print) == 0:
            # No valid items provided, return an error message

            raise ValidationError('No valid objects provided to label template')

        outputs = []

        # In debug mode, generate single HTML output, rather than PDF
        debug_mode = common.models.InvenTreeSetting.get_setting('REPORT_DEBUG_MODE', cache=False)

        label_name = "label.pdf"

        label_names = []
        label_instances = []

        # Merge one or more PDF files into a single download
        for item in items_to_print:
            label = self.get_object()
            label.object_to_print = item

            label_name = label.generate_filename(request)

            label_names.append(label_name)
            label_instances.append(label)

            if debug_mode:
                outputs.append(label.render_as_string(request))
            else:
                outputs.append(label.render(request))

        if not label_name.endswith(".pdf"):
            label_name += ".pdf"

        if plugin is not None:
            """Label printing is to be handled by a plugin, rather than being exported to PDF.

            In this case, we do the following:

            - Individually generate each label, exporting as an image file
            - Pass all the images through to the label printing plugin
            - Return a JSON response indicating that the printing has been offloaded
            """

            for idx, output in enumerate(outputs):
                """For each output, we generate a temporary image file, which will then get sent to the printer."""

                # Generate PDF data for the label
                pdf = output.get_document().write_pdf()

                # Offload a background task to print the provided label
                offload_task(
                    plugin_label.print_label,
                    plugin.plugin_slug(),
                    pdf,
                    filename=label_names[idx],
                    label_instance=label_instances[idx],
                    user=request.user,
                )

            return JsonResponse({
                'plugin': plugin.plugin_slug(),
                'labels': label_names,
            })

        elif debug_mode:
            """Contatenate all rendered templates into a single HTML string, and return the string as a HTML response."""

            html = "\n".join(outputs)

            return HttpResponse(html)

        else:
            """Concatenate all rendered pages into a single PDF object, and return the resulting document!"""

            pages = []

            for output in outputs:
                doc = output.get_document()
                for page in doc.pages:
                    pages.append(page)

            pdf = outputs[0].get_document().copy(pages).write_pdf()

            inline = common.models.InvenTreeUserSetting.get_setting('LABEL_INLINE', user=request.user, cache=False)

            return InvenTree.helpers.DownloadFile(
                pdf,
                label_name,
                content_type='application/pdf',
                inline=inline
            )


class StockItemLabelMixin:
    """Mixin for StockItemLabel endpoints"""

    queryset = StockItemLabel.objects.all()
    serializer_class = StockItemLabelSerializer

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

    queryset = StockLocationLabel.objects.all()
    serializer_class = StockLocationLabelSerializer

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
    queryset = PartLabel.objects.all()
    serializer_class = PartLabelSerializer

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


label_api_urls = [

    # Stock item labels
    re_path(r'stock/', include([
        # Detail views
        path(r'<int:pk>/', include([
            re_path(r'print/?', StockItemLabelPrint.as_view(), name='api-stockitem-label-print'),
            re_path(r'metadata/', MetadataView.as_view(), {'model': StockItemLabel}, name='api-stockitem-label-metadata'),
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
            re_path(r'metadata/', MetadataView.as_view(), {'model': StockLocationLabel}, name='api-stocklocation-label-metadata'),
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
            re_path(r'^metadata/', MetadataView.as_view(), {'model': PartLabel}, name='api-part-label-metadata'),
            re_path(r'^.*$', PartLabelDetail.as_view(), name='api-part-label-detail'),
        ])),

        # List view
        re_path(r'^.*$', PartLabelList.as_view(), name='api-part-label-list'),
    ])),
]
