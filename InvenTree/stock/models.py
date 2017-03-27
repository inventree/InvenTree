from __future__ import unicode_literals

from django.db import models

from part.models import Part

class Warehouse(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=250, blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True)
    
    def __str__(self):
        if self.parent:
            return "/".join([p.name for p in self.path]) + "/" + self.name
        else:
            return self.name
    
    # Return path of this category
    @property
    def path(self):
        if self.parent:
            return self.parent.path + [self.parent]
        else:
            return []
    
class StockItem(models.Model):
    part = models.ForeignKey(Part, on_delete=models.CASCADE)
    location = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    updated = models.DateField(auto_now=True)
    
    def __str__(self):
        return "{n} x {part} @ {loc}".format(
            n = self.quantity,
            part = self.part.name,
            loc = self.location.name)