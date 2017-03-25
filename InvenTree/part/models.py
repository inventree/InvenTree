from __future__ import unicode_literals

from django.db import models

class PartCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=250)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True)
    
    def __str__(self):
        if self.parent:
            return "/".join([p.name for p in self.path]) + "/" + self.name
        else:
            return self.name
        
    # Return the parent path of this category
    @property
    def path(self):
        parent_path = []
        
        if self.parent:
            parent_path = self.parent.path + [self.parent]
        
        return parent_path
        
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
        

        