"""API functionality for the 'label' app"""

from django.conf import settings
from django.core.exceptions import FieldError, ValidationError
from django.http import HttpResponse, JsonResponse
from django.urls import include, re_path

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework.exceptions import NotFound

import common.models
import InvenTree.helpers
from InvenTree.mixins import ListAPI, RetrieveAPI, RetrieveUpdateDestroyAPI
from InvenTree.tasks import offload_task
from part.models import Part
from plugin.base.label import label as plugin_label
from plugin.registry import registry
from stock.models import StockItem, StockLocation

from .models import PartLabel, StockItemLabel, StockLocationLabel
from .serializers import (PartLabelSerializer, StockItemLabelSerializer,
                          StockLocationLabelSerializer)


class LabelListView(ListAPI):
    """Generic API class for label templates."""

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter
    ]

    filterset_fields = [
        'enabled',
    ]

    search_fields = [
        'name',
        'description',
    ]


class LabelPrintMixin:
    """Mixin for printing labels."""

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
            config = plugin.plugin_config()

            if config and config.active:
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
        debug_mode = common.models.InvenTreeSetting.get_setting('REPORT_DEBUG_MODE')

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

            inline = common.models.InvenTreeUserSetting.get_setting('LABEL_INLINE', user=request.user)

            return InvenTree.helpers.DownloadFile(
                pdf,
                label_name,
                content_type='application/pdf',
                inline=inline
            )


class StockItemLabelMixin:
    """Mixin for extracting stock items from query params."""

    def get_items(self):
        """Return a list of requested stock items."""
        items = []

        params = self.request.query_params

        for key in ['item', 'item[]', 'items', 'items[]']:
            if key in params:
                items = params.getlist(key, [])
                break

        valid_ids = []

        for item in items:
            try:
                valid_ids.append(int(item))
            except (ValueError):
                pass

        # List of StockItems which match provided values
        valid_items = StockItem.objects.filter(pk__in=valid_ids)

        return valid_items


class StockItemLabelList(LabelListView, StockItemLabelMixin):
    """API endpoint for viewing list of StockItemLabel objects.

    Filterable by:

    - enabled: Filter by enabled / disabled status
    - item: Filter by single stock item
    - items: Filter by list of stock items
    """

    queryset = StockItemLabel.objects.all()
    serializer_class = StockItemLabelSerializer

    def filter_queryset(self, queryset):
        """Filter the StockItem label queryset."""
        queryset = super().filter_queryset(queryset)

        # List of StockItem objects to match against
        items = self.get_items()

        # We wish to filter by stock items
        if len(items) > 0:
            """
            At this point, we are basically forced to be inefficient,
            as we need to compare the 'filters' string of each label,
            and see if it matches against each of the requested items.

            TODO: In the future, if this becomes excessively slow, it
                  will need to be readdressed.
            """

            # Keep track of which labels match every specified stockitem
            valid_label_ids = set()

            for label in queryset.all():

                matches = True

                # Filter string defined for the StockItemLabel object
                try:
                    filters = InvenTree.helpers.validateFilterString(label.filters)
                except ValidationError:  # pragma: no cover
                    continue

                for item in items:

                    item_query = StockItem.objects.filter(pk=item.pk)

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
                    continue  # pragma: no cover

            # Reduce queryset to only valid matches
            queryset = queryset.filter(pk__in=[pk for pk in valid_label_ids])

        return queryset


class StockItemLabelDetail(RetrieveUpdateDestroyAPI):
    """API endpoint for a single StockItemLabel object."""

    queryset = StockItemLabel.objects.all()
    serializer_class = StockItemLabelSerializer


class StockItemLabelPrint(RetrieveAPI, StockItemLabelMixin, LabelPrintMixin):
    """API endpoint for printing a StockItemLabel object."""

    queryset = StockItemLabel.objects.all()
    serializer_class = StockItemLabelSerializer

    def get(self, request, *args, **kwargs):
        """Check if valid stock item(s) have been provided."""
        items = self.get_items()

        return self.print(request, items)


class StockLocationLabelMixin:
    """Mixin for extracting stock locations from query params."""

    def get_locations(self):
        """Return a list of requested stock locations."""
        locations = []

        params = self.request.query_params

        for key in ['location', 'location[]', 'locations', 'locations[]']:

            if key in params:
                locations = params.getlist(key, [])

        valid_ids = []

        for loc in locations:
            try:
                valid_ids.append(int(loc))
            except (ValueError):
                pass

        # List of StockLocation objects which match provided values
        valid_locations = StockLocation.objects.filter(pk__in=valid_ids)

        return valid_locations


