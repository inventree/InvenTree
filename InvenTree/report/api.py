"""API functionality for the 'report' app"""

from django.core.exceptions import FieldError, ValidationError
from django.http import HttpResponse
from django.template.exceptions import TemplateDoesNotExist
from django.urls import include, path, re_path
from django.utils.translation import gettext_lazy as _

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics
from rest_framework.response import Response

import build.models
import common.models
import InvenTree.helpers
import order.models
import part.models
from stock.models import StockItem

from .models import (BillOfMaterialsReport, BuildReport, PurchaseOrderReport,
                     SalesOrderReport, TestReport)
from .serializers import (BOMReportSerializer, BuildReportSerializer,
                          PurchaseOrderReportSerializer,
                          SalesOrderReportSerializer, TestReportSerializer)


class ReportListView(generics.ListAPIView):
    """Generic API class for report templates."""

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


class BuildReportMixin:
    """Mixin for extracting Build items from query params."""

    def get_builds(self):
        """Return a list of requested Build objects."""
        builds = []

        params = self.request.query_params

        for key in ['build', 'build[]', 'builds', 'builds[]']:

            if key in params:
                builds = params.getlist(key, [])

                break

        valid_ids = []

        for b in builds:
            try:
                valid_ids.append(int(b))
            except (ValueError):
                continue

        return build.models.Build.objects.filter(pk__in=valid_ids)


class OrderReportMixin:
    """Mixin for extracting order items from query params.

    requires the OrderModel class attribute to be set!
    """

    def get_orders(self):
        """Return a list of order objects."""
        orders = []

        params = self.request.query_params

        for key in ['order', 'order[]', 'orders', 'orders[]']:
            if key in params:
                orders = params.getlist(key, [])
                break

        valid_ids = []

        for o in orders:
            try:
                valid_ids.append(int(o))
            except (ValueError):
                pass

        valid_orders = self.OrderModel.objects.filter(pk__in=valid_ids)

        return valid_orders


class PartReportMixin:
    """Mixin for extracting part items from query params."""

    def get_parts(self):
        """Return a list of requested part objects."""
        parts = []

        params = self.request.query_params

        for key in ['part', 'part[]', 'parts', 'parts[]']:

            if key in params:
                parts = params.getlist(key, [])

        valid_ids = []

        for p in parts:
            try:
                valid_ids.append(int(p))
            except (ValueError):
                continue

        # Extract a valid set of Part objects
        valid_parts = part.models.Part.objects.filter(pk__in=valid_ids)

        return valid_parts


class ReportPrintMixin:
    """Mixin for printing reports."""

    def print(self, request, items_to_print):
        """Print this report template against a number of pre-validated items."""
        if len(items_to_print) == 0:
            # No valid items provided, return an error message
            data = {
                'error': _('No valid objects provided to template'),
            }

            return Response(data, status=400)

        outputs = []

        # In debug mode, generate single HTML output, rather than PDF
        debug_mode = common.models.InvenTreeSetting.get_setting('REPORT_DEBUG_MODE')

        # Start with a default report name
        report_name = "report.pdf"

        # Merge one or more PDF files into a single download
        for item in items_to_print:
            report = self.get_object()
            report.object_to_print = item

            report_name = report.generate_filename(request)

            try:
                if debug_mode:
                    outputs.append(report.render_as_string(request))
                else:
                    outputs.append(report.render(request))
            except TemplateDoesNotExist as e:
                template = str(e)
                if not template:
                    template = report.template

                return Response(
                    {
                        'error': _(f"Template file '{template}' is missing or does not exist"),
                    },
                    status=400,
                )

        if not report_name.endswith('.pdf'):
            report_name += '.pdf'

        if debug_mode:
            """Contatenate all rendered templates into a single HTML string, and return the string as a HTML response."""

            html = "\n".join(outputs)

            return HttpResponse(html)
        else:
            """Concatenate all rendered pages into a single PDF object, and return the resulting document!"""

            pages = []

            try:

                if len(outputs) > 1:
                    # If more than one output is generated, merge them into a single file
                    for output in outputs:
                        doc = output.get_document()
                        for page in doc.pages:
                            pages.append(page)

                    pdf = outputs[0].get_document().copy(pages).write_pdf()
                else:
                    pdf = outputs[0].get_document().write_pdf()

            except TemplateDoesNotExist as e:

                template = str(e)

                if not template:
                    template = report.template

                return Response(
                    {
                        'error': _(f"Template file '{template}' is missing or does not exist"),
                    },
                    status=400,
                )

            inline = common.models.InvenTreeUserSetting.get_setting('REPORT_INLINE', user=request.user)

            return InvenTree.helpers.DownloadFile(
                pdf,
                report_name,
                content_type='application/pdf',
                inline=inline,
            )


