from __future__ import unicode_literals

from django.db import models
from django.contrib.contenttypes.models import ContentType
from rest_framework.exceptions import ValidationError


class Company(models.Model):
    """ Abstract model representing an external company
    """

    class Meta:
        abstract = True

    name = models.CharField(max_length=100, unique=True)
    website = models.URLField(blank=True)
    address = models.CharField(max_length=200,
                               blank=True)
    phone = models.CharField(max_length=50,
                             blank=True)
    email = models.EmailField(blank=True)
    contact = models.CharField(max_length=100,
                               blank=True)
    notes = models.CharField(max_length=500,
                             blank=True)

    def __str__(self):
        return self.name


class InvenTreeTree(models.Model):
    """ Provides an abstracted self-referencing tree model for data categories.
    - Each Category has one parent Category, which can be blank (for a top-level Category).
    - Each Category can have zero-or-more child Categor(y/ies)
    """

    class Meta:
        abstract = True
        unique_together = ('name', 'parent')

    name = models.CharField(max_length=100)
    description = models.CharField(max_length=250, blank=True)
    parent = models.ForeignKey('self',
                               on_delete=models.CASCADE,
                               blank=True,
                               null=True,
                               related_name='children')

    def getUniqueParents(self, unique=None):
        """ Return a flat set of all parent items that exist above this node.
        If any parents are repeated (which would be very bad!), the process is halted
        """

        if unique is None:
            unique = set()
        else:
            unique.add(self.id)

        if self.parent and self.parent.id not in unique:
            self.parent.getUniqueParents(unique)

        return unique

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
        children = contents.get_all_objects_for_this_type(parent=self.id)

        for child in children:
            child.getUniqueChildren(unique)

        return unique

    @property
    def children(self):
        contents = ContentType.objects.get_for_model(type(self))
        children = contents.get_all_objects_for_this_type(parent=self.id)

        return children

    def getAcceptableParents(self):
        """ Returns a list of acceptable parent items within this model
        Acceptable parents are ones which are not underneath this item.
        Setting the parent of an item to its own child results in recursion.
        """
        contents = ContentType.objects.get_for_model(type(self))

        available = contents.get_all_objects_for_this_type()

        # List of child IDs
        childs = self.getUniqueChildren()

        acceptable = [None]

        for a in available:
            if a.id not in childs:
                acceptable.append(a)

        return acceptable

    @property
    def parentpath(self):
        """ Return the parent path of this category

        Todo:
            This function is recursive and expensive.
            It should be reworked such that only a single db call is required
        """

        if self.parent:
            return self.parent.parentpath + [self.parent]
        else:
            return []

    @property
    def path(self):
        if self.parent:
            return "/".join([p.name for p in self.parentpath]) + "/" + self.name
        else:
            return self.name

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
            # If current ID is None, continue
            # - This object is just being created
            if self.id is None:
                pass
            # Parent cannot be set to same ID (this would cause looping)
            elif val == self.id:
                raise ValidationError("Category cannot set itself as parent")
            # Null parent is OK
            elif val is None:
                pass
            # Ensure that the new parent is not already a child
            else:
                kids = self.getUniqueChildren()
                if val in kids:
                    raise ValidationError("Category cannot set a child as parent")

        # Prohibit certain characters from tree node names
        elif attrname == 'name':
            val = val.translate({ord(c): None for c in "!@#$%^&*'\"\\/[]{}<>,|+=~`"})

        super(InvenTreeTree, self).__setattr__(attrname, val)

    def __str__(self):
        """ String representation of a category is the full path to that category

        Todo:
            This is recursive - Make it not so.
        """

        return self.path


def FilterChildren(queryset, parent):
    """ Filter a queryset, limit to only objects that are a child of the given parent
    Filter is passed in the URL string, e.g. '/?parent=123'
    To accommodate for items without a parent, top-level items can be specified as:
    none / false / null / top / 0
    """

    if not parent:
        return queryset
    elif str(parent).lower() in ['none', 'false', 'null', 'top', '0']:
        return queryset.filter(parent=None)
    else:
        try:
            parent_id = int(parent)
            if parent_id == 0:
                return queryset.filter(parent=None)
            else:
                return queryset.filter(parent=parent_id)
        except:
            return queryset
