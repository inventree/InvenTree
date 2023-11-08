"""Label printing plugin which supports printing multiple labels on a single page"""

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

import report.helpers
from label.models import LabelTemplate
from plugin import InvenTreePlugin
from plugin.mixins import LabelPrintingMixin, SettingsMixin


class LabelPrintingOptionsSerializer(serializers.Serializer):
    """Custom printing options for the label sheet plugin"""

    page_size = serializers.ChoiceField(
        choices=report.helpers.report_page_size_options(),
        default='A4',
        label=_('Page Size'),
        help_text=_('Page size for the label sheet')
    )


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

    PrintingOptionsSerializer = LabelPrintingOptionsSerializer

    def print_labels(self, label: LabelTemplate, items: list, request, **kwargs):
        """Handle printing of the provided labels"""

        for item in items:
            output = label.render_as_string(request, target_object=item)

            print("output:", output)

        raise ValidationError("oh no we don't")