class StockItemTestReportList(ReportListView, StockItemReportMixin):
    """API endpoint for viewing list of TestReport objects.

    Filterable by:

    - enabled: Filter by enabled / disabled status
    - item: Filter by stock item(s)
    """

    queryset = TestReport.objects.all()
    serializer_class = TestReportSerializer

    def filter_queryset(self, queryset):
        """Custom queryset filtering"""
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
                try:
                    filters = InvenTree.helpers.validateFilterString(report.filters)
                except:
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

                if matches:
                    valid_report_ids.add(report.pk)
                else:
                    continue

            # Reduce queryset to only valid matches
            queryset = queryset.filter(pk__in=[pk for pk in valid_report_ids])
        return queryset


class StockItemTestReportDetail(generics.RetrieveUpdateDestroyAPIView):
    """API endpoint for a single TestReport object."""

    queryset = TestReport.objects.all()
    serializer_class = TestReportSerializer


class StockItemTestReportPrint(generics.RetrieveAPIView, StockItemReportMixin, ReportPrintMixin):
    """API endpoint for printing a TestReport object."""

    queryset = TestReport.objects.all()
    serializer_class = TestReportSerializer

    def get(self, request, *args, **kwargs):
        """Check if valid stock item(s) have been provided."""
        items = self.get_items()

        return self.print(request, items)


class BOMReportList(ReportListView, PartReportMixin):
    """API endpoint for viewing a list of BillOfMaterialReport objects.

    Filterably by:

    - enabled: Filter by enabled / disabled status
    - part: Filter by part(s)
    """

    queryset = BillOfMaterialsReport.objects.all()
    serializer_class = BOMReportSerializer

    def filter_queryset(self, queryset):
        """Custom queryset filtering"""
        queryset = super().filter_queryset(queryset)

        # List of Part objects to match against
        parts = self.get_parts()

        if len(parts) > 0:
            """
            We wish to filter by part(s).

            We need to compare the 'filters' string of each report,
            and see if it matches against each of the specified parts.
            """

            valid_report_ids = set()

            for report in queryset.all():

                matches = True

                try:
                    filters = InvenTree.helpers.validateFilterString(report.filters)
                except ValidationError:
                    # Filters are ill-defined
                    continue

                for p in parts:
                    part_query = part.models.Part.objects.filter(pk=p.pk)

                    try:
                        if not part_query.filter(**filters).exists():
                            matches = False
                            break
                    except FieldError:
                        matches = False
                        break

                if matches:
                    valid_report_ids.add(report.pk)
                else:
                    continue

            # Reduce queryset to only valid matches
            queryset = queryset.filter(pk__in=[pk for pk in valid_report_ids])

        return queryset


class BOMReportDetail(generics.RetrieveUpdateDestroyAPIView):
    """API endpoint for a single BillOfMaterialReport object."""

    queryset = BillOfMaterialsReport.objects.all()
    serializer_class = BOMReportSerializer


class BOMReportPrint(generics.RetrieveAPIView, PartReportMixin, ReportPrintMixin):
    """API endpoint for printing a BillOfMaterialReport object."""

    queryset = BillOfMaterialsReport.objects.all()
    serializer_class = BOMReportSerializer

    def get(self, request, *args, **kwargs):
        """Check if valid part item(s) have been provided."""
        parts = self.get_parts()

        return self.print(request, parts)


