"""Plugin mixin classes for label plugins."""

from typing import Union

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

import pdf2image
from rest_framework import serializers
from rest_framework.request import Request

from common.models import InvenTreeSetting
from InvenTree.exceptions import log_error
from InvenTree.tasks import offload_task
from plugin.base.label import label as plugin_label
from plugin.helpers import MixinNotImplementedError
from report.models import LabelTemplate, TemplateOutput


class LabelPrintingMixin:
    """Mixin which enables direct printing of stock labels.

    Each plugin must provide a NAME attribute, which is used to uniquely identify the printer.

    The plugin *must* also implement the print_label() function for rendering an individual label

    Note that the print_labels() function can also be overridden to provide custom behavior.
    """

    class MixinMeta:
        """Meta options for this mixin."""

        MIXIN_NAME = 'Label printing'

    def __init__(self):  # pragma: no cover
        """Register mixin."""
        super().__init__()
        self.add_mixin('labels', True, __class__)

    BLOCKING_PRINT = True

    def render_to_pdf(self, label: LabelTemplate, instance, request, **kwargs):
        """Render this label to PDF format.

        Arguments:
            label: The LabelTemplate object to render against
            instance: The model instance to render
            request: The HTTP request object which triggered this print job
        """
        try:
            return label.render(instance, request)
        except Exception:
            log_error('label.render_to_pdf')
            raise ValidationError(_('Error rendering label to PDF'))

    def render_to_html(self, label: LabelTemplate, instance, request, **kwargs):
        """Render this label to HTML format.

        Arguments:
            label: The LabelTemplate object to render against
            instance: The model instance to render
            request: The HTTP request object which triggered this print job
        """
        try:
            return label.render_as_string(instance, request)
        except Exception:
            log_error('label.render_to_html')
            raise ValidationError(_('Error rendering label to HTML'))

    def render_to_png(self, label: LabelTemplate, instance, request=None, **kwargs):
        """Render this label to PNG format.

        Arguments:
            label: The LabelTemplate object to render against
            item: The model instance to render
            request: The HTTP request object which triggered this print job
        Keyword Arguments:
            pdf_data: The raw PDF data of the rendered label (if already rendered)
            dpi: The DPI to use for the PNG rendering
            use_cairo (bool): Whether to use the pdftocairo backend for rendering which provides better results in tests,
                see [#6488](https://github.com/inventree/InvenTree/pull/6488) for details. If False, pdftoppm is used (default: True)
            pdf2image_kwargs (dict): Additional keyword arguments to pass to the
                [`pdf2image.convert_from_bytes`](https://pdf2image.readthedocs.io/en/latest/reference.html#pdf2image.pdf2image.convert_from_bytes) method (optional)
        """
        # Check if pdf data is provided
        pdf_data = kwargs.get('pdf_data', None)

        if not pdf_data:
            pdf_data = (
                self.render_to_pdf(label, instance, request, **kwargs)
                .get_document()
                .write_pdf()
            )

        pdf2image_kwargs = {
            'dpi': kwargs.get('dpi', InvenTreeSetting.get_setting('LABEL_DPI', 300)),
            'use_pdftocairo': kwargs.get('use_cairo', True),
            **kwargs.get('pdf2image_kwargs', {}),
        }

        # Convert to png data
        try:
            return pdf2image.convert_from_bytes(pdf_data, **pdf2image_kwargs)[0]
        except Exception:
            log_error('label.render_to_png')
            return None

    def print_labels(
        self,
        label: LabelTemplate,
        output: TemplateOutput,
        items: list,
        request: Request,
        **kwargs,
    ) -> None:
        """Print one or more labels with the provided template and items.

        Arguments:
            label: The LabelTemplate object to use for printing
            output: The TemplateOutput object used to store the results
            items: The list of database items to print (e.g. StockItem instances)
            request: The HTTP request object which triggered this print job

        Keyword Arguments:
            printing_options: The printing options set for this print job defined in the PrintingOptionsSerializer

        Returns:
            None. Output data should be stored in the provided TemplateOutput object

        Raises:
            ValidationError if there is an error during the print process

        The default implementation simply calls print_label() for each label, producing multiple single label output "jobs"
        but this can be overridden by the particular plugin.
        """
        try:
            user = request.user
        except AttributeError:
            user = None

        # Initial state for the output print job
        output.progress = 0
        output.complete = False
        output.save()

        N = len(items)

        if N <= 0:
            raise ValidationError(_('No items provided to print'))

        # Generate a label output for each provided item
        for item in items:
            context = label.get_context(item, request)
            filename = label.generate_filename(context)
            pdf_file = self.render_to_pdf(label, item, request, **kwargs)
            pdf_data = pdf_file.get_document().write_pdf()
            png_file = self.render_to_png(
                label, item, request, pdf_data=pdf_data, **kwargs
            )

            print_args = {
                'pdf_file': pdf_file,
                'pdf_data': pdf_data,
                'png_file': png_file,
                'filename': filename,
                'context': context,
                'output': output,
                'label_instance': label,
                'item_instance': item,
                'user': user,
                'width': label.width,
                'height': label.height,
                'printing_options': kwargs['printing_options'],
            }

            if self.BLOCKING_PRINT:
                # Print the label (blocking)
                self.print_label(**print_args)
            else:
                # Offload the print task to the background worker

                # Exclude the 'pdf_file' object - cannot be pickled
                print_args.pop('pdf_file', None)

                # Exclude the 'context' object - cannot be pickled
                print_args.pop('context', None)

                offload_task(plugin_label.print_label, self.plugin_slug(), **print_args)

            # Update the progress of the print job
            output.progress += int(100 / N)
            output.save()

        # Mark the output as complete
        output.complete = True
        output.progress = 100

        # Add in the generated file (if applicable)
        output.output = self.get_generated_file(**print_args)

        output.save()

    def get_generated_file(self, **kwargs):
        """Return the generated file for download (or None, if this plugin does not generate a file output).

        The default implementation returns None, but this can be overridden by the particular plugin.
        """
        return None

    def print_label(self, **kwargs):
        """Print a single label (blocking).

        kwargs:
            pdf_file: The PDF file object of the rendered label (WeasyTemplateResponse object)
            pdf_data: Raw PDF data of the rendered label
            filename: The filename of this PDF label
            label_instance: The instance of the label model which triggered the print_label() method
            item_instance: The instance of the database model against which the label is printed
            output: The TemplateOutput object used to store the results of the print job
            user: The user who triggered this print job
            width: The expected width of the label (in mm)
            height: The expected height of the label (in mm)
            printing_options: The printing options set for this print job defined in the PrintingOptionsSerializer

        Note that the supplied kwargs may be different if the plugin overrides the print_labels() method.
        """
        # Unimplemented (to be implemented by the particular plugin class)
        raise MixinNotImplementedError(
            'This Plugin must implement a `print_label` method'
        )

    def get_printing_options_serializer(
        self, request: Request, *args, **kwargs
    ) -> Union[serializers.Serializer, None]:
        """Return a serializer class instance with dynamic printing options.

        Arguments:
            request: The request made to print a label or interfering the available serializer fields via an OPTIONS request
            *args, **kwargs: need to be passed to the serializer instance

        Returns:
            A class instance of a DRF serializer class, by default this an instance of
            self.PrintingOptionsSerializer using the *args, **kwargs if existing for this plugin
        """
        serializer = getattr(self, 'PrintingOptionsSerializer', None)

        if not serializer:
            return None

        return serializer(*args, **kwargs)

    def before_printing(self):
        """Hook method called before printing labels."""

    def after_printing(self):
        """Hook method called after printing labels."""
