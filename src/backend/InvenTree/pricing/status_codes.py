"""Status codes for the 'pricing' app."""

from django.utils.translation import gettext_lazy as _

from generic.states import ColorEnum, StatusCode


class CostType(StatusCode):
    """Defines the type (source) of a StockItemCost entry.

    Attributes:
        PURCHASE: Cost taken directly from a purchase (e.g. supplier price break, PO line item)
        LANDED: Purchase cost plus additional landed costs (freight, duty, handling, etc)
        MANUFACTURING: Cost calculated from a build order (BOM cost plus labor / overhead)
        MANUAL: Cost manually entered (or overridden) by a user
        SYSTEM: Cost calculated automatically by the pricing system (e.g. a pricing plugin)
    """

    PURCHASE = 10, _('Purchase'), ColorEnum.primary
    LANDED = 20, _('Landed'), ColorEnum.info
    MANUFACTURING = 30, _('Manufacturing'), ColorEnum.secondary
    MANUAL = 40, _('Manual'), ColorEnum.warning
    SYSTEM = 50, _('System'), ColorEnum.success