class BuildReportList(ReportListView, BuildReportMixin):
    """API endpoint for viewing a list of BuildReport objects.

    Can be filtered by:

    - enabled: Filter by enabled / disabled status
    - build: Filter by Build object
    """

    queryset = BuildReport.objects.all()
    serializer_class = BuildReportSerializer

    def filter_queryset(self, queryset):
        """Custom queryset filtering"""
        queryset = super().filter_queryset(queryset)

        # List of Build objects to match against
        builds = self.get_builds()

        if len(builds) > 0:
            """
            We wish to filter by Build(s)

            We need to compare the 'filters' string of each report,
            and see if it matches against each of the specified parts

            # TODO: This code needs some refactoring!
            """

            valid_build_ids = set()

            for report in queryset.all():

                matches = True

                try:
                    filters = InvenTree.helpers.validateFilterString(report.filters)
                except ValidationError:
                    continue

                for b in builds:
                    build_query = build.models.Build.objects.filter(pk=b.pk)

                    try:
                        if not build_query.filter(**filters).exists():
                            matches = False
                            break
                    except FieldError:
                        matches = False
                        break

                if matches:
                    valid_build_ids.add(report.pk)
                else:
                    continue

            # Reduce queryset to only valid matches
            queryset = queryset.filter(pk__in=[pk for pk in valid_build_ids])

        return queryset


class BuildReportDetail(generics.RetrieveUpdateDestroyAPIView):
    """API endpoint for a single BuildReport object."""

    queryset = BuildReport.objects.all()
    serializer_class = BuildReportSerializer


class BuildReportPrint(generics.RetrieveAPIView, BuildReportMixin, ReportPrintMixin):
    """API endpoint for printing a BuildReport."""

    queryset = BuildReport.objects.all()
    serializer_class = BuildReportSerializer

    def get(self, request, *ars, **kwargs):
        """Perform a GET action to print the report"""
        builds = self.get_builds()

        return self.print(request, builds)


class PurchaseOrderReportList(ReportListView, OrderReportMixin):
    """API list endpoint for the PurchaseOrderReport model"""
    OrderModel = order.models.PurchaseOrder

    queryset = PurchaseOrderReport.objects.all()
    serializer_class = PurchaseOrderReportSerializer

    def filter_queryset(self, queryset):
        """Custom queryset filter for the PurchaseOrderReport list"""
        queryset = super().filter_queryset(queryset)

        orders = self.get_orders()

        if len(orders) > 0:
            """
            We wish to filter by purchase orders.

            We need to compare the 'filters' string of each report,
            and see if it matches against each of the specified orders.

            TODO: In the future, perhaps there is a way to make this more efficient.
            """

            valid_report_ids = set()

            for report in queryset.all():

                matches = True

                # Filter string defined for the report object
                try:
                    filters = InvenTree.helpers.validateFilterString(report.filters)
                except:
                    continue

                for o in orders:
                    order_query = order.models.PurchaseOrder.objects.filter(pk=o.pk)

                    try:
                        if not order_query.filter(**filters).exists():
                            matches = False
                            break
                    except FieldError:
                        matches = False
                        break

                if matches:
                    valid_report_ids.add(report.pk)
                else:
                    continue

            # Reduce queryset to only valid matches
            queryset = queryset.filter(pk__in=[pk for pk in valid_report_ids])

        return queryset


class PurchaseOrderReportDetail(generics.RetrieveUpdateDestroyAPIView):
    """API endpoint for a single PurchaseOrderReport object."""

    queryset = PurchaseOrderReport.objects.all()
    serializer_class = PurchaseOrderReportSerializer


class PurchaseOrderReportPrint(generics.RetrieveAPIView, OrderReportMixin, ReportPrintMixin):
    """API endpoint for printing a PurchaseOrderReport object."""

    OrderModel = order.models.PurchaseOrder

    queryset = PurchaseOrderReport.objects.all()
    serializer_class = PurchaseOrderReportSerializer

    def get(self, request, *args, **kwargs):
        """Perform GET request to print the report"""
        orders = self.get_orders()

        return self.print(request, orders)


