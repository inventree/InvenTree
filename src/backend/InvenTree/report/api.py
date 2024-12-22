"""API functionality for the 'report' app."""

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.template.exceptions import TemplateDoesNotExist
from django.urls import include, path
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import cache_page, never_cache

from django_filters import rest_framework as rest_filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions
from rest_framework.generics import GenericAPIView
from rest_framework.request import clone_request
from rest_framework.response import Response

import common.models
import InvenTree.exceptions
import InvenTree.helpers
import InvenTree.permissions
import report.helpers
import report.models
import report.serializers
from InvenTree.api import BulkDeleteMixin, MetadataView
from InvenTree.exceptions import log_error
from InvenTree.filters import InvenTreeSearchFilter
from InvenTree.mixins import (
    ListAPI,
    ListCreateAPI,
    RetrieveAPI,
    RetrieveUpdateDestroyAPI,
)
from plugin.builtin.labels.inventree_label import InvenTreeLabelPlugin
from plugin.registry import registry


class TemplatePermissionMixin:
    """Permission mixin for report and label templates."""

    # Read only for non-staff users
    permission_classes = [
        permissions.IsAuthenticated,
        InvenTree.permissions.IsStaffOrReadOnly,
    ]


@method_decorator(cache_page(5), name='dispatch')
class TemplatePrintBase(RetrieveAPI):
    """Base class for printing against templates."""

    @method_decorator(never_cache)
    def dispatch(self, *args, **kwargs):
        """Prevent caching when printing report templates."""
        return super().dispatch(*args, **kwargs)

    def check_permissions(self, request):
        """Override request method to GET so that also non superusers can print using a post request."""
        if request.method == 'POST':
            request = clone_request(request, 'GET')
        return super().check_permissions(request)

    def post(self, request, *args, **kwargs):
        """Respond as if a POST request was provided."""
        return self.get(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        """GET action for a template printing endpoint.

        - Items are expected to be passed as a list of valid IDs
        """
        # Extract a list of items to print from the queryset
        item_ids = []

        for value in request.query_params.get('items', '').split(','):
            try:
                item_ids.append(int(value))
            except Exception:
                pass

        template = self.get_object()

        items = template.get_model().objects.filter(pk__in=item_ids)

        if len(items) == 0:
            # At least one item must be provided
            return Response(
                {'error': _('No valid objects provided to template')}, status=400
            )

        return self.print(request, items)


class ReportFilterBase(rest_filters.FilterSet):
    """Base filter class for label and report templates."""

    enabled = rest_filters.BooleanFilter()

    model_type = rest_filters.ChoiceFilter(
        choices=report.helpers.report_model_options(), label=_('Model Type')
    )

    items = rest_filters.CharFilter(method='filter_items', label=_('Items'))

    def filter_items(self, queryset, name, values):
        """Filter against a comma-separated list of provided items.

        Note: This filter is only applied if the 'model_type' is also provided.
        """
        model_type = self.data.get('model_type', None)
        values = values.strip().split(',')

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


class ReportFilter(ReportFilterBase):
    """Filter class for report template list."""

    class Meta:
        """Filter options."""

        model = report.models.ReportTemplate
        fields = ['landscape']


class LabelFilter(ReportFilterBase):
    """Filter class for label template list."""

    class Meta:
        """Filter options."""

        model = report.models.LabelTemplate
        fields = []


class LabelPrint(GenericAPIView):
    """API endpoint for printing labels."""

    # Any authenticated user can print labels
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = report.serializers.LabelPrintSerializer

    def get_plugin_class(self, plugin_slug: str, raise_error=False):
        """Return the plugin class for the given plugin key."""
        from plugin.models import PluginConfig

        if not plugin_slug:
            # Use the default label printing plugin
            plugin_slug = InvenTreeLabelPlugin.NAME.lower()

        plugin = None

        try:
            plugin_config = PluginConfig.objects.get(key=plugin_slug)
            plugin = plugin_config.plugin
        except (ValueError, PluginConfig.DoesNotExist):
            pass

        error = None

        if not plugin:
            error = _('Plugin not found')
        elif not plugin.is_active():
            error = _('Plugin is not active')
        elif not plugin.mixin_enabled('labels'):
            error = _('Plugin does not support label printing')

        if error:
            plugin = None

            if raise_error:
                raise ValidationError({'plugin': error})

        return plugin

    def get_plugin_serializer(self, plugin):
        """Return the serializer for the given plugin."""
        if plugin and hasattr(plugin, 'get_printing_options_serializer'):
            return plugin.get_printing_options_serializer(
                self.request,
                data=self.request.data,
                context=self.get_serializer_context(),
            )

        return None

    def get_serializer(self, *args, **kwargs):
        """Return serializer information for the label print endpoint."""
        plugin = None

        # Plugin information provided?
        if self.request:
            plugin_key = self.request.data.get('plugin', '')
            # Legacy url based lookup
            if not plugin_key:
                plugin_key = self.request.query_params.get('plugin', '')
            plugin = self.get_plugin_class(plugin_key)
            plugin_serializer = self.get_plugin_serializer(plugin)

            if plugin_serializer:
                kwargs['plugin_serializer'] = plugin_serializer

        serializer = super().get_serializer(*args, **kwargs)
        return serializer

    @method_decorator(never_cache)
    def post(self, request, *args, **kwargs):
        """POST action for printing labels."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        template = serializer.validated_data['template']

        if template.width <= 0 or template.height <= 0:
            raise ValidationError({'template': _('Invalid label dimensions')})

        items = serializer.validated_data['items']

        # Default to the InvenTreeLabelPlugin
        plugin_key = InvenTreeLabelPlugin.NAME.lower()

        if plugin_config := serializer.validated_data.get('plugin', None):
            plugin_key = plugin_config.key

        plugin = self.get_plugin_class(plugin_key, raise_error=True)

        instances = template.get_model().objects.filter(pk__in=items)

        if instances.count() == 0:
            raise ValidationError(_('No valid items provided to template'))

        return self.print(template, instances, plugin, request)

    def print(self, template, items_to_print, plugin, request):
        """Print this label template against a number of provided items."""
        if plugin_serializer := plugin.get_printing_options_serializer(
            request, data=request.data, context=self.get_serializer_context()
        ):
            plugin_serializer.is_valid(raise_exception=True)

        # Create a new LabelOutput instance to print against
        output = report.models.LabelOutput.objects.create(
            template=template,
            items=len(items_to_print),
            plugin=plugin.slug,
            user=request.user,
            progress=0,
            complete=False,
        )

        try:
            plugin.before_printing()
            plugin.print_labels(
                template,
                output,
                items_to_print,
                request,
                printing_options=(plugin_serializer.data if plugin_serializer else {}),
            )
            plugin.after_printing()
        except ValidationError as e:
            raise (e)
        except Exception as e:
            InvenTree.exceptions.log_error(f'plugins.{plugin.slug}.print_labels')
            raise ValidationError([_('Error printing label'), str(e)])

        output.refresh_from_db()

        return Response(
            report.serializers.LabelOutputSerializer(output).data, status=201
        )


class LabelTemplateList(TemplatePermissionMixin, ListCreateAPI):
    """API endpoint for viewing list of LabelTemplate objects."""

    queryset = report.models.LabelTemplate.objects.all()
    serializer_class = report.serializers.LabelTemplateSerializer
    filterset_class = LabelFilter
    filter_backends = [DjangoFilterBackend, InvenTreeSearchFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'enabled']


class LabelTemplateDetail(TemplatePermissionMixin, RetrieveUpdateDestroyAPI):
    """Detail API endpoint for label template model."""

    queryset = report.models.LabelTemplate.objects.all()
    serializer_class = report.serializers.LabelTemplateSerializer


class ReportPrint(GenericAPIView):
    """API endpoint for printing reports."""

    # Any authenticated user can print reports
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = report.serializers.ReportPrintSerializer

    @method_decorator(never_cache)
    def post(self, request, *args, **kwargs):
        """POST action for printing a report."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        template = serializer.validated_data['template']
        items = serializer.validated_data['items']

        instances = template.get_model().objects.filter(pk__in=items)

        if instances.count() == 0:
            raise ValidationError(_('No valid items provided to template'))

        return self.print(template, instances, request)

    def print(self, template, items_to_print, request):
        """Print this report template against a number of provided items."""
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
                context = template.get_context(instance, request)
                report_name = template.generate_filename(context)

                output = template.render(instance, request)

                if template.attach_to_model:
                    # Attach the generated report to the model instance
                    data = output.get_document().write_pdf()
                    instance.create_attachment(
                        attachment=ContentFile(data, report_name),
                        comment=_('Report saved at time of printing'),
                        upload_user=request.user,
                    )

                # Provide generated report to any interested plugins
                for plugin in registry.with_mixin('report'):
                    try:
                        plugin.report_callback(self, instance, output, request)
                    except Exception:
                        InvenTree.exceptions.log_error(
                            f'plugins.{plugin.slug}.report_callback'
                        )

                try:
                    if debug_mode:
                        outputs.append(template.render_as_string(instance, request))
                    else:
                        outputs.append(template.render(instance, request))
                except TemplateDoesNotExist as e:
                    template = str(e)
                    if not template:
                        template = template.template

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

                data = '\n'.join(outputs)
                report_name = report_name.replace('.pdf', '.html')
            else:
                """Concatenate all rendered pages into a single PDF object, and return the resulting document!"""

                pages = []

                try:
                    for output in outputs:
                        doc = output.get_document()
                        for page in doc.pages:
                            pages.append(page)

                    data = outputs[0].get_document().copy(pages).write_pdf()

                except TemplateDoesNotExist as e:
                    template = str(e)

                    if not template:
                        template = template.template

                    return Response(
                        {
                            'error': _(
                                f"Template file '{template}' is missing or does not exist"
                            )
                        },
                        status=400,
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

        # Generate a report output object
        # TODO: This should be moved to a separate function
        # TODO: Allow background printing of reports, with progress reporting
        output = report.models.ReportOutput.objects.create(
            template=template,
            items=len(items_to_print),
            user=request.user,
            progress=100,
            complete=True,
            output=ContentFile(data, report_name),
        )

        return Response(
            report.serializers.ReportOutputSerializer(output).data, status=201
        )


class ReportTemplateList(TemplatePermissionMixin, ListCreateAPI):
    """API endpoint for viewing list of ReportTemplate objects."""

    queryset = report.models.ReportTemplate.objects.all()
    serializer_class = report.serializers.ReportTemplateSerializer
    filterset_class = ReportFilter
    filter_backends = [DjangoFilterBackend, InvenTreeSearchFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'enabled']


class ReportTemplateDetail(TemplatePermissionMixin, RetrieveUpdateDestroyAPI):
    """Detail API endpoint for report template model."""

    queryset = report.models.ReportTemplate.objects.all()
    serializer_class = report.serializers.ReportTemplateSerializer


class ReportSnippetList(TemplatePermissionMixin, ListCreateAPI):
    """API endpoint for listing ReportSnippet objects."""

    queryset = report.models.ReportSnippet.objects.all()
    serializer_class = report.serializers.ReportSnippetSerializer


class ReportSnippetDetail(TemplatePermissionMixin, RetrieveUpdateDestroyAPI):
    """API endpoint for a single ReportSnippet object."""

    queryset = report.models.ReportSnippet.objects.all()
    serializer_class = report.serializers.ReportSnippetSerializer


class ReportAssetList(TemplatePermissionMixin, ListCreateAPI):
    """API endpoint for listing ReportAsset objects."""

    queryset = report.models.ReportAsset.objects.all()
    serializer_class = report.serializers.ReportAssetSerializer


class ReportAssetDetail(TemplatePermissionMixin, RetrieveUpdateDestroyAPI):
    """API endpoint for a single ReportAsset object."""

    queryset = report.models.ReportAsset.objects.all()
    serializer_class = report.serializers.ReportAssetSerializer


class LabelOutputList(TemplatePermissionMixin, BulkDeleteMixin, ListAPI):
    """List endpoint for LabelOutput objects."""

    queryset = report.models.LabelOutput.objects.all()
    serializer_class = report.serializers.LabelOutputSerializer


class ReportOutputList(TemplatePermissionMixin, BulkDeleteMixin, ListAPI):
    """List endpoint for ReportOutput objects."""

    queryset = report.models.ReportOutput.objects.all()
    serializer_class = report.serializers.ReportOutputSerializer


label_api_urls = [
    # Printing endpoint
    path('print/', LabelPrint.as_view(), name='api-label-print'),
    # Label templates
    path(
        'template/',
        include([
            path(
                '<int:pk>/',
                include([
                    path(
                        'metadata/',
                        MetadataView.as_view(),
                        {'model': report.models.LabelTemplate},
                        name='api-label-template-metadata',
                    ),
                    path(
                        '',
                        LabelTemplateDetail.as_view(),
                        name='api-label-template-detail',
                    ),
                ]),
            ),
            path('', LabelTemplateList.as_view(), name='api-label-template-list'),
        ]),
    ),
    # Label outputs
    path(
        'output/',
        include([path('', LabelOutputList.as_view(), name='api-label-output-list')]),
    ),
]

report_api_urls = [
    # Printing endpoint
    path('print/', ReportPrint.as_view(), name='api-report-print'),
    # Report templates
    path(
        'template/',
        include([
            path(
                '<int:pk>/',
                include([
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
    # Generated report outputs
    path(
        'output/',
        include([path('', ReportOutputList.as_view(), name='api-report-output-list')]),
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
