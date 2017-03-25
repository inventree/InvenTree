from __future__ import unicode_literals

from django.db import models

class PartCategory(models.Model):
    name = models.CharField(max_length=128)
    description = models.CharField(max_length=512)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True)
    
    def __str__(self):
        if self.parent:
            return str(self.parent) + "/" + self.name
        else:
            return self.name