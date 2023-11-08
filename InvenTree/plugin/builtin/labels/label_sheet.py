"""Label printing plugin which supports printing multiple labels on a single page"""

from django.utils.translation import gettext_lazy as _

from label.models import LabelTemplate
from plugin import InvenTreePlugin
from plugin.mixins import LabelPrintingMixin, SettingsMixin


class InvenTreeLabelSheetPlugin(LabelPrintingMixin, SettingsMixin, InvenTreePlugin):
    """Builtin plugin for label printing.

    This plugin arrays multiple labels onto a single larger sheet,
    and returns the resulting PDF file.
    """

    NAME = "InvenTreeLabelSheet"
    TITLE = _("InvenTree Label Sheet Printer")
    DESCRIPTION = _("Arrays multiple labels onto a single sheet")
    VERSION = "1.0.0"
    AUTHOR = _("InvenTree contributors")

    BLOCKING_PRINT = True

    SETTINGS = {}

    def print_labels(self, label: LabelTemplate, items: list, request, **kwargs):
        """Handle printing of the provided labels"""

        print("printing label sheet:", len(items), "labels -", label)
