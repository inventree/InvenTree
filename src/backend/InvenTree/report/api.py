"""API functionality for the 'report' app."""

from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.template.exceptions import TemplateDoesNotExist
from django.urls import include, path, re_path
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import cache_page, never_cache

from django_filters import rest_framework as rest_filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response

import common.models
import InvenTree.exceptions
import InvenTree.helpers
import report.helpers
import report.models
import report.serializers
from InvenTree.api import MetadataView
from InvenTree.exceptions import log_error
from InvenTree.filters import InvenTreeSearchFilter
from InvenTree.mixins import ListCreateAPI, RetrieveAPI, RetrieveUpdateDestroyAPI
from plugin.registry import registry


class ReportFilter(rest_filters.FilterSet):
    """Filter class for report template list."""

    class Meta:
        """Filter options."""

        model = report.models.ReportTemplate
        fields = ['enabled', 'landscape']

    model_type = rest_filters.ChoiceFilter(
        choices=report.helpers.report_model_options(), label=_('Model Type')
    )

    items = rest_filters.CharFilter(method='filter_items', label=_('Items'))
    # items = rest_filters.AllValuesMultipleFilter(method='filter_items', label=_('Items'))

    def filter_items(self, queryset, name, values):
        """Filter against a comma-separated list of provided items.

        Note: This filter is only applied if the 'model_type' is also provided.
        """
        model_type = self.data.get('model_type', None)
        values = self.request.query_params.getlist('items', [])

        if not model_type or len(values) == 0:
            return queryset

        if model_class := report.helpers.report_model_from_name(model_type):
            model_items = model_class.objects.filter(pk__in=values)

            # Ensure that we have already filtered by model_type
            queryset = queryset.filter(model_type=model_type)

            # Construct a list of templates which match the list of provided IDs
            matching_template_ids = []

            for template in queryset.all():
                filters = template.get_filters()
                results = model_items.filter(**filters)
                # If the resulting queryset is *shorter* than the provided items, then this template does not match
                if results.count() == model_items.count():
                    matching_template_ids.append(template.pk)

            queryset = queryset.filter(pk__in=matching_template_ids)

        return queryset


@method_decorator(cache_page(5), name='dispatch')
class ReportTemplatePrint(RetrieveAPI):
    """API endpoint for printing reports against a single template."""

    queryset = report.models.ReportTemplate.objects.all()

    @method_decorator(never_cache)
    def dispatch(self, *args, **kwargs):
        """Prevent caching when printing report templates."""
        return super().dispatch(*args, **kwargs)

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
            for instance in items_to_print:
                report = self.get_object()

                report_name = report.generate_filename(request)

                output = report.render(instance, request)

                # Provide generated report to any interested plugins
                for plugin in registry.with_mixin('report'):
                    try:
                        plugin.report_callback(self, instance, output, request)
                    except Exception as e:
                        InvenTree.exceptions.log_error(
                            f'plugins.{plugin.slug}.report_callback'
                        )

                try:
                    if debug_mode:
                        outputs.append(report.render_as_string(instance, request))
                    else:
                        outputs.append(report.render(instance, request))
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
            if InvenTree.helpers.str2bool(
                common.models.InvenTreeSetting.get_setting(
                    'REPORT_LOG_ERRORS', cache=False
                )
            ):
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
        # Extract a list of items to print from the queryset
        item_ids = request.query_params.get('items', '').split(',')

        template = self.get_object()

        items = template.get_model().objects.filter(pk__in=item_ids)

        return self.print(request, items)


class ReportTemplateList(ListCreateAPI):
    """API endpoint for viewing list of ReportTemplate objects."""

    queryset = report.models.ReportTemplate.objects.all()
    serializer_class = report.serializers.ReportSerializer
    filterset_class = ReportFilter
    filter_backends = [DjangoFilterBackend, InvenTreeSearchFilter]

    search_fields = ['name', 'description']

    ordering_fields = ['name', 'enabled']


class ReportTemplateDetail(RetrieveUpdateDestroyAPI):
    """Detail API endpoint for report template model."""

    queryset = report.models.ReportTemplate.objects.all()
    serializer_class = report.serializers.ReportSerializer


class ReportSnippetList(ListCreateAPI):
    """API endpoint for listing ReportSnippet objects."""

    queryset = report.models.ReportSnippet.objects.all()
    serializer_class = report.serializers.ReportSnippetSerializer


class ReportSnippetDetail(RetrieveUpdateDestroyAPI):
    """API endpoint for a single ReportSnippet object."""

    queryset = report.models.ReportSnippet.objects.all()
    serializer_class = report.serializers.ReportSnippetSerializer


class ReportAssetList(ListCreateAPI):
    """API endpoint for listing ReportAsset objects."""

    queryset = report.models.ReportAsset.objects.all()
    serializer_class = report.serializers.ReportAssetSerializer


class ReportAssetDetail(RetrieveUpdateDestroyAPI):
    """API endpoint for a single ReportAsset object."""

    queryset = report.models.ReportAsset.objects.all()
    serializer_class = report.serializers.ReportAssetSerializer


report_api_urls = [
    # Report templates
    path(
        'template/',
        include([
            path(
                '<int:pk>/',
                include([
                    path(
                        'print/',
                        ReportTemplatePrint.as_view(),
                        name='api-report-template-print',
                    ),
                    path(
                        'metadata/',
                        MetadataView.as_view(),
                        {'model': report.models.ReportTemplate},
                        name='api-report-template-metadata',
                    ),
                    path(
                        '',
                        ReportTemplateDetail.as_view(),
                        name='api-report-template-detail',
                    ),
                ]),
            ),
            path('', ReportTemplateList.as_view(), name='api-report-template-list'),
        ]),
    ),
    # Report assets
    path(
        'asset/',
        include([
            path(
                '<int:pk>/', ReportAssetDetail.as_view(), name='api-report-asset-detail'
            ),
            path('', ReportAssetList.as_view(), name='api-report-asset-list'),
        ]),
    ),
    # Report snippets
    path(
        'snippet/',
        include([
            path(
                '<int:pk>/',
                ReportSnippetDetail.as_view(),
                name='api-report-snippet-detail',
            ),
            path('', ReportSnippetList.as_view(), name='api-report-snippet-list'),
        ]),
    ),
]
