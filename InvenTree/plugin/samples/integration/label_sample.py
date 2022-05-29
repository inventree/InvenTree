"""Simple sample for a plugin with the LabelPrintingMixin.

This does not function in real usage and is more to show the required components and for unit tests.
"""

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
        """Sample printing step.

        Normally here the connection to the printer and transfer of the label would take place.
        """
        print("OK PRINTING")
