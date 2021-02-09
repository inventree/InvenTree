# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.translation import ugettext as _
from django.conf.urls import url, include
from django.http import HttpResponse

from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import generics, filters
from rest_framework.response import Response

import common.models
import InvenTree.helpers

from stock.models import StockItem

from .models import TestReport
from .serializers import TestReportSerializer


class ReportListView(generics.ListAPIView):
    """
    Generic API class for report templates
    """

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
    ]

    filter_fields = [
        'enabled',
    ]

    search_fields = [
        'name',
        'description',
    ]


class StockItemReportMixin:
    """
    Mixin for extracting stock items from query params
    """

    def get_items(self):
        """
        Return a list of requested stock items
        """
        
        items = []

        params = self.request.query_params

        if 'items[]' in params:
            items = params.getlist('items[]', [])
        elif 'item' in params:
            items = [params.get('item', None)]

        if type(items) not in [list, tuple]:
            item = [items]

        valid_ids = []

        for item in items:
            try:
                valid_ids.append(int(item))
            except (ValueError):
                pass

        # List of StockItems which match provided values
        valid_items = StockItem.objects.filter(pk__in=valid_ids)

        return valid_items


class StockItemTestReportList(ReportListView, StockItemReportMixin):
    """
    API endpoint for viewing list of TestReport objects.

    Filterable by:

    - enabled: Filter by enabled / disabled status
    - item: Filter by single stock item
    - items: Filter by list of stock items

    """

    queryset = TestReport.objects.all()
    serializer_class = TestReportSerializer

    def filter_queryset(self, queryset):
        
        queryset = super().filter_queryset(queryset)

        # List of StockItem objects to match against
        items = self.get_items()

        if len(items) > 0:
            """
            We wish to filter by stock items.

            We need to compare the 'filters' string of each report,
            and see if it matches against each of the specified stock items.

            TODO: In the future, perhaps there is a way to make this more efficient.
            """

            valid_report_ids = set()

            for report in queryset.all():

                matches = True

                # Filter string defined for the report object
                filters = InvenTree.helpers.validateFilterString(report.filters)

                for item in items:
                    item_query = StockItem.objects.filter(pk=item.pk)

                    if not item_query.filter(**filters).exists():
                        matches = False
                        break

                if matches:
                    valid_report_ids.add(report.pk)
                else:
                    continue

            # Reduce queryset to only valid matches
            queryset = queryset.filter(pk__in=[pk for pk in valid_report_ids])
        return queryset


class StockItemTestReportDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint for a single TestReport object
    """

    queryset = TestReport.objects.all()
    serializer_class = TestReportSerializer


class StockItemTestReportPrint(generics.RetrieveAPIView, StockItemReportMixin):
    """
    API endpoint for printing a TestReport object
    """

    queryset = TestReport.objects.all()
    serializer_class = TestReportSerializer

    def get(self, request, *args, **kwargs):
        """
        Check if valid stock item(s) have been provided.
        """

        items = self.get_items()

        if len(items) == 0:
            # No valid items provided, return an error message
            data = {
                'error': _('Must provide valid StockItem(s)')
            }

            return Response(data, status=400)

        outputs = []

        # In debug mode, generate single HTML output, rather than PDF
        debug_mode = common.models.InvenTreeSetting.get_setting('REPORT_DEBUG_MODE')

        # Merge one or more PDF files into a single download
        for item in items:
            report = self.get_object()
            report.stock_item = item

            if debug_mode:
                outputs.append(report.render_to_string(request))
            else:
                outputs.append(report.render(request))

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
                'test_report.pdf',
                content_type='application/pdf'
            )


report_api_urls = [

    # Stock item test reports
    url(r'test/', include([
        # Detail views
        url(r'^(?P<pk>\d+)/', include([
            url(r'print/?', StockItemTestReportPrint.as_view(), name='api-stockitem-testreport-print'),
            url(r'^.*$', StockItemTestReportDetail.as_view(), name='api-stockitem-testreport-detail'),
        ])),

        # List view
        url(r'^.*$', StockItemTestReportList.as_view(), name='api-stockitem-testreport-list'),
    ])),
]
