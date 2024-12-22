"""Default label printing plugin (supports PDF generation)."""

from django.core.files.base import ContentFile
from django.utils.translation import gettext_lazy as _

from InvenTree.helpers import str2bool
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
    VERSION = '1.1.0'
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

    # Keep track of individual label outputs
    # These will be stitched together at the end of printing
    outputs = []

    def before_printing(self):
        """Reset the list of label outputs."""
        self.outputs = []

    def print_label(self, **kwargs):
        """Print a single label."""
        label = kwargs['label_instance']
        instance = kwargs['item_instance']

        if str2bool(self.get_setting('DEBUG')):
            # In debug mode, return raw HTML output
            output = self.render_to_html(label, instance, None, **kwargs)
        else:
            # Output is already provided
            output = kwargs['pdf_file']

        self.outputs.append(output)

    def get_generated_file(self, **kwargs):
        """Return the generated file, by stitching together the individual label outputs."""
        if len(self.outputs) == 0:
            return None

        if str2bool(self.get_setting('DEBUG')):
            # Simple HTML output
            data = '\n'.join(self.outputs)
            filename = 'labels.html'
        else:
            # Stitch together the PDF outputs
            pages = []

            for output in self.outputs:
                doc = output.get_document()

                for page in doc.pages:
                    pages.append(page)

            data = self.outputs[0].get_document().copy(pages).write_pdf()
            filename = kwargs.get('filename', 'labels.pdf')

        return ContentFile(data, name=filename)
