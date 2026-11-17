"""Status codes for the 'pricing' app."""

from django.utils.translation import gettext_lazy as _

from generic.states import ColorEnum, StatusCode


class CostType(StatusCode):
    """Defines the category of a StockItemCostEntry - i.e. *what* the cost is for.

    Note that the category does not describe who (or what) created the cost entry
    (see StockItemCostEntry.source). An estimated cost is recorded as a range (min_cost < max_cost).

    Attributes:
        PURCHASE: Unit price paid to the supplier
        LANDED: Additional cost of getting the item in stock (freight, duty, handling)
        FEES: Supplier or transaction fees
        MATERIAL: Cost of components consumed to manufacture the item (e.g. via a build order)
        MANUFACTURING: Manufacturing process cost (e.g. labor, overhead)
        ADJUSTMENT: Corrections, rebates and credits
        OTHER: Any other cost
    """

    PURCHASE = 10, _('Purchase'), ColorEnum.primary
    LANDED = 20, _('Landed'), ColorEnum.info
    FEES = 30, _('Fees'), ColorEnum.warning
    MATERIAL = 40, _('Material'), ColorEnum.success
    MANUFACTURING = 50, _('Manufacturing'), ColorEnum.dark
    ADJUSTMENT = 60, _('Adjustment'), ColorEnum.danger
    OTHER = 90, _('Other'), ColorEnum.secondary
