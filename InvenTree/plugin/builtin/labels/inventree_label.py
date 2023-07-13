"""Default label printing plugin (supports PDF generation)"""

from django.utils.translation import gettext_lazy as _

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

    SETTINGS = {
        'DEBUG': {
            'name': _('Debug mode'),
            'description': _('Enable debug mode - returns raw HTML instead of PDF'),
            'validator': bool,
            'default': False,
        },
    }

    def print_labels(self, labels: list[LabelTemplate], request, **kwargs):
        """Handle printing of multiple labels"""
        return super().print_labels(labels, request, **kwargs)

    def print_label(self, label: LabelTemplate, request, **kwargs):
        """Handle printing of a single label"""
        return super().print_label(label, request, **kwargs)
