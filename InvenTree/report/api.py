"""API functionality for the 'report' app."""

from django.core.exceptions import FieldError, ValidationError
from django.core.files.base import ContentFile
from django.http import HttpResponse
from django.template.exceptions import TemplateDoesNotExist
from django.urls import include, path, re_path
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import cache_page, never_cache

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response

import build.models
import common.models
import InvenTree.helpers
import order.models
import part.models
from InvenTree.api import MetadataView
from InvenTree.exceptions import log_error
from InvenTree.filters import InvenTreeSearchFilter
from InvenTree.mixins import ListCreateAPI, RetrieveAPI, RetrieveUpdateDestroyAPI
from stock.models import StockItem, StockItemAttachment, StockLocation

from .models import (
    BillOfMaterialsReport,
    BuildReport,
    PurchaseOrderReport,
    ReturnOrderReport,
    SalesOrderReport,
    StockLocationReport,
    TestReport,
)
from .serializers import (
    BOMReportSerializer,
    BuildReportSerializer,
    PurchaseOrderReportSerializer,
    ReturnOrderReportSerializer,
    SalesOrderReportSerializer,
    StockLocationReportSerializer,
    TestReportSerializer,
)


class ReportListView(ListCreateAPI):
    """Generic API class for report templates."""

    filter_backends = [DjangoFilterBackend, InvenTreeSearchFilter]

    filterset_fields = ['enabled']

    search_fields = ['name', 'description']


class ReportFilterMixin:
    """Mixin for extracting multiple objects from query params.

    Each subclass *must* have an attribute called 'ITEM_KEY',
    which is used to determine what 'key' is used in the query parameters.

    This mixin defines a 'get_items' method which provides a generic implementation
    to return a list of matching database model instances
    """

    # Database model for instances to actually be "printed" against this report template
    ITEM_MODEL = None

    # Default key for looking up database model instances
    ITEM_KEY = 'item'

    def get_items(self):
        """Return a list of database objects from query parameters."""
        if not self.ITEM_MODEL:
            raise NotImplementedError(
                f'ITEM_MODEL attribute not defined for {__class__}'
            )

        ids = []

        # Construct a list of possible query parameter value options
        # e.g. if self.ITEM_KEY = 'order' -> ['order', 'order[]', 'orders', 'orders[]']
        for k in [self.ITEM_KEY + x for x in ['', '[]', 's', 's[]']]:
            if ids := self.request.query_params.getlist(k, []):
                # Return the first list of matches
                break

        # Next we must validated each provided object ID
        valid_ids = []

        for id in ids:
            try:
                valid_ids.append(int(id))
            except ValueError:
                pass

        # Filter queryset by matching ID values
        return self.ITEM_MODEL.objects.filter(pk__in=valid_ids)

    def filter_queryset(self, queryset):
        """Filter the queryset based on the provided report ID values.

        As each 'report' instance may optionally define its own filters,
        the resulting queryset is the 'union' of the two
        """
        queryset = super().filter_queryset(queryset)

        items = self.get_items()

        if len(items) > 0:
            """At this point, we are basically forced to be inefficient:

            We need to compare the 'filters' string of each report template,
            and see if it matches against each of the requested items.

            In practice, this is not too bad.
            """

            valid_report_ids = set()

            for report in queryset.all():
                matches = True

                try:
                    filters = InvenTree.helpers.validateFilterString(report.filters)
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
                    valid_report_ids.add(report.pk)

            # Reduce queryset to only valid matches
            queryset = queryset.filter(pk__in=list(valid_report_ids))

        return queryset