class StockLocationLabelList(LabelListView, StockLocationLabelMixin):
    """API endpoint for viewiing list of StockLocationLabel objects.

    Filterable by:

    - enabled: Filter by enabled / disabled status
    - location: Filter by a single stock location
    - locations: Filter by list of stock locations
    """

    queryset = StockLocationLabel.objects.all()
    serializer_class = StockLocationLabelSerializer

    def filter_queryset(self, queryset):
        """Filter the StockLocationLabel queryset."""
        queryset = super().filter_queryset(queryset)

        # List of StockLocation objects to match against
        locations = self.get_locations()

        # We wish to filter by stock location(s)
        if len(locations) > 0:
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

                # Filter string defined for the StockLocationLabel object
                try:
                    filters = InvenTree.helpers.validateFilterString(label.filters)
                except Exception:  # pragma: no cover
                    # Skip if there was an error validating the filters...
                    continue

                for loc in locations:

                    loc_query = StockLocation.objects.filter(pk=loc.pk)

                    try:
                        if not loc_query.filter(**filters).exists():
                            matches = False
                            break
                    except FieldError:
                        matches = False
                        break

                # Matched all items
                if matches:
                    valid_label_ids.add(label.pk)
                else:
                    continue  # pragma: no cover

            # Reduce queryset to only valid matches
            queryset = queryset.filter(pk__in=[pk for pk in valid_label_ids])

        return queryset


class StockLocationLabelDetail(RetrieveUpdateDestroyAPI):
    """API endpoint for a single StockLocationLabel object."""

    queryset = StockLocationLabel.objects.all()
    serializer_class = StockLocationLabelSerializer


class StockLocationLabelPrint(RetrieveAPI, StockLocationLabelMixin, LabelPrintMixin):
    """API endpoint for printing a StockLocationLabel object."""

    queryset = StockLocationLabel.objects.all()
    seiralizer_class = StockLocationLabelSerializer

    def get(self, request, *args, **kwargs):
        """Print labels based on the request parameters"""
        locations = self.get_locations()

        return self.print(request, locations)


class PartLabelMixin:
    """Mixin for extracting Part objects from query parameters."""

    def get_parts(self):
        """Return a list of requested Part objects."""
        parts = []

        params = self.request.query_params

        for key in ['part', 'part[]', 'parts', 'parts[]']:
            if key in params:
                parts = params.getlist(key, [])
                break

        valid_ids = []

        for part in parts:
            try:
                valid_ids.append(int(part))
            except (ValueError):
                pass

        # List of Part objects which match provided values
        return Part.objects.filter(pk__in=valid_ids)


class PartLabelList(LabelListView, PartLabelMixin):
    """API endpoint for viewing list of PartLabel objects."""

    queryset = PartLabel.objects.all()
    serializer_class = PartLabelSerializer

    def filter_queryset(self, queryset):
        """Custom queryset filtering for the PartLabel list"""
        queryset = super().filter_queryset(queryset)

        parts = self.get_parts()

        if len(parts) > 0:

            valid_label_ids = set()

            for label in queryset.all():

                matches = True

                try:
                    filters = InvenTree.helpers.validateFilterString(label.filters)
                except ValidationError:  # pragma: no cover
                    continue

                for part in parts:

                    part_query = Part.objects.filter(pk=part.pk)

                    try:
                        if not part_query.filter(**filters).exists():
                            matches = False
                            break
                    except FieldError:
                        matches = False
                        break

                if matches:
                    valid_label_ids.add(label.pk)

            # Reduce queryset to only valid matches
            queryset = queryset.filter(pk__in=[pk for pk in valid_label_ids])

        return queryset


class PartLabelDetail(RetrieveUpdateDestroyAPI):
    """API endpoint for a single PartLabel object."""

    queryset = PartLabel.objects.all()
    serializer_class = PartLabelSerializer


class PartLabelPrint(RetrieveAPI, PartLabelMixin, LabelPrintMixin):
    """API endpoint for printing a PartLabel object."""

    queryset = PartLabel.objects.all()
    serializer_class = PartLabelSerializer

    def get(self, request, *args, **kwargs):
        """Check if valid part(s) have been provided."""
        parts = self.get_parts()

        return self.print(request, parts)


label_api_urls = [

    # Stock item labels
    re_path(r'stock/', include([
        # Detail views
        re_path(r'^(?P<pk>\d+)/', include([
            re_path(r'print/?', StockItemLabelPrint.as_view(), name='api-stockitem-label-print'),
            re_path(r'^.*$', StockItemLabelDetail.as_view(), name='api-stockitem-label-detail'),
        ])),

        # List view
        re_path(r'^.*$', StockItemLabelList.as_view(), name='api-stockitem-label-list'),
    ])),

    # Stock location labels
    re_path(r'location/', include([
        # Detail views
        re_path(r'^(?P<pk>\d+)/', include([
            re_path(r'print/?', StockLocationLabelPrint.as_view(), name='api-stocklocation-label-print'),
            re_path(r'^.*$', StockLocationLabelDetail.as_view(), name='api-stocklocation-label-detail'),
        ])),

        # List view
        re_path(r'^.*$', StockLocationLabelList.as_view(), name='api-stocklocation-label-list'),
    ])),

    # Part labels
    re_path(r'^part/', include([
        # Detail views
        re_path(r'^(?P<pk>\d+)/', include([
            re_path(r'^print/', PartLabelPrint.as_view(), name='api-part-label-print'),
            re_path(r'^.*$', PartLabelDetail.as_view(), name='api-part-label-detail'),
        ])),

        # List view
        re_path(r'^.*$', PartLabelList.as_view(), name='api-part-label-list'),
    ])),
]
