"""Plugin mixin classes for label plugins"""

from plugin.helpers import MixinNotImplementedError


class LabelPrintingMixin:
    """
    Mixin which enables direct printing of stock labels.

    Each plugin must provide a NAME attribute, which is used to uniquely identify the printer.

    The plugin must also implement the print_label() function
    """

    class MixinMeta:
        """
        Meta options for this mixin
        """
        MIXIN_NAME = 'Label printing'

    def __init__(self):  # pragma: no cover
        super().__init__()
        self.add_mixin('labels', True, __class__)

    def print_label(self, **kwargs):
        """
        Callback to print a single label

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
