"""Label printing plugin which supports printing multiple labels on a single page"""

import logging
import math

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

import weasyprint
from rest_framework import serializers

import report.helpers
from label.models import LabelTemplate
from plugin import InvenTreePlugin
from plugin.mixins import LabelPrintingMixin, SettingsMixin

logger = logging.getLogger('inventree')


class LabelPrintingOptionsSerializer(serializers.Serializer):
    """Custom printing options for the label sheet plugin"""

    page_size = serializers.ChoiceField(
        choices=report.helpers.report_page_size_options(),
        default='A4',
        label=_('Page Size'),
        help_text=_('Page size for the label sheet')
    )

    border = serializers.BooleanField(
        default=False,
        label=_('Border'),
        help_text=_('Print a border around each label')
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
        border = printing_options.get('border', False)

        # Extract size of page
        page_size = report.helpers.page_size(page_size_code)
        page_width, page_height = page_size

        if landscape:
            page_width, page_height = page_height, page_width

        # Calculate number of rows and columns
        n_cols = math.floor(page_width / label.width)
        n_rows = math.floor(page_height / label.height)
        n_cells = n_cols * n_rows

        n_labels = len(items)

        # Data to pass through to each page
        document_data = {
            "border": border,
            "landscape": landscape,
            "page_width": page_width,
            "page_height": page_height,
            "label_width": label.width,
            "label_height": label.height,
            "n_labels": n_labels,
            "n_pages": math.ceil(n_labels / n_cells),
            "n_cols": n_cols,
            "n_rows": n_rows,
        }

        pages = []

        idx = 0

        while idx < n_labels:
            if page := self.print_page(label, items[idx:idx + n_cells], request, **document_data):
                pages.append(page)

            idx += n_cells

        FILENAME = "/workspaces/inventree/dev/out.html"
        PDF_FILENAME = "/workspaces/inventree/dev/out.pdf"

        html_data = self.wrap_pages(pages, **document_data)

        with open(FILENAME, 'w') as file_out:
            file_out.write(html_data)

        # Render resulting outputs
        html = weasyprint.HTML(string=html_data)

        pdf = html.render().write_pdf()

        with open(PDF_FILENAME, 'wb') as file_out:
            file_out.write(pdf)

        raise ValidationError("oh no we don't")

    def print_page(self, label: LabelTemplate, items: list, request, **kwargs):
        """Generate a single page of labels:

        For a single page, generate a simple table grid of labels.
        Styling of the table is handled by the higher level label template

        Arguments:
            label: The LabelTemplate object to use for printing
            items: The list of database items to print (e.g. StockItem instances)
            request: The HTTP request object which triggered this print job

        Kwargs:
            n_cols: Number of columns
            n_rows: Number of rows
        """

        n_cols = kwargs['n_cols']
        n_rows = kwargs['n_rows']

        # Generate a table of labels
        html = """<table class='label-sheet-table'>"""

        for row in range(n_rows):
            html += "<tr class='label-sheet-row'>"

            for col in range(n_cols):
                html += f"<td class='label-sheet-cell label-sheet-row-{row} label-sheet-col-{col}'>"

                # Cell index
                idx = row * n_cols + col

                if idx < len(items):
                    # Render the label
                    try:
                        cell = label.render_as_string(request, target_object=items[idx])
                        html += cell
                    except Exception as exc:
                        logger.exception("Error rendering label: %s", str(exc))
                        return """
                        <div class='label-sheet-cell-error'></div>
                        """

                html += "</td>"

            html += "</tr>"

        html += "</table>"

        return html

    def wrap_pages(self, pages, **kwargs):
        """Wrap the generated pages into a single document"""

        border = kwargs['border']

        page_width = kwargs['page_width']
        page_height = kwargs['page_height']

        label_width = kwargs['label_width']
        label_height = kwargs['label_height']

        n_rows = kwargs['n_rows']
        n_cols = kwargs['n_cols']

        inner = ''.join(pages)

        # Generate styles for individual cells (on each page)
        cell_styles = []

        for row in range(n_rows):
            cell_styles.append(f"""
            .label-sheet-row-{row} {{
                top: {row * label_height}mm;
            }}
            """)

        for col in range(n_cols):
            cell_styles.append(f"""
            .label-sheet-col-{col} {{
                left: {col * label_width}mm;
            }}
            """)

        cell_styles = "\n".join(cell_styles)

        return f"""
        <head>
            <style>
                @page {{
                    size: {page_width}mm {page_height}mm;
                    margin: 0mm;
                    padding: 0mm;
                }}

                .label-sheet-table {{
                    page-break-after: always;
                    table-layout: fixed;
                    width: {page_width}mm;
                    border-spacing: 0mm 0mm;
                }}

                .label-sheet-row {{

                }}

                .label-sheet-cell-error {{
                    background-color: #F00;
                }}

                .label-sheet-cell {{
                    border: {"1px solid #000;" if border else "0mm;"}
                    width: {label_width}mm;
                    height: {label_height}mm;
                    padding: 0mm;
                    position: absolute;
                }}

                {cell_styles}

                body {{
                    margin: 0mm !important;
                }}
            </style>
        </head>
        <body>
            {inner}
        </body>
        </html>
        """
