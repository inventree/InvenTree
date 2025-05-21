"""Label printing plugin which supports printing multiple labels on a single page."""

import math

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.utils.translation import gettext_lazy as _

import structlog
import weasyprint
from rest_framework import serializers

import report.helpers
from common.models import DataOutput
from InvenTree.helpers import str2bool
from plugin import InvenTreePlugin
from plugin.mixins import LabelPrintingMixin, SettingsMixin
from report.models import LabelTemplate

logger = structlog.get_logger('inventree')


class LabelPrintingOptionsSerializer(serializers.Serializer):
    """Custom printing options for the label sheet plugin."""

    page_size = serializers.ChoiceField(
        choices=report.helpers.report_page_size_options(),
        default='A4',
        label=_('Page Size'),
        help_text=_('Page size for the label sheet'),
    )

    skip = serializers.IntegerField(
        default=0,
        label=_('Skip Labels'),
        help_text=_('Skip this number of labels when printing label sheets'),
        min_value=0,
    )

    border = serializers.BooleanField(
        default=False,
        label=_('Border'),
        help_text=_('Print a border around each label'),
    )

    landscape = serializers.BooleanField(
        default=False,
        label=_('Landscape'),
        help_text=_('Print the label sheet in landscape mode'),
    )

    margin = serializers.IntegerField(
        default=10,
        label=_('Page Margin'),
        help_text=_('Margin around the page in mm'),
        min_value=0,
    )


class InvenTreeLabelSheetPlugin(LabelPrintingMixin, SettingsMixin, InvenTreePlugin):
    """Builtin plugin for label printing.

    This plugin arrays multiple labels onto a single larger sheet,
    and returns the resulting PDF file.
    """

    NAME = 'InvenTreeLabelSheet'
    TITLE = _('InvenTree Label Sheet Printer')
    DESCRIPTION = _('Arrays multiple labels onto a single sheet')
    VERSION = '1.0.1'
    AUTHOR = _('InvenTree contributors')

    BLOCKING_PRINT = True

    SETTINGS = {
        'DEBUG': {
            'name': _('Debug mode'),
            'description': _('Enable debug mode - returns raw HTML instead of PDF'),
            'validator': bool,
            'default': False,
        }
    }

    PrintingOptionsSerializer = LabelPrintingOptionsSerializer

    def print_labels(
        self, label: LabelTemplate, output: DataOutput, items: list, request, **kwargs
    ):
        """Handle printing of the provided labels.

        Note that we override the entire print_labels method for this plugin.
        """
        printing_options = kwargs['printing_options']

        # Extract page size for the label sheet
        page_size_code = printing_options.get('page_size', 'A4')
        landscape = printing_options.get('landscape', False)
        border = printing_options.get('border', False)
        skip = int(printing_options.get('skip', 0))

        # Get margin from printing options
        margin = printing_options.get('margin', 10)

        # Extract size of page
        page_size = report.helpers.page_size(page_size_code)
        page_width, page_height = page_size

        if landscape:
            page_width, page_height = page_height, page_width

        # Calculate available space after margins
        available_width = page_width - (2 * margin)
        available_height = page_height - (2 * margin)

        # Calculate number of rows and columns based on available space
        n_cols = math.floor(available_width / label.width)
        n_rows = math.floor(available_height / label.height)
        n_cells = n_cols * n_rows

        if n_cells == 0:
            raise ValidationError(_('Label is too large for page size'))

        # Prepend the required number of skipped null labels
        items = [None] * skip + list(items)

        n_labels = len(items)

        # Data to pass through to each page
        document_data = {
            'border': border,
            'landscape': landscape,
            'page_width': page_width,
            'page_height': page_height,
            'label_width': label.width,
            'label_height': label.height,
            'n_labels': n_labels,
            'n_pages': math.ceil(n_labels / n_cells),
            'n_cols': n_cols,
            'n_rows': n_rows,
            'margin': margin,
        }

        pages = []

        idx = 0

        while idx < n_labels:
            if page := self.print_page(
                label, items[idx : idx + n_cells], request, **document_data
            ):
                pages.append(page)

            idx += n_cells

            # Update printing progress
            output.progress += 1
            output.save()

        if len(pages) == 0:
            raise ValidationError(_('No labels were generated'))

        # Render to a single HTML document
        html_data = self.wrap_pages(pages, **document_data)

        if str2bool(self.get_setting('DEBUG')):
            # In debug mode return with the raw HTML
            output.output = ContentFile(html_data, 'labels.html')
        else:
            # Render HTML to PDF
            html = weasyprint.HTML(string=html_data)
            document = html.render().write_pdf()

            output.output = ContentFile(document, 'labels.pdf')

        output.progress = n_labels
        output.complete = True
        output.save()

    def print_page(self, label: LabelTemplate, items: list, request, **kwargs):
        """Generate a single page of labels.

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
                # Cell index
                idx = row * n_cols + col

                if idx >= len(items):
                    break

                html += f"<td class='label-sheet-cell label-sheet-row-{row} label-sheet-col-{col}'>"

                # If the label is empty (skipped), render an empty cell
                if items[idx] is None:
                    html += """<div class='label-sheet-cell-skip'></div>"""
                else:
                    try:
                        # Render the individual label template
                        # Note that we disable @page styling for this
                        cell = label.render_as_string(
                            items[idx], request, insert_page_style=False
                        )
                        html += cell
                    except Exception as exc:
                        logger.exception('Error rendering label: %s', str(exc))
                        html += """
                        <div class='label-sheet-cell-error'></div>
                        """

                html += '</td>'

            html += '</tr>'

        html += '</table>'

        return html

    def wrap_pages(self, pages, **kwargs):
        """Wrap the generated pages into a single document."""
        border = kwargs['border']

        page_width = kwargs['page_width']
        page_height = kwargs['page_height']

        label_width = kwargs['label_width']
        label_height = kwargs['label_height']

        n_rows = kwargs['n_rows']
        n_cols = kwargs['n_cols']

        margin = kwargs.get('margin', 0)

        inner = ''.join(pages)

        # Generate styles for individual cells (on each page)
        cell_styles = []

        for row in range(n_rows):
            cell_styles.append(
                f"""
            .label-sheet-row-{row} {{
                top: {row * label_height}mm;
            }}
            """
            )

        for col in range(n_cols):
            cell_styles.append(
                f"""
            .label-sheet-col-{col} {{
                left: {col * label_width}mm;
            }}
            """
            )

        cell_styles = '\n'.join(cell_styles)

        return f"""
        <head>
            <style>
                @page {{
                    size: {page_width}mm {page_height}mm;
                    margin: {margin}mm;
                    padding: 0mm;
                }}

                .label-sheet-table {{
                    page-break-after: always;
                    table-layout: fixed;
                    width: {page_width}mm;
                    border-spacing: 0mm 0mm;
                }}

                .label-sheet-cell-error {{
                    background-color: #F00;
                }}

                .label-sheet-cell {{
                    border: {'1px solid #000;' if border else '0mm;'}
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
