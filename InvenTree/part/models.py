from __future__ import unicode_literals

from django.db import models
from django.core.exceptions import ObjectDoesNotExist

from InvenTree.models import InvenTreeTree

class PartCategory(InvenTreeTree):    
    def __str__(self):
        if self.parent:
            return "/".join([p.name for p in self.path]) + "/" + self.name
        else:
            return self.name
        
    class Meta:
        verbose_name = "Part Category"
        verbose_name_plural = "Part Categories"
        
class Part(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=250, blank=True)
    IPN = models.CharField(max_length=100, blank=True)
    category = models.ForeignKey(PartCategory, on_delete=models.CASCADE)
    
    def __str__(self):
        if self.IPN:
            return "{name} ({ipn})".format(
                ipn = self.IPN,
                name = self.name)
        else:
            return self.name
        
    class Meta:
        verbose_name = "Part"
        verbose_name_plural = "Parts"

        