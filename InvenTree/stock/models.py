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
    
    def __str__(self):
        return "{n} x {part} @ {loc}".format(
            n = self.quantity,
            part = self.part.name,
            loc = self.location.name)