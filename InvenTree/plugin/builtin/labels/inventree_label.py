"""Default label printing plugin (supports PDF generation)"""

from django.http import HttpResponse
from django.utils.translation import gettext_lazy as _

import InvenTree.helpers
from common.models import InvenTreeUserSetting
from label.models import LabelTemplate
from plugin import InvenTreePlugin
from plugin.mixins import LabelPrintingMixin, SettingsMixin


class InvenTreeLabelPlugin(LabelPrintingMixin, SettingsMixin, InvenTreePlugin):
    """Builtin plugin for label printing"""

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

        for item in items:

            label.object_to_print = item

            outputs.append(self.print_label(label, request, debug=debug, **kwargs))

        if self.get_setting('DEBUG'):
            html = '\n'.join(outputs)
            return HttpResponse(html)
        else:
            pages = []

            # Following process is required to stitch labels together into a single PDF
            for output in outputs:
                doc = output.get_document()
                for page in doc.pages:
                    pages.append(page)

            pdf = outputs[0].get_document().copy(pages).write_pdf()
            inline = InvenTreeUserSetting.get_setting('LABEL_INLINE', user=request.user, cache=False)

            return InvenTree.helpers.DownloadFile(
                pdf,
                'labels.pdf',
                content_type='application/pdf',
                inline=inline
            )

    def print_label(self, label: LabelTemplate, request, **kwargs):
        """Handle printing of a single label.

        Returns either a PDF or HTML output, depending on the DEBUG setting.
        """

        debug = kwargs.get('debug', self.get_setting('DEBUG'))

        if debug:
            return self.render_to_html(label, request, **kwargs)
        else:
            return self.render_to_pdf(label, request, **kwargs)
