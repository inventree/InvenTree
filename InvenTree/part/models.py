from __future__ import unicode_literals

from django.db import models
from django.db.models import Sum
from django.core.exceptions import ObjectDoesNotExist

from InvenTree.models import InvenTreeTree


class PartCategory(InvenTreeTree):    
    """ PartCategory provides hierarchical organization of Part objects.
    """
    
    
    class Meta:
        verbose_name = "Part Category"
        verbose_name_plural = "Part Categories"
        
        
class Part(models.Model):
    """ Represents a """
    
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=250, blank=True)
    IPN = models.CharField(max_length=100, blank=True)
    category = models.ForeignKey(PartCategory, on_delete=models.CASCADE)
    minimum_stock = models.IntegerField(default=0)
    units = models.CharField(max_length=20, default="pcs", blank=True)
    trackable = models.BooleanField(default=False)
    
    
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
        
        
    @property
    def stock_list(self):
        """ Return a list of all stock objects associated with this part
        """
        
        return self.stockitem_set.all()
        
        
    @property
    def stock(self):
        """ Return the total stock quantity for this part.
        Part may be stored in multiple locations
        """
        
        stocks = self.stock_list
        if len(stocks) == 0:
            return 0
            
        result = stocks.aggregate(total=Sum('quantity'))
        return result['total']
        
        
    @property
    def projects(self):
        """ Return a list of unique projects that this part is associated with
        """
        
        project_ids = set()
        project_parts = self.projectpart_set.all()
        
        projects = []
        
        for pp in project_parts:
            if pp.project.id not in project_ids:
                project_ids.add(pp.project.id)
                projects.append(pp.project)
                
        return projects

        
class PartRevision(models.Model):
    """ A PartRevision represents a change-notification to a Part
    A Part may go through several revisions in its lifetime,
    which should be tracked.
    UniqueParts can have a single associated PartRevision
    """
    
    part = models.ForeignKey(Part, on_delete=models.CASCADE)
    
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=500)
    revision_date = models.DateField(auto_now_add = True)
    
    
    def __str__(self):
        return self.name