from __future__ import unicode_literals

from django.db import models

from part.models import Part
from InvenTree.models import InvenTreeTree

class Warehouse(InvenTreeTree):
    pass
    
class StockItem(models.Model):
    part = models.ForeignKey(Part,
                             on_delete=models.CASCADE)
    location = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    updated = models.DateField(auto_now=True)
    
    # Stock status types
    ITEM_IN_PROGRESS = 0
    ITEM_DAMAGED = 10
    ITEM_ATTENTION = 20
    ITEM_COMPLETE = 50
    
    status = models.IntegerField(default=ITEM_IN_PROGRESS,
                                 choices=[
                                 (ITEM_IN_PROGRESS, "In progress"),
                                 (ITEM_DAMAGED, "Damaged"),
                                 (ITEM_ATTENTION, "Requires attention"),
                                 (ITEM_COMPLETE, "Complete")
                                 ])
    
    def __str__(self):
        return "{n} x {part} @ {loc}".format(
            n = self.quantity,
            part = self.part.name,
            loc = self.location.name)