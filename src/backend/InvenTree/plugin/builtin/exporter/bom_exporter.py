"""Multi-level BOM exporter plugin."""

from django.utils.translation import gettext_lazy as _

import rest_framework.serializers as serializers

from plugin import InvenTreePlugin
from plugin.mixins import DataExportMixin, SettingsMixin


class BomExporterOptionsSerializer(serializers.Serializer):
    """Custom export options for the BOM exporter plugin."""

    levels = serializers.IntegerField(
        default=1,
        label=_('Levels'),
        help_text=_('Number of levels to export'),
        min_value=0,
    )


class BomExporterPlugin(DataExportMixin, SettingsMixin, InvenTreePlugin):
    """Builtin plugin for performing multi-level BOM exports."""

    NAME = 'BomExporter'
    SLUG = 'bom-exporter'
    TITLE = _('InvenTree BOM exporter')
    DESCRIPTION = _('Provides support for exporting multi-level BOMs')
    VERSION = '1.0.0'
    AUTHOR = _('InvenTree contributors')

    SETTINGS = {}

    ExportOptionsSerializer = BomExporterOptionsSerializer
