"""Django Forms for interacting with Stock app."""

from InvenTree.forms import HelperForm

from .models import StockItem


class ConvertStockItemForm(HelperForm):
    """Form for converting a StockItem to a variant of its current part.

    TODO: Migrate this form to the modern API forms interface
    """

    class Meta:
        """Metaclass options."""

        model = StockItem
        fields = [
            'part'
        ]
