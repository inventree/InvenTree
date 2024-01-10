"""Default label printing plugin (supports PDF generation)."""

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

    NAME = 'InvenTreeLabel'
    TITLE = _('InvenTree PDF label printer')
    DESCRIPTION = _('Provides native support for printing PDF labels')
    VERSION = '1.0.0'
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

    def print_labels(self, label: LabelTemplate, items: list, request, **kwargs):
        """Handle printing of multiple labels.

        - Label outputs are concatenated together, and we return a single PDF file.
        - If DEBUG mode is enabled, we return a single HTML file.
        """
        debug = self.get_setting('DEBUG')

        outputs = []
        output_file = None

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
        output = LabelOutput.objects.create(label=output_file, user=request.user)

        return JsonResponse({
            'file': output.label.url,
            'success': True,
            'message': f'{len(items)} labels generated',
        })

    def print_label(self, label: LabelTemplate, request, **kwargs):
        """Handle printing of a single label.

        Returns either a PDF or HTML output, depending on the DEBUG setting.
        """
        debug = kwargs.get('debug', self.get_setting('DEBUG'))

        if debug:
            return self.render_to_html(label, request, **kwargs)

        return self.render_to_pdf(label, request, **kwargs)
