"""Default label printing plugin (supports PDF generation)."""

from django.utils.translation import gettext_lazy as _

from InvenTree.helpers import DownloadFile
from plugin import InvenTreePlugin
from plugin.mixins import LabelPrintingMixin, SettingsMixin
from report.models import LabelTemplate


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

        # TODO: Generate filename based on the first label
        filename = 'labels.pdf'

        for item in items:
            outputs.append(
                self.print_label(label, item, request, debug=debug, **kwargs)
            )

        if self.get_setting('DEBUG'):
            data = '\n'.join(outputs)
            filename = 'labels.html'
        else:
            pages = []

            # Following process is required to stitch labels together into a single PDF
            for output in outputs:
                print('output:', output)
                print('template:', label.template)
                doc = output.get_document()

                for page in doc.pages:
                    pages.append(page)

            data = outputs[0].get_document().copy(pages).write_pdf()

        return DownloadFile(data, filename)

    def print_label(self, label: LabelTemplate, instance, request, **kwargs):
        """Handle printing of a single label.

        Returns either a PDF or HTML output, depending on the DEBUG setting.
        """
        debug = kwargs.get('debug', self.get_setting('DEBUG'))

        if debug:
            return self.render_to_html(label, instance, request, **kwargs)

        return self.render_to_pdf(label, instance, request, **kwargs)
