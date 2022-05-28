
from plugin import InvenTreePlugin
from plugin.mixins import LabelPrintingMixin


class SampleLabelPrinter(LabelPrintingMixin, InvenTreePlugin):
    """Sample plugin which provides a 'fake' label printer endpoint."""

    NAME = "Label Printer"
    SLUG = "samplelabel"
    TITLE = "Sample Label Printer"
    DESCRIPTION = "A sample plugin which provides a (fake) label printer interface"
    VERSION = "0.1"

    def print_label(self, label, **kwargs):
        print("OK PRINTING")