@method_decorator(cache_page(5), name='dispatch')
class ReportPrintMixin:
    """Mixin for printing reports."""

    @method_decorator(never_cache)
    def dispatch(self, *args, **kwargs):
        """Prevent caching when printing report templates."""
        return super().dispatch(*args, **kwargs)

    def report_callback(self, object, report, request):
        """Callback function for each object/report combination.

        Allows functionality to be performed before returning the consolidated PDF

        Arguments:
            object: The model instance to be printed
            report: The individual PDF file object
            request: The request instance associated with this print call
        """
        ...

    def print(self, request, items_to_print):
        """Print this report template against a number of pre-validated items."""
        if len(items_to_print) == 0:
            # No valid items provided, return an error message
            data = {'error': _('No valid objects provided to template')}

            return Response(data, status=400)

        outputs = []

        # In debug mode, generate single HTML output, rather than PDF
        debug_mode = common.models.InvenTreeSetting.get_setting(
            'REPORT_DEBUG_MODE', cache=False
        )

        # Start with a default report name
        report_name = 'report.pdf'

        try:
            # Merge one or more PDF files into a single download
            for item in items_to_print:
                report = self.get_object()
                report.object_to_print = item

                report_name = report.generate_filename(request)
                output = report.render(request)

                # Run report callback for each generated report
                self.report_callback(item, output, request)

                try:
                    if debug_mode:
                        outputs.append(report.render_as_string(request))
                    else:
                        outputs.append(output)
                except TemplateDoesNotExist as e:
                    template = str(e)
                    if not template:
                        template = report.template

                    return Response(
                        {
                            'error': _(
                                f"Template file '{template}' is missing or does not exist"
                            )
                        },
                        status=400,
                    )

            if not report_name.endswith('.pdf'):
                report_name += '.pdf'

            if debug_mode:
                """Concatenate all rendered templates into a single HTML string, and return the string as a HTML response."""

                html = '\n'.join(outputs)

                return HttpResponse(html)
            else:
                """Concatenate all rendered pages into a single PDF object, and return the resulting document!"""

                pages = []

                try:
                    for output in outputs:
                        doc = output.get_document()
                        for page in doc.pages:
                            pages.append(page)

                    pdf = outputs[0].get_document().copy(pages).write_pdf()

                except TemplateDoesNotExist as e:
                    template = str(e)

                    if not template:
                        template = report.template

                    return Response(
                        {
                            'error': _(
                                f"Template file '{template}' is missing or does not exist"
                            )
                        },
                        status=400,
                    )

                inline = common.models.InvenTreeUserSetting.get_setting(
                    'REPORT_INLINE', user=request.user, cache=False
                )

                return InvenTree.helpers.DownloadFile(
                    pdf, report_name, content_type='application/pdf', inline=inline
                )

        except Exception as exc:
            # Log the exception to the database
            log_error(request.path)

            # Re-throw the exception to the client as a DRF exception
            raise ValidationError({
                'error': 'Report printing failed',
                'detail': str(exc),
                'path': request.path,
            })

    def get(self, request, *args, **kwargs):
        """Default implementation of GET for a print endpoint.

        Note that it expects the class has defined a get_items() method
        """
        items = self.get_items()
        return self.print(request, items)


class StockItemTestReportMixin(ReportFilterMixin):
    """Mixin for StockItemTestReport report template."""

    ITEM_MODEL = StockItem
    ITEM_KEY = 'item'
    queryset = TestReport.objects.all()
    serializer_class = TestReportSerializer


class StockItemTestReportList(StockItemTestReportMixin, ReportListView):
    """API endpoint for viewing list of TestReport objects.

    Filterable by:

    - enabled: Filter by enabled / disabled status
    - item: Filter by stock item(s)
    """

    pass


class StockItemTestReportDetail(StockItemTestReportMixin, RetrieveUpdateDestroyAPI):
    """API endpoint for a single TestReport object."""

    pass


class StockItemTestReportPrint(StockItemTestReportMixin, ReportPrintMixin, RetrieveAPI):
    """API endpoint for printing a TestReport object."""

    def report_callback(self, item, report, request):
        """Callback to (optionally) save a copy of the generated report."""
        if common.models.InvenTreeSetting.get_setting(
            'REPORT_ATTACH_TEST_REPORT', cache=False
        ):
            # Construct a PDF file object
            try:
                pdf = report.get_document().write_pdf()
                pdf_content = ContentFile(pdf, 'test_report.pdf')
            except TemplateDoesNotExist:
                return

            StockItemAttachment.objects.create(
                attachment=pdf_content,
                stock_item=item,
                user=request.user,
                comment=_('Test report'),
            )


class BOMReportMixin(ReportFilterMixin):
    """Mixin for BillOfMaterialsReport report template."""

    ITEM_MODEL = part.models.Part
    ITEM_KEY = 'part'

    queryset = BillOfMaterialsReport.objects.all()
    serializer_class = BOMReportSerializer


class BOMReportList(BOMReportMixin, ReportListView):
    """API endpoint for viewing a list of BillOfMaterialReport objects.

    Filterably by:

    - enabled: Filter by enabled / disabled status
    - part: Filter by part(s)
    """

    pass


class BOMReportDetail(BOMReportMixin, RetrieveUpdateDestroyAPI):
    """API endpoint for a single BillOfMaterialReport object."""

    pass


class BOMReportPrint(BOMReportMixin, ReportPrintMixin, RetrieveAPI):
    """API endpoint for printing a BillOfMaterialReport object."""

    pass


