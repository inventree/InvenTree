"""Default label printing plugin (supports PDF generation)"""

from django.utils.translation import gettext_lazy as _

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

    def print_label(self, **kwargs):
        """Handle printing of a single label."""
        ...
