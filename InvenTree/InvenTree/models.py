"""
Generic models which provide extra functionality over base Django model types.
"""

from __future__ import unicode_literals

from django.db import models
from django.contrib.contenttypes.models import ContentType
from rest_framework.exceptions import ValidationError

from django.db.models.signals import pre_delete
from django.dispatch import receiver

from .validators import validate_tree_name


class InvenTreeTree(models.Model):
    """ Provides an abstracted self-referencing tree model for data categories.

    - Each Category has one parent Category, which can be blank (for a top-level Category).
    - Each Category can have zero-or-more child Categor(y/ies)

    Attributes:
        name: brief name
        description: longer form description
        parent: The item immediately above this one. An item with a null parent is a top-level item
    """

    class Meta:
        abstract = True
        unique_together = ('name', 'parent')

    name = models.CharField(
        blank=False,
        max_length=100,
        unique=True,
        validators=[validate_tree_name]
    )

    description = models.CharField(
        blank=False,
        max_length=250
    )

    # When a category is deleted, graft the children onto its parent
    parent = models.ForeignKey('self',
                               on_delete=models.DO_NOTHING,
                               blank=True,
                               null=True,
                               related_name='children')

    @property
    def item_count(self):
        """ Return the number of items which exist *under* this node in the tree.

        Here an 'item' is considered to be the 'leaf' at the end of each branch,
        and the exact nature here will depend on the class implementation.
        
        The default implementation returns zero
        """
        return 0

    def getUniqueParents(self, unique=None):
        """ Return a flat set of all parent items that exist above this node.
        If any parents are repeated (which would be very bad!), the process is halted
        """

        item = self

        # Prevent infinite regression
        max_parents = 500

        unique = set()

        while item.parent and max_parents > 0:
            max_parents -= 1

            unique.add(item.parent.id)
            item = item.parent

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
    def has_children(self):
        """ True if there are any children under this item """
        return self.children.count() > 0

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
        """ Get the parent path of this category

        Returns:
            List of category names from the top level to the parent of this category
        """

        if self.parent:
            return self.parent.parentpath + [self.parent]
        else:
            return []

    @property
    def path(self):
        """ Get the complete part of this category.

        e.g. ["Top", "Second", "Third", "This"]

        Returns:
            List of category names from the top level to this category
        """
        return self.parentpath + [self]

    @property
    def pathstring(self):
        """ Get a string representation for the path of this item.

        e.g. "Top/Second/Third/This"
        """
        return '/'.join([item.name for item in self.path])

    def clean(self):
        """ Custom cleaning

        Parent:
        Setting the parent of an item to its own child results in an infinite loop.
        The parent of an item cannot be set to:
            a) Its own ID
            b) The ID of any child items that exist underneath it

        Name:
        Tree node names are limited to a reduced character set
        """

        super().clean()

        # Parent cannot be set to same ID (this would cause looping)
        try:
            if self.parent.id == self.id:
               raise ValidationError("Category cannot set itself as parent")
        except:
            pass

        # Ensure that the new parent is not already a child
        if self.id in self.getUniqueChildren():
            raise ValidationError("Category cannot set a child as parent")

    def __str__(self):
        """ String representation of a category is the full path to that category """

        return self.pathstring


@receiver(pre_delete, sender=InvenTreeTree, dispatch_uid='tree_pre_delete_log')
def before_delete_tree_item(sender, instance, using, **kwargs):
    """ Receives pre_delete signal from InvenTreeTree object.

    Before an item is deleted, update each child object to point to the parent of the object being deleted.
    """

    # Update each tree item below this one
    for child in instance.children.all():
        child.parent = instance.parent
        child.save()
