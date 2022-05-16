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

    def print_label(self, label, **kwargs):
        """
        Callback to print a single label

        Arguments:
            label: A black-and-white pillow Image object

        kwargs:
            length: The length of the label (in mm)
            width: The width of the label (in mm)

        """

        # Unimplemented (to be implemented by the particular plugin class)
        raise MixinNotImplementedError('This Plugin must implement a `print_label` method')
