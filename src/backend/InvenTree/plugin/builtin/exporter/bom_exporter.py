"""Multi-level BOM exporter plugin."""

from django.utils.translation import gettext_lazy as _

import rest_framework.serializers as serializers

from part.models import BomItem
from plugin import InvenTreePlugin
from plugin.mixins import DataExportMixin, SettingsMixin


class BomExporterOptionsSerializer(serializers.Serializer):
    """Custom export options for the BOM exporter plugin."""

    export_levels = serializers.IntegerField(
        default=1,
        label=_('Levels'),
        help_text=_('Number of levels to export'),
        min_value=0,
    )


class BomExporterPlugin(DataExportMixin, SettingsMixin, InvenTreePlugin):
    """Builtin plugin for performing multi-level BOM exports."""

    NAME = 'BOM Exporter'
    SLUG = 'bom-exporter'
    TITLE = _('InvenTree BOM exporter')
    DESCRIPTION = _('Provides support for exporting multi-level BOMs')
    VERSION = '1.0.0'
    AUTHOR = _('InvenTree contributors')

    SETTINGS = {}

    ExportOptionsSerializer = BomExporterOptionsSerializer

    def supports_export(self, model_class: type, user, *args, **kwargs) -> bool:
        """This exported only supports the BomItem model."""
        return model_class == BomItem

    def export_data(self, queryset, serializer_class, headers, context, **kwargs):
        """Export BOM data from the queryset."""
        # TODO: Custom BOM export!

        return super().export_data(
            queryset, serializer_class, headers, context, **kwargs
        )