class BuildReportMixin(ReportFilterMixin):
    """Mixin for the BuildReport report template."""

    ITEM_MODEL = build.models.Build
    ITEM_KEY = 'build'

    queryset = BuildReport.objects.all()
    serializer_class = BuildReportSerializer


class BuildReportList(BuildReportMixin, ReportListView):
    """API endpoint for viewing a list of BuildReport objects.

    Can be filtered by:

    - enabled: Filter by enabled / disabled status
    - build: Filter by Build object
    """

    pass


class BuildReportDetail(BuildReportMixin, RetrieveUpdateDestroyAPI):
    """API endpoint for a single BuildReport object."""

    pass


class BuildReportPrint(BuildReportMixin, ReportPrintMixin, RetrieveAPI):
    """API endpoint for printing a BuildReport."""

    pass


class PurchaseOrderReportMixin(ReportFilterMixin):
    """Mixin for the PurchaseOrderReport report template."""

    ITEM_MODEL = order.models.PurchaseOrder
    ITEM_KEY = 'order'

    queryset = PurchaseOrderReport.objects.all()
    serializer_class = PurchaseOrderReportSerializer


class PurchaseOrderReportList(PurchaseOrderReportMixin, ReportListView):
    """API list endpoint for the PurchaseOrderReport model."""

    pass


class PurchaseOrderReportDetail(PurchaseOrderReportMixin, RetrieveUpdateDestroyAPI):
    """API endpoint for a single PurchaseOrderReport object."""

    pass


class PurchaseOrderReportPrint(PurchaseOrderReportMixin, ReportPrintMixin, RetrieveAPI):
    """API endpoint for printing a PurchaseOrderReport object."""

    pass


class SalesOrderReportMixin(ReportFilterMixin):
    """Mixin for the SalesOrderReport report template."""

    ITEM_MODEL = order.models.SalesOrder
    ITEM_KEY = 'order'

    queryset = SalesOrderReport.objects.all()
    serializer_class = SalesOrderReportSerializer


class SalesOrderReportList(SalesOrderReportMixin, ReportListView):
    """API list endpoint for the SalesOrderReport model."""

    pass


class SalesOrderReportDetail(SalesOrderReportMixin, RetrieveUpdateDestroyAPI):
    """API endpoint for a single SalesOrderReport object."""

    pass


class SalesOrderReportPrint(SalesOrderReportMixin, ReportPrintMixin, RetrieveAPI):
    """API endpoint for printing a PurchaseOrderReport object."""

    pass


class ReturnOrderReportMixin(ReportFilterMixin):
    """Mixin for the ReturnOrderReport report template."""

    ITEM_MODEL = order.models.ReturnOrder
    ITEM_KEY = 'order'

    queryset = ReturnOrderReport.objects.all()
    serializer_class = ReturnOrderReportSerializer


class ReturnOrderReportList(ReturnOrderReportMixin, ReportListView):
    """API list endpoint for the ReturnOrderReport model."""

    pass


class ReturnOrderReportDetail(ReturnOrderReportMixin, RetrieveUpdateDestroyAPI):
    """API endpoint for a single ReturnOrderReport object."""

    pass


class ReturnOrderReportPrint(ReturnOrderReportMixin, ReportPrintMixin, RetrieveAPI):
    """API endpoint for printing a ReturnOrderReport object."""

    pass


class StockLocationReportMixin(ReportFilterMixin):
    """Mixin for StockLocation report template."""

    ITEM_MODEL = StockLocation
    ITEM_KEY = 'location'
    queryset = StockLocationReport.objects.all()
    serializer_class = StockLocationReportSerializer


class StockLocationReportList(StockLocationReportMixin, ReportListView):
    """API list endpoint for the StockLocationReportList model."""

    pass


class StockLocationReportDetail(StockLocationReportMixin, RetrieveUpdateDestroyAPI):
    """API endpoint for a single StockLocationReportDetail object."""

    pass


class StockLocationReportPrint(StockLocationReportMixin, ReportPrintMixin, RetrieveAPI):
    """API endpoint for printing a StockLocationReportPrint object."""

    pass


