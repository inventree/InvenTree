"""Label printing plugin which supports printing multiple labels on a single page"""

import math

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

    landscape = serializers.BooleanField(
        default=False,
        label=_('Landscape'),
        help_text=_('Print the label sheet in landscape mode')
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

        printing_options = kwargs['printing_options']

        # Extract page size for the label sheet
        page_size_code = printing_options.get('page_size', 'A4')
        landscape = printing_options.get('landscape', False)
        page_size = report.helpers.page_size(page_size_code)

        page_width, page_height = page_size

        if landscape:
            page_width, page_height = page_height, page_width

        # Calculate number of rows and columns
        n_cols = math.floor(page_width / label.width)
        n_rows = math.floor(page_height / label.height)
        n_cells = n_cols * n_rows

        print("printing:", n_cols, n_rows, '->', n_cells)

        for item in items:
            output = label.render_as_string(request, target_object=item)

            print("output:", output)

        raise ValidationError("oh no we don't")

    def print_page(self, label: LabelTemplate, items: list, request, **kwargs):
        """Print a single page of labels"""
        ...
