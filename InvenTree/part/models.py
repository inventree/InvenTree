from __future__ import unicode_literals

from django.db import models
from django.core.exceptions import ObjectDoesNotExist

class InvenTreeTree(models.Model):
    
    # Return a flat set of all child items under this node
    def getUniqueChildren(self, unique=None):
        
        if unique is None:
            unique = set()
        
        if self.id in unique:
            return unique
        
        unique.add(self.id)
            
        children = PartCategory.objects.filter(parent = self.id)
        
        for child in children:
            child.getUniqueChildren(unique)
            
        return unique
    
    # Return the parent path of this category
    @property
    def path(self):
        if self.parent:
            return self.parent.path + [self.parent]
        else:
            return []
        
        return parent_path
    
    # Custom SetAttribute function to prevent parent recursion
    def __setattr__(self, attrname, val):
        # Prevent parent from being set such that it would cause a recursion loop
        if attrname == 'parent_id':
            # Parent cannot be set to same ID (this would cause looping)
            if val == self.id:
                return
            # Null parent is OK
            elif val is None:
                pass
            # Ensure that the new parent is not already a child 
            else:
                kids = self.getUniqueChildren()
                if val in kids:
                    print("ALREADY A CHILD")
                    return
                
        super(InvenTreeTree, self).__setattr__(attrname, val)
    
    class Meta:
        abstract = True

class PartCategory(InvenTreeTree):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=250)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True)
    
    def __str__(self):
        if self.parent:
            return "/".join([p.name for p in self.path]) + "/" + self.name
        else:
            return self.name
        
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
        

        