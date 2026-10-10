"""Custom exporter for Parameter data."""

from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from plugin import InvenTreePlugin
from plugin.mixins import DataExportMixin


class ParameterExportOptionsSerializer(serializers.Serializer):
    """Custom export options for the ParameterExporter plugin."""

    export_exclude_inactive_parameters = serializers.BooleanField(
        default=True,
        label=_('Exclude Inactive'),
        help_text=_('Exclude parameters which are inactive'),
    )


class ParameterExporter(DataExportMixin, InvenTreePlugin):
    """Builtin plugin for exporting Parameter data.

    Extends the export process, to include all associated Parameter data.
    """

    NAME = 'Parameter Exporter'
    SLUG = 'parameter-exporter'
    TITLE = _('Parameter Exporter')
    DESCRIPTION = _('Exporter for model parameter data')
    VERSION = '2.0.0'
    AUTHOR = _('InvenTree contributors')

    ExportOptionsSerializer = ParameterExportOptionsSerializer

    def supports_export(
        self,
        model_class: type,
        user=None,
        serializer_class=None,
        view_class=None,
        *args,
        **kwargs,
    ) -> bool:
        """Supported if the base model implements the InvenTreeParameterMixin."""
        from InvenTree.models import InvenTreeParameterMixin

        return issubclass(model_class, InvenTreeParameterMixin)

    def update_headers(self, headers, context, **kwargs):
        """Update headers for the export."""
        # Add in a header for each parameter
        for pk, name in self.parameters.items():
            headers[f'parameter_{pk}'] = str(name)

        return headers

    def prefetch_queryset(self, queryset):
        """Ensure that the associated parameters are prefetched."""
        from InvenTree.models import InvenTreeParameterMixin

        queryset = InvenTreeParameterMixin.annotate_parameters(queryset)
        return queryset

    def export_data(
        self, queryset, serializer_class, headers, context, output, **kwargs
    ):
        """Export parameter data."""
        # Extract custom serializer options and cache
        queryset = self.prefetch_queryset(queryset)
        self.serializer_class = serializer_class

        self.exclude_inactive = context.get('export_exclude_inactive_parameters', True)

        # Keep a dict of observed parameters against their primary key
        self.parameters = {}

        # Serialize the queryset using DRF first
        rows = self.serializer_class(
            queryset, parameters=True, exporting=True, many=True
        ).data

        for row in rows:
            # Extract the associated parameters from the serialized data
            for parameter in row.get('parameters', []):
                template_detail = parameter['template_detail']
                template_id = template_detail['pk']

                active = template_detail.get('enabled', True)

                if not active and self.exclude_inactive:
                    continue

                self.parameters[template_id] = template_detail['name']

                row[f'parameter_{template_id}'] = parameter['data']

        return rows
