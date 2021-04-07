# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _
from django.conf.urls import url, include
from django.core.exceptions import ValidationError, FieldError
from django.http import HttpResponse

from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import generics, filters
from rest_framework.response import Response

import InvenTree.helpers
import common.models

from stock.models import StockItem, StockLocation

from .models import StockItemLabel, StockLocationLabel
from .serializers import StockItemLabelSerializer, StockLocationLabelSerializer


class LabelListView(generics.ListAPIView):
    """
    Generic API class for label templates
    """

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter
    ]

    filter_fields = [
        'enabled',
    ]

    search_fields = [
        'name',
        'description',
    ]


class LabelPrintMixin:
    """
    Mixin for printing labels
    """

    def print(self, request, items_to_print):
        """
        Print this label template against a number of pre-validated items
        """

        if len(items_to_print) == 0:
            # No valid items provided, return an error message
            data = {
                'error': _('No valid objects provided to template'),
            }

            return Response(data, status=400)

        outputs = []

        # In debug mode, generate single HTML output, rather than PDF
        debug_mode = common.models.InvenTreeSetting.get_setting('REPORT_DEBUG_MODE')

        # Merge one or more PDF files into a single download
        for item in items_to_print:
            label = self.get_object()
            label.object_to_print = item

            if debug_mode:
                outputs.append(label.render_as_string(request))
            else:
                outputs.append(label.render(request))

        if debug_mode:
            """
            Contatenate all rendered templates into a single HTML string,
            and return the string as a HTML response.
            """

            html = "\n".join(outputs)

            return HttpResponse(html)
        else:
            """
            Concatenate all rendered pages into a single PDF object,
            and return the resulting document!
            """

            pages = []

            if len(outputs) > 1:
                # If more than one output is generated, merge them into a single file
                for output in outputs:
                    doc = output.get_document()
                    for page in doc.pages:
                        pages.append(page)

                pdf = outputs[0].get_document().copy(pages).write_pdf()
            else:
                pdf = outputs[0].get_document().write_pdf()

            return InvenTree.helpers.DownloadFile(
                pdf,
                'inventree_label.pdf',
                content_type='application/pdf'
            )


class StockItemLabelMixin:
    """
    Mixin for extracting stock items from query params
    """

    def get_items(self):
        """
        Return a list of requested stock items
        """

        items = []

        params = self.request.query_params

        for key in ['item', 'item[]', 'items', 'items[]']:
            if key in params:
                items = params.getlist(key, [])

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
    """
    API endpoint for viewing list of StockItemLabel objects.

    Filterable by:

    - enabled: Filter by enabled / disabled status
    - item: Filter by single stock item
    - items: Filter by list of stock items

    """

    queryset = StockItemLabel.objects.all()
    serializer_class = StockItemLabelSerializer

    def filter_queryset(self, queryset):
        """
        Filter the StockItem label queryset.
        """
        
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
                except ValidationError:
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
                    continue

            # Reduce queryset to only valid matches
            queryset = queryset.filter(pk__in=[pk for pk in valid_label_ids])

        return queryset


class StockItemLabelDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint for a single StockItemLabel object
    """

    queryset = StockItemLabel.objects.all()
    serializer_class = StockItemLabelSerializer


class StockItemLabelPrint(generics.RetrieveAPIView, StockItemLabelMixin, LabelPrintMixin):
    """
    API endpoint for printing a StockItemLabel object
    """

    queryset = StockItemLabel.objects.all()
    serializer_class = StockItemLabelSerializer

    def get(self, request, *args, **kwargs):
        """
        Check if valid stock item(s) have been provided.
        """

        items = self.get_items()

        return self.print(request, items)


class StockLocationLabelMixin:
    """
    Mixin for extracting stock locations from query params
    """

    def get_locations(self):
        """
        Return a list of requested stock locations
        """

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
    """
    API endpoint for viewiing list of StockLocationLabel objects.

    Filterable by:

    - enabled: Filter by enabled / disabled status
    - location: Filter by a single stock location
    - locations: Filter by list of stock locations
    """

    queryset = StockLocationLabel.objects.all()
    serializer_class = StockLocationLabelSerializer

    def filter_queryset(self, queryset):
        """
        Filter the StockLocationLabel queryset
        """

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
                except:
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
                    continue

            # Reduce queryset to only valid matches
            queryset = queryset.filter(pk__in=[pk for pk in valid_label_ids])

        return queryset


class StockLocationLabelDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint for a single StockLocationLabel object
    """

    queryset = StockLocationLabel.objects.all()
    serializer_class = StockLocationLabelSerializer


class StockLocationLabelPrint(generics.RetrieveAPIView, StockLocationLabelMixin, LabelPrintMixin):
    """
    API endpoint for printing a StockLocationLabel object
    """

    queryset = StockLocationLabel.objects.all()
    seiralizer_class = StockLocationLabelSerializer

    def get(self, request, *args, **kwargs):

        locations = self.get_locations()

        return self.print(request, locations)


label_api_urls = [

    # Stock item labels
    url(r'stock/', include([
        # Detail views
        url(r'^(?P<pk>\d+)/', include([
            url(r'print/?', StockItemLabelPrint.as_view(), name='api-stockitem-label-print'),
            url(r'^.*$', StockItemLabelDetail.as_view(), name='api-stockitem-label-detail'),
        ])),

        # List view
        url(r'^.*$', StockItemLabelList.as_view(), name='api-stockitem-label-list'),
    ])),

    # Stock location labels
    url(r'location/', include([
        # Detail views
        url(r'^(?P<pk>\d+)/', include([
            url(r'print/?', StockLocationLabelPrint.as_view(), name='api-stocklocation-label-print'),
            url(r'^.*$', StockLocationLabelDetail.as_view(), name='api-stocklocation-label-detail'),
        ])),

        # List view
        url(r'^.*$', StockLocationLabelList.as_view(), name='api-stocklocation-label-list'),
    ])),
]
