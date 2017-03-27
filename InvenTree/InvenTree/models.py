from __future__ import unicode_literals

from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.contenttypes.models import ContentType

class InvenTreeTree(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=250)
    parent = models.ForeignKey('self',
                               on_delete=models.CASCADE,
                               blank=True,
                               null=True)
                               #limit_choices_to={id: getAcceptableParents})
    
    # Return a flat set of all child items under this node
    def getUniqueChildren(self, unique=None):
        
        if unique is None:
            unique = set()
        
        if self.id in unique:
            return unique
        
        unique.add(self.id)
            
        # Some magic to get around the limitations of abstract models
        contents = ContentType.objects.get_for_model(type(self))
        children = contents.get_all_objects_for_this_type(parent = self.id)
        
        for child in children:
            child.getUniqueChildren(unique)
            
        return unique
    
    # Return a list of acceptable other parents
    def getAcceptableParents(self):
        contents = ContentType.objects.get_for_model(type(self))
        
        available = contents.get_all_objects_for_this_type()
        
        # List of child IDs 
        childs = getUniqueChildren()
        
        acceptable = [None]
        
        for a in available:
            if a.id not in childs:
                acceptable.append(a)
                
        return acceptable
    
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