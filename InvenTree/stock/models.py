from __future__ import unicode_literals
from django.utils.translation import ugettext as _
from django.db import models

from part.models import Part
from InvenTree.models import InvenTreeTree


class Warehouse(InvenTreeTree):
    pass


class StockItem(models.Model):
    part = models.ForeignKey(Part,
                             on_delete=models.CASCADE,
                             related_name='locations')
    location = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    updated = models.DateField(auto_now=True)

    # last time the stock was checked / counted
    last_checked = models.DateField(blank=True, null=True)

    review_needed = models.BooleanField(default=False)

    # Stock status types
    ITEM_IN_STOCK = 10
    ITEM_INCOMING = 15
    ITEM_IN_PROGRESS = 20
    ITEM_COMPLETE = 25
    ITEM_ATTENTION = 50
    ITEM_DAMAGED = 55
    ITEM_DESTROYED = 60

    ITEM_STATUS_CODES = {
        ITEM_IN_STOCK: _("In stock"),
        ITEM_INCOMING: _("Incoming"),
        ITEM_IN_PROGRESS: _("In progress"),
        ITEM_COMPLETE: _("Complete"),
        ITEM_ATTENTION: _("Attention needed"),
        ITEM_DAMAGED: _("Damaged"),
        ITEM_DESTROYED: _("Destroyed")
    }

    status = models.PositiveIntegerField(
        default=ITEM_IN_STOCK,
        choices=ITEM_STATUS_CODES.items())

    # If stock item is incoming, an (optional) ETA field
    expected_arrival = models.DateField(null=True, blank=True)

    def __str__(self):
        return "{n} x {part} @ {loc}".format(
            n=self.quantity,
            part=self.part.name,
            loc=self.location.name)
