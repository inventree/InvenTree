"""Generic data export plugin for InvenTree."""

from django.utils.translation import gettext_lazy as _

from plugin import InvenTreePlugin
from plugin.mixins import DataExportMixin, SettingsMixin


class InvenTreeExporter(DataExportMixin, SettingsMixin, InvenTreePlugin):
    """Generic exporter plugin for InvenTree."""

    NAME = 'InvenTree Exporter'
    SLUG = 'inventree-exporter'
    TITLE = _('InvenTree Generic Exporter')
    DESCRIPTION = _('Provides support for exporting data from InvenTree')
    VERSION = '1.0.0'
    AUTHOR = _('InvenTree contributors')

    SETTINGS = {}

    def supports_model(self, model_class: type) -> bool:
        """This exporter supports all model classes."""
        return True
