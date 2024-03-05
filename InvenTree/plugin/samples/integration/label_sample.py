"""Simple sample for a plugin with the LabelPrintingMixin.

This does not function in real usage and is more to show the required components and for unit tests.
"""

from rest_framework import serializers

from InvenTree.settings import BASE_DIR
from plugin import InvenTreePlugin
from plugin.mixins import LabelPrintingMixin


class SampleLabelPrinter(LabelPrintingMixin, InvenTreePlugin):
    """Sample plugin which provides a 'fake' label printer endpoint."""

    NAME = 'Sample Label Printer'
    SLUG = 'samplelabelprinter'
    TITLE = 'Sample Label Printer'
    DESCRIPTION = 'A sample plugin which provides a (fake) label printer interface'
    AUTHOR = 'InvenTree contributors'
    VERSION = '0.3.0'

    class PrintingOptionsSerializer(serializers.Serializer):
        """Serializer to return printing options."""

        amount = serializers.IntegerField(required=False, default=1)

    def print_label(self, **kwargs):
        """Sample printing step.

        Normally here the connection to the printer and transfer of the label would take place.
        """
        # Test that the expected kwargs are present
        print(f"Printing Label: {kwargs['filename']} (User: {kwargs['user']})")

        pdf_data = kwargs['pdf_data']
        png_file = self.render_to_png(label=None, pdf_data=pdf_data)

        filename = str(BASE_DIR / '_testfolder' / 'label.pdf')

        # Dump the PDF to a local file
        with open(filename, 'wb') as pdf_out:
            pdf_out.write(pdf_data)

        # Save the PNG to disk
        png_file.save(filename.replace('.pdf', '.png'))
