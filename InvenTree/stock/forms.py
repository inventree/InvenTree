"""Django Forms for interacting with Stock app."""

from InvenTree.forms import HelperForm

from .models import StockItem, StockItemTracking


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


class TrackingEntryForm(HelperForm):
    """Form for creating / editing a StockItemTracking object.

    Note: 2021-05-11 - This form is not currently used - should delete?
    """

    class Meta:
        """Metaclass options."""

        model = StockItemTracking

        fields = [
            'notes',
        ]
