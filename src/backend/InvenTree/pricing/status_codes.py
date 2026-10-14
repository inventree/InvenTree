"""Status codes for the 'pricing' app."""

from django.utils.translation import gettext_lazy as _

from generic.states import ColorEnum, StatusCode


class CostType(StatusCode):
    """Defines the type (source) of a StockItemCost entry.

    Attributes:
        PURCHASE: Cost taken directly from a purchase (e.g. supplier price break, PO line item)
        LANDED: Purchase cost plus additional landed costs (freight, duty, handling, etc)
        MATERIAL: Cost calculated from a build order's consumed BOM components, from allocated stock which itself has a recorded cost
        MATERIAL_ESTIMATED: Cost calculated from a build order's consumed BOM components, from allocated stock with no recorded cost (estimated from the component part's price range instead)
        MANUFACTURING: Reserved for manufacturing *process* cost (e.g. labor, overhead) added during a build - distinct from MATERIAL, which is the cost of the components consumed. Not yet calculated anywhere.
        MANUAL: Cost manually entered (or overridden) by a user
        SYSTEM: Cost calculated automatically by the pricing system (e.g. a pricing plugin)
    """

    PURCHASE = 10, _('Purchase'), ColorEnum.primary
    LANDED = 20, _('Landed'), ColorEnum.info
    MATERIAL = 30, _('Material'), ColorEnum.secondary
    MATERIAL_ESTIMATED = 35, _('Material (Estimated)'), ColorEnum.dark
    MANUFACTURING = 37, _('Manufacturing'), ColorEnum.danger
    MANUAL = 40, _('Manual'), ColorEnum.warning
    SYSTEM = 50, _('System'), ColorEnum.success
