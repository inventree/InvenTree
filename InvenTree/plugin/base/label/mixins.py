"""Plugin mixin classes for label plugins."""

from typing import Union

from django.http import JsonResponse

import pdf2image
from rest_framework import serializers
from rest_framework.request import Request

from common.models import InvenTreeSetting
from InvenTree.tasks import offload_task
from label.models import LabelTemplate
from plugin.base.label import label as plugin_label
from plugin.helpers import MixinNotImplementedError


class LabelPrintingMixin:
    """Mixin which enables direct printing of stock labels.

    Each plugin must provide a NAME attribute, which is used to uniquely identify the printer.

    The plugin *must* also implement the print_label() function for rendering an individual label

    Note that the print_labels() function can also be overridden to provide custom behavior.
    """

    # If True, the print_label() method will block until the label is printed
    # If False, the offload_label() method will be called instead
    # By default, this is False, which means that labels will be printed in the background
    BLOCKING_PRINT = False

    class MixinMeta:
        """Meta options for this mixin."""
        MIXIN_NAME = 'Label printing'

    def __init__(self):  # pragma: no cover
        """Register mixin."""
        super().__init__()
        self.add_mixin('labels', True, __class__)

    def render_to_pdf(self, label: LabelTemplate, request, **kwargs):
        """Render this label to PDF format

        Arguments:
            label: The LabelTemplate object to render
            request: The HTTP request object which triggered this print job
        """
        return label.render(request)

    def render_to_html(self, label: LabelTemplate, request, **kwargs):
        """Render this label to HTML format

        Arguments:
            label: The LabelTemplate object to render
            request: The HTTP request object which triggered this print job
        """
        return label.render_as_string(request)

    def render_to_png(self, label: LabelTemplate, request=None, **kwargs):
        """Render this label to PNG format"""
        # Check if pdf data is provided
        pdf_data = kwargs.get('pdf_data', None)

        if not pdf_data:
            pdf_data = self.render_to_pdf(label, request, **kwargs).get_document().write_pdf()

        dpi = kwargs.get(
            'dpi',
            InvenTreeSetting.get_setting('LABEL_DPI', 300)
        )

        # Convert to png data
        png = pdf2image.convert_from_bytes(pdf_data, dpi=dpi)[0]
        return png

    def print_labels(self, label: LabelTemplate, items: list, request: Request, printing_options: dict, **kwargs):
        """Print one or more labels with the provided template and items.

        Arguments:
            label: The LabelTemplate object to use for printing
            items: The list of database items to print (e.g. StockItem instances)
            request: The HTTP request object which triggered this print job

        Keyword Arguments:
            printing_options: The printing options set for this print job defined in the PrintingOptionsSerializer

        Returns:
            A JSONResponse object which indicates outcome to the user

        The default implementation simply calls print_label() for each label, producing multiple single label output "jobs"
        but this can be overridden by the particular plugin.
        """
        try:
            user = request.user
        except AttributeError:
            user = None

        # Generate a label output for each provided item
        for item in items:
            label.object_to_print = item
            filename = label.generate_filename(request)
            pdf_file = self.render_to_pdf(label, request, **kwargs)
            pdf_data = pdf_file.get_document().write_pdf()
            png_file = self.render_to_png(label, request, pdf_data=pdf_data, **kwargs)

            print_args = {
                'pdf_file': pdf_file,
                'pdf_data': pdf_data,
                'png_file': png_file,
                'filename': filename,
                'label_instance': label,
                'item_instance': item,
                'user': user,
                'width': label.width,
                'height': label.height,
                'printing_options': printing_options,
            }

            if self.BLOCKING_PRINT:
                # Blocking print job
                self.print_label(**print_args)
            else:
                # Non-blocking print job

                # Offload the print job to a background worker
                self.offload_label(**print_args)

        # Return a JSON response to the user
        return JsonResponse({
            'success': True,
            'message': f'{len(items)} labels printed',
        })

    def print_label(self, **kwargs):
        """Print a single label (blocking)

        kwargs:
            pdf_file: The PDF file object of the rendered label (WeasyTemplateResponse object)
            pdf_data: Raw PDF data of the rendered label
            filename: The filename of this PDF label
            label_instance: The instance of the label model which triggered the print_label() method
            item_instance: The instance of the database model against which the label is printed
            user: The user who triggered this print job
            width: The expected width of the label (in mm)
            height: The expected height of the label (in mm)
            printing_options: The printing options set for this print job defined in the PrintingOptionsSerializer

        Note that the supplied kwargs may be different if the plugin overrides the print_labels() method.
        """
        # Unimplemented (to be implemented by the particular plugin class)
        raise MixinNotImplementedError('This Plugin must implement a `print_label` method')

    def offload_label(self, **kwargs):
        """Offload a single label (non-blocking)

        Instead of immediately printing the label (which is a blocking process),
        this method should offload the label to a background worker process.

        Offloads a call to the 'print_label' method (of this plugin) to a background worker.
        """
        # Exclude the 'pdf_file' object - cannot be pickled
        kwargs.pop('pdf_file', None)

        offload_task(
            plugin_label.print_label,
            self.plugin_slug(),
            **kwargs
        )

    def get_printing_options_serializer(self, request: Request, *args, **kwargs) -> Union[serializers.Serializer, None]:
        """Return a serializer class instance with dynamic printing options.

        Arguments:
            request: The request made to print a label or interfering the available serializer fields via an OPTIONS request
            *args, **kwargs: need to be passed to the serializer instance

        Returns:
            A class instance of a DRF serializer class, by default this an instance of
            self.PrintingOptionsSerializer using the *args, **kwargs if existing for this plugin
        """
        serializer = getattr(self, "PrintingOptionsSerializer", None)

        if not serializer:
            return None

        return serializer(*args, **kwargs)
