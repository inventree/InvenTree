"""Plugin mixin classes for label plugins."""

from django.http import JsonResponse

from label.models import LabelTemplate
from plugin.helpers import MixinNotImplementedError


class LabelPrintingMixin:
    """Mixin which enables direct printing of stock labels.

    Each plugin must provide a NAME attribute, which is used to uniquely identify the printer.

    The plugin must also implement the print_label() function
    """

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

    def print_labels(self, labels: list[LabelTemplate], request, **kwargs):
        """Print one or more labels.

        Arguments:
            labels: A list of LabelTemplate objects to print
            request: The HTTP request object which triggered this print job

        kwargs:
            user: The user who triggered this print job
            copies: The number of copies to print

        The default implementation simply calls print_label() for each label,
        producing multiple single label output "jobs"
        but this can be overridden by the particular plugin.
        """

        for label in labels:
            self.print_label(label, request, **kwargs)

        return JsonResponse({
            'plugin': self.plugin_slug(),
            'success': True,
            'message': f'{len(labels)} labels printed',
        })

    def print_label(self, label: LabelTemplate, request, **kwargs):
        """Callback to print a single label.

        Arguments:
            label: The LabelTemplate object to print
            request: The HTTP request object which triggered this print job

        kwargs:
            pdf_data: Raw PDF data of the rendered label
            png_file: An in-memory PIL image file, rendered at 300dpi
            label_instance: The instance of the label model which triggered the print_label() method
            width: The expected width of the label (in mm)
            height: The expected height of the label (in mm)
            filename: The filename of this PDF label
            user: The user who printed this label
        """
        # Unimplemented (to be implemented by the particular plugin class)
        raise MixinNotImplementedError('This Plugin must implement a `print_label` method')