class SalesOrderReportList(ReportListView, OrderReportMixin):
    """API list endpoint for the SalesOrderReport model"""
    OrderModel = order.models.SalesOrder

    queryset = SalesOrderReport.objects.all()
    serializer_class = SalesOrderReportSerializer

    def filter_queryset(self, queryset):
        """Custom queryset filtering for the SalesOrderReport API list"""
        queryset = super().filter_queryset(queryset)

        orders = self.get_orders()

        if len(orders) > 0:
            """
            We wish to filter by purchase orders.

            We need to compare the 'filters' string of each report,
            and see if it matches against each of the specified orders.

            TODO: In the future, perhaps there is a way to make this more efficient.
            """

            valid_report_ids = set()

            for report in queryset.all():

                matches = True

                # Filter string defined for the report object
                try:
                    filters = InvenTree.helpers.validateFilterString(report.filters)
                except:
                    continue

                for o in orders:
                    order_query = order.models.SalesOrder.objects.filter(pk=o.pk)

                    try:
                        if not order_query.filter(**filters).exists():
                            matches = False
                            break
                    except FieldError:
                        matches = False
                        break

                if matches:
                    valid_report_ids.add(report.pk)
                else:
                    continue

            # Reduce queryset to only valid matches
            queryset = queryset.filter(pk__in=[pk for pk in valid_report_ids])

        return queryset


class SalesOrderReportDetail(generics.RetrieveUpdateDestroyAPIView):
    """API endpoint for a single SalesOrderReport object."""

    queryset = SalesOrderReport.objects.all()
    serializer_class = SalesOrderReportSerializer


class SalesOrderReportPrint(generics.RetrieveAPIView, OrderReportMixin, ReportPrintMixin):
    """API endpoint for printing a PurchaseOrderReport object."""

    OrderModel = order.models.SalesOrder

    queryset = SalesOrderReport.objects.all()
    serializer_class = SalesOrderReportSerializer

    def get(self, request, *args, **kwargs):
        """Perform a GET request to print the report"""
        orders = self.get_orders()

        return self.print(request, orders)


report_api_urls = [

    # Purchase order reports
    re_path(r'po/', include([
        # Detail views
        re_path(r'^(?P<pk>\d+)/', include([
            re_path(r'print/', PurchaseOrderReportPrint.as_view(), name='api-po-report-print'),
            path('', PurchaseOrderReportDetail.as_view(), name='api-po-report-detail'),
        ])),

        # List view
        path('', PurchaseOrderReportList.as_view(), name='api-po-report-list'),
    ])),

    # Sales order reports
    re_path(r'so/', include([
        # Detail views
        re_path(r'^(?P<pk>\d+)/', include([
            re_path(r'print/', SalesOrderReportPrint.as_view(), name='api-so-report-print'),
            path('', SalesOrderReportDetail.as_view(), name='api-so-report-detail'),
        ])),

        path('', SalesOrderReportList.as_view(), name='api-so-report-list'),
    ])),

    # Build reports
    re_path(r'build/', include([
        # Detail views
        re_path(r'^(?P<pk>\d+)/', include([
            re_path(r'print/?', BuildReportPrint.as_view(), name='api-build-report-print'),
            re_path(r'^.$', BuildReportDetail.as_view(), name='api-build-report-detail'),
        ])),

        # List view
        re_path(r'^.*$', BuildReportList.as_view(), name='api-build-report-list'),
    ])),

    # Bill of Material reports
    re_path(r'bom/', include([

        # Detail views
        re_path(r'^(?P<pk>\d+)/', include([
            re_path(r'print/?', BOMReportPrint.as_view(), name='api-bom-report-print'),
            re_path(r'^.*$', BOMReportDetail.as_view(), name='api-bom-report-detail'),
        ])),

        # List view
        re_path(r'^.*$', BOMReportList.as_view(), name='api-bom-report-list'),
    ])),

    # Stock item test reports
    re_path(r'test/', include([
        # Detail views
        re_path(r'^(?P<pk>\d+)/', include([
            re_path(r'print/?', StockItemTestReportPrint.as_view(), name='api-stockitem-testreport-print'),
            re_path(r'^.*$', StockItemTestReportDetail.as_view(), name='api-stockitem-testreport-detail'),
        ])),

        # List view
        re_path(r'^.*$', StockItemTestReportList.as_view(), name='api-stockitem-testreport-list'),
    ])),
]
