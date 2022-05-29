
from plugin import InvenTreePlugin
from plugin.mixins import LabelPrintingMixin


class SampleLabelPrinter(LabelPrintingMixin, InvenTreePlugin):
    """
    Sample plugin which provides a 'fake' label printer endpoint
    """

    NAME = "Label Printer"
    SLUG = "samplelabel"
    TITLE = "Sample Label Printer"
    DESCRIPTION = "A sample plugin which provides a (fake) label printer interface"
    VERSION = "0.2"

    def print_label(self, **kwargs):

        # Test that the expected kwargs are present
        print(f"Printing Label: {kwargs['filename']} (User: {kwargs['user']})")
        print(f"Width: {kwargs['width']} x Height: {kwargs['height']}")

        pdf_data = kwargs['pdf_data']
        png_file = kwargs['png_file']

        filename = kwargs['filename']

        # Dump the PDF to a local file
        with open(filename, 'wb') as pdf_out:
            pdf_out.write(pdf_data)

        # Save the PNG to disk
        png_file.save(filename.replace('.pdf', '.png'))