report_api_urls = [
    # Purchase order reports
    re_path(
        r'po/',
        include([
            # Detail views
            path(
                r'<int:pk>/',
                include([
                    re_path(
                        r'print/',
                        PurchaseOrderReportPrint.as_view(),
                        name='api-po-report-print',
                    ),
                    re_path(
                        r'metadata/',
                        MetadataView.as_view(),
                        {'model': PurchaseOrderReport},
                        name='api-po-report-metadata',
                    ),
                    path(
                        '',
                        PurchaseOrderReportDetail.as_view(),
                        name='api-po-report-detail',
                    ),
                ]),
            ),
            # List view
            path('', PurchaseOrderReportList.as_view(), name='api-po-report-list'),
        ]),
    ),
    # Sales order reports
    re_path(
        r'so/',
        include([
            # Detail views
            path(
                r'<int:pk>/',
                include([
                    re_path(
                        r'print/',
                        SalesOrderReportPrint.as_view(),
                        name='api-so-report-print',
                    ),
                    re_path(
                        r'metadata/',
                        MetadataView.as_view(),
                        {'model': SalesOrderReport},
                        name='api-so-report-metadata',
                    ),
                    path(
                        '',
                        SalesOrderReportDetail.as_view(),
                        name='api-so-report-detail',
                    ),
                ]),
            ),
            path('', SalesOrderReportList.as_view(), name='api-so-report-list'),
        ]),
    ),
    # Return order reports
    re_path(
        r'ro/',
        include([
            path(
                r'<int:pk>/',
                include([
                    path(
                        r'print/',
                        ReturnOrderReportPrint.as_view(),
                        name='api-return-order-report-print',
                    ),
                    re_path(
                        r'metadata/',
                        MetadataView.as_view(),
                        {'model': ReturnOrderReport},
                        name='api-so-report-metadata',
                    ),
                    path(
                        '',
                        ReturnOrderReportDetail.as_view(),
                        name='api-return-order-report-detail',
                    ),
                ]),
            ),
            path(
                '', ReturnOrderReportList.as_view(), name='api-return-order-report-list'
            ),
        ]),
    ),
    # Build reports
    re_path(
        r'build/',
        include([
            # Detail views
            path(
                r'<int:pk>/',
                include([
                    re_path(
                        r'print/?',
                        BuildReportPrint.as_view(),
                        name='api-build-report-print',
                    ),
                    re_path(
                        r'metadata/',
                        MetadataView.as_view(),
                        {'model': BuildReport},
                        name='api-build-report-metadata',
                    ),
                    re_path(
                        r'^.$',
                        BuildReportDetail.as_view(),
                        name='api-build-report-detail',
                    ),
                ]),
            ),
            # List view
            re_path(r'^.*$', BuildReportList.as_view(), name='api-build-report-list'),
        ]),
    ),
    # Bill of Material reports
    re_path(
        r'bom/',
        include([
            # Detail views
            path(
                r'<int:pk>/',
                include([
                    re_path(
                        r'print/?',
                        BOMReportPrint.as_view(),
                        name='api-bom-report-print',
                    ),
                    re_path(
                        r'metadata/',
                        MetadataView.as_view(),
                        {'model': BillOfMaterialsReport},
                        name='api-bom-report-metadata',
                    ),
                    re_path(
                        r'^.*$', BOMReportDetail.as_view(), name='api-bom-report-detail'
                    ),
                ]),
            ),
            # List view
            re_path(r'^.*$', BOMReportList.as_view(), name='api-bom-report-list'),
        ]),
    ),
    # Stock item test reports
    re_path(
        r'test/',
        include([
            # Detail views
            path(
                r'<int:pk>/',
                include([
                    re_path(
                        r'print/?',
                        StockItemTestReportPrint.as_view(),
                        name='api-stockitem-testreport-print',
                    ),
                    re_path(
                        r'metadata/',
                        MetadataView.as_view(),
                        {'report': TestReport},
                        name='api-stockitem-testreport-metadata',
                    ),
                    re_path(
                        r'^.*$',
                        StockItemTestReportDetail.as_view(),
                        name='api-stockitem-testreport-detail',
                    ),
                ]),
            ),
            # List view
            re_path(
                r'^.*$',
                StockItemTestReportList.as_view(),
                name='api-stockitem-testreport-list',
            ),
        ]),
    ),
    # Stock Location reports (Stock Location Reports -> sir)
    re_path(
        r'slr/',
        include([
            # Detail views
            path(
                r'<int:pk>/',
                include([
                    re_path(
                        r'print/?',
                        StockLocationReportPrint.as_view(),
                        name='api-stocklocation-report-print',
                    ),
                    re_path(
                        r'metadata/',
                        MetadataView.as_view(),
                        {'report': StockLocationReport},
                        name='api-stocklocation-report-metadata',
                    ),
                    re_path(
                        r'^.*$',
                        StockLocationReportDetail.as_view(),
                        name='api-stocklocation-report-detail',
                    ),
                ]),
            ),
            # List view
            re_path(
                r'^.*$',
                StockLocationReportList.as_view(),
                name='api-stocklocation-report-list',
            ),
        ]),
    ),
]
