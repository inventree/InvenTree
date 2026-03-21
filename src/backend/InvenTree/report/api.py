"""API functionality for the 'report' app."""

from django.core.exceptions import ValidationError
from django.urls import include, path
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache

import django_filters.rest_framework.filters as rest_filters
from django_filters.rest_framework import DjangoFilterBackend
from django_filters.rest_framework.filterset import FilterSet
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

import InvenTree.permissions
import report.helpers
import report.models
import report.serializers
from common.models import DataOutput
from common.serializers import DataOutputSerializer
from InvenTree.api import meta_path
from InvenTree.filters import InvenTreeSearchFilter
from InvenTree.mixins import ListCreateAPI, RetrieveUpdateDestroyAPI
from plugin import PluginMixinEnum
from plugin.builtin.labels.inventree_label import InvenTreeLabelPlugin


class TemplatePermissionMixin:
    """Permission mixin for report and label templates."""

    # Read only for non-staff users
    permission_classes = [InvenTree.permissions.IsStaffOrReadOnlyScope]


class ReportFilterBase(FilterSet):
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
    permission_classes = [InvenTree.permissions.IsAuthenticatedOrReadScope]
    serializer_class = report.serializers.LabelPrintSerializer

    def get_plugin_class(self, plugin_slug: str, raise_error=False):
        """Return the plugin class for the given plugin key."""
        from plugin import registry

        if not plugin_slug:
            # Use the default label printing plugin
            plugin_slug = InvenTreeLabelPlugin.NAME.lower()

        plugin = registry.get_plugin(plugin_slug, active=True)

        error = None

        if not plugin:
            error = _('Plugin not found')
        elif not plugin.mixin_enabled(PluginMixinEnum.LABELS):
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

        return super().get_serializer(*args, **kwargs)

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

        # Sort the instances by the order of the provided items
        instances = sorted(instances, key=lambda item: items.index(item.pk))

        if len(instances) == 0:
            raise ValidationError(_('No valid items provided to template'))

        return self.print(template, instances, plugin, request)

    def print(self, template, items_to_print, plugin, request):
        """Print this label template against a number of provided items."""
        import report.tasks
        from InvenTree.tasks import offload_task

        if plugin_serializer := plugin.get_printing_options_serializer(
            request, data=request.data, context=self.get_serializer_context()
        ):
            plugin_serializer.is_valid(raise_exception=True)

        user = getattr(request, 'user', None)

        # Generate a new DataOutput object to print against
        output = DataOutput.objects.create(
            user=user if user and user.is_authenticated else None,
            total=len(items_to_print),
            progress=0,
            complete=False,
            output_type=DataOutput.DataOutputTypes.LABEL,
            plugin=plugin.slug,
            template_name=template.name,
            output=None,
        )

        output.refresh_from_db()

        offload_task(
            report.tasks.print_labels,
            template.pk,
            [item.pk for item in items_to_print],
            output.pk,
            plugin.slug,
            options=(plugin_serializer.data if plugin_serializer else {}),
        )

        output.refresh_from_db()

        return Response(DataOutputSerializer(output).data, status=201)


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
    permission_classes = [InvenTree.permissions.IsAuthenticatedOrReadScope]
    serializer_class = report.serializers.ReportPrintSerializer

    @method_decorator(never_cache)
    def post(self, request, *args, **kwargs):
        """POST action for printing a report."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        template = serializer.validated_data['template']
        items = serializer.validated_data['items']

        instances = template.get_model().objects.filter(pk__in=items)

        # Sort the instances by the order of the provided items
        instances = sorted(instances, key=lambda item: items.index(item.pk))

        if len(instances) == 0:
            raise ValidationError(_('No valid items provided to template'))

        return self.print(template, instances, request)

    def print(self, template, items_to_print, request):
        """Print this report template against a number of provided items.

        This functionality is offloaded to the background worker process,
        which will update the status of the DataOutput object as it progresses.
        """
        import report.tasks
        from InvenTree.tasks import offload_task

        user = getattr(request, 'user', None)

        # Generate a new DataOutput object
        output = DataOutput.objects.create(
            user=user if user and user.is_authenticated else None,
            total=len(items_to_print),
            progress=0,
            complete=False,
            output_type=DataOutput.DataOutputTypes.REPORT,
            template_name=template.name,
            output=None,
        )

        item_ids = [item.pk for item in items_to_print]

        # Offload the task to the background worker
        offload_task(report.tasks.print_reports, template.pk, item_ids, output.pk)

        output.refresh_from_db()

        return Response(DataOutputSerializer(output).data, status=201)


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
                    meta_path(report.models.LabelTemplate),
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
                    meta_path(report.models.ReportTemplate),
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
