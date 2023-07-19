"""Default label printing plugin (supports PDF generation)"""

import math

from django.core.files.base import ContentFile
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _

from label.models import LabelOutput, LabelTemplate
from plugin import InvenTreePlugin
from plugin.mixins import LabelPrintingMixin, SettingsMixin


class InvenTreeLabelPlugin(LabelPrintingMixin, SettingsMixin, InvenTreePlugin):
    """Builtin plugin for label printing.

    This plugin merges the selected labels into a single PDF file,
    which is made available for download.
    """

    NAME = "InvenTreeLabel"
    TITLE = _("InvenTree PDF label printer")
    DESCRIPTION = _("Provides native support for printing PDF labels")
    VERSION = "1.0.0"
    AUTHOR = _("InvenTree contributors")

    BLOCKING_PRINT = True

    SETTINGS = {
        'DEBUG': {
            'name': _('Debug mode'),
            'description': _('Enable debug mode - returns raw HTML instead of PDF'),
            'validator': bool,
            'default': False,
        },
    }

    def print_labels(self, label: LabelTemplate, items: list, request, **kwargs):
        """Handle printing of multiple labels

        - Label outputs are concatenated together, and we return a single PDF file.
        - If DEBUG mode is enabled, we return a single HTML file.
        """

        debug = self.get_setting('DEBUG')

        outputs = []
        output_file = None

        if label.multipage:
            outputs = self.print_paginated(label, request, items, debug)
        else:
            for item in items:

                label.object_to_print = item

                outputs.append(self.print_label(label, request, debug=debug, **kwargs))

        if self.get_setting('DEBUG'):
            html = '\n'.join(outputs)

            output_file = ContentFile(html, 'labels.html')
        else:
            pages = []

            # Following process is required to stitch labels together into a single PDF
            for output in outputs:
                doc = output.get_document()

                for page in doc.pages:
                    pages.append(page)

            pdf = outputs[0].get_document().copy(pages).write_pdf()

            # Create label output file
            output_file = ContentFile(pdf, 'labels.pdf')

        # Save the generated file to the database
        output = LabelOutput.objects.create(
            label=output_file,
            user=request.user
        )

        return JsonResponse({
            'file': output.label.url,
            'success': True,
            'message': f'{len(items)} labels generated'
        })

    def print_label(self, label: LabelTemplate, request, **kwargs):
        """Handle printing of a single label.

        Returns either a PDF or HTML output, depending on the DEBUG setting.
        """

        debug = kwargs.get('debug', self.get_setting('DEBUG'))

        if debug:
            return self.render_to_html(label, request, **kwargs)
        else:
            return self.render_to_pdf(label, request, **kwargs)

    def print_paginated(self, label: LabelTemplate, request, items, debug):
        """Paginate the labels to pages depending on th label/page geometry ratio"""

        col_count = math.floor(label.page_width / label.width)
        row_count = math.floor(label.page_height / label.height)

        main_tables = '<table class="main-table"><tr class="main-table-row">'

        col_counter = 0
        row_counter = 0
        item_counter = 0

        outputs = []

        for item in items:
            label.object_to_print = item

            main_tables += '<td class="main-table-cell">' + self.print_label(label, request, debug=True) + '</td>'

            col_counter = col_counter + 1
            if col_counter >= col_count:
                col_counter = 0
                main_tables += "</tr>"

                row_counter = row_counter + 1
                if row_counter >= row_count:
                    row_counter = 0
                    main_tables += "</table>"
                    if item_counter < len(items) - 1:
                        main_tables += '<table class="main-table"><tr class="main-table-row">'
                else:
                    if item_counter < len(items) - 1:
                        main_tables += '<tr class="main-table-row">'
            item_counter = item_counter + 1

        if debug:
            outputs.append(label.render_paginated_to_string(request, main_tables))
        else:
            outputs.append(label.render_paginated(request, main_tables))

        return outputs
