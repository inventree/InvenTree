from __future__ import unicode_literals

from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.contenttypes.models import ContentType

class InvenTreeTree(models.Model):
    """ Provides an abstracted self-referencing tree model for data categories.
    - Each Category has one parent Category, which can be blank (for a top-level Category).
    - Each Category can have zero-or-more child Categor(y/ies)
    """
    
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=250)
    parent = models.ForeignKey('self',
                               on_delete=models.CASCADE,
                               blank=True,
                               null=True)
                               #limit_choices_to={id: getAcceptableParents})
    
    def getUniqueChildren(self, unique=None):
        """ Return a flat set of all child items that exist under this node.
        If any child items are repeated, the repetitions are omitted.
        """
        
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
    
    def getAcceptableParents(self):
        """ Returns a list of acceptable parent items within this model
        Acceptable parents are ones which are not underneath this item.
        Setting the parent of an item to its own child results in recursion.
        """
        contents = ContentType.objects.get_for_model(type(self))
        
        available = contents.get_all_objects_for_this_type()
        
        # List of child IDs 
        childs = getUniqueChildren()
        
        acceptable = [None]
        
        for a in available:
            if a.id not in childs:
                acceptable.append(a)
                
        return acceptable
    
    @property
    def path(self):
        """ Return the parent path of this category
        
        Todo:
            This function is recursive and expensive.
            It should be reworked such that only a single db call is required
        """
        
        if self.parent:
            return self.parent.path + [self.parent]
        else:
            return []
        
        return parent_path
    
    def __setattr__(self, attrname, val):
        """ Custom Attribute Setting function
        
        Parent:
        Setting the parent of an item to its own child results in an infinite loop.
        The parent of an item cannot be set to:
            a) Its own ID
            b) The ID of any child items that exist underneath it
        
        Name:
        Tree node names are limited to a reduced character set
        """
        
        if attrname == 'parent_id':
            # If current ID is None, continue (as this object is just being created)
            if self.id is None:
                pass
            # Parent cannot be set to same ID (this would cause looping)
            elif val == self.id:
                return
            # Null parent is OK
            elif val is None:
                pass
            # Ensure that the new parent is not already a child 
            else:
                kids = self.getUniqueChildren()
                if val in kids:
                    return
                
        # Prohibit certain characters from tree node names
        elif attrname == 'name':
            val = val.translate({ord(c): None for c in "!@#$%^&*'\"\\/[]{}<>,|+=~`"})
                
        super(InvenTreeTree, self).__setattr__(attrname, val)
        
    def __str__(self):
        """ String representation of a category is the full path to that category
        
        Todo:
            This is recursive - Make it not so.
        """
        
        if self.parent:
            return "/".join([p.name for p in self.path]) + "/" + self.name
        else:
            return self.name
            
    
    class Meta:
        abstract = True