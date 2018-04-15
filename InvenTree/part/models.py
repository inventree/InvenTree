from __future__ import unicode_literals
from django.utils.translation import ugettext as _
from django.db import models
from django.db.models import Sum
from django.core.validators import MinValueValidator

from InvenTree.models import InvenTreeTree

import os

from django.db.models.signals import pre_delete
from django.dispatch import receiver


class PartCategory(InvenTreeTree):
    """ PartCategory provides hierarchical organization of Part objects.
    """

    def get_absolute_url(self):
        return '/part/category/{id}/'.format(id=self.id)

    class Meta:
        verbose_name = "Part Category"
        verbose_name_plural = "Part Categories"


    @property
    def partcount(self):
        """ Return the total part count under this category
        (including children of child categories)
        """

        count = self.parts.count()

        for child in self.children.all():
            count += child.partcount

        return count

    """
    @property
    def parts(self):
        return self.part_set.all()
    """

@receiver(pre_delete, sender=PartCategory, dispatch_uid='partcategory_delete_log')
def before_delete_part_category(sender, instance, using, **kwargs):

    # Update each part in this category to point to the parent category
    for part in instance.parts.all():
        part.category = instance.parent
        part.save()

    # Update each child category
    for child in instance.children.all():
        child.parent = instance.parent
        child.save()


# Function to automatically rename a part image on upload
# Format: part_pk.<img>
def rename_part_image(instance, filename):
    base = 'part_images'

    if filename.count('.') > 0:
        ext = filename.split('.')[-1]
    else:
        ext = ''

    fn = 'part_{pk}_img'.format(pk=instance.pk)

    if ext:
        fn += '.' + ext

    return os.path.join(base, fn)


class Part(models.Model):
    """ Represents an abstract part
    Parts can be "stocked" in multiple warehouses,
    and can be combined to form other parts
    """

    def get_absolute_url(self):
        return '/part/{id}/'.format(id=self.id)

    # Short name of the part
    name = models.CharField(max_length=100, unique=True)

    # Longer description of the part (optional)
    description = models.CharField(max_length=250)

    # Internal Part Number (optional)
    # Potentially multiple parts map to the same internal IPN (variants?)
    # So this does not have to be unique
    IPN = models.CharField(max_length=100, blank=True)

    # Provide a URL for an external link
    URL = models.URLField(blank=True)

    # Part category - all parts must be assigned to a category
    category = models.ForeignKey(PartCategory, related_name='parts',
                                 null=True, blank=True,
                                 on_delete=models.DO_NOTHING)

    image = models.ImageField(upload_to=rename_part_image, max_length=255, null=True, blank=True)

    # Minimum "allowed" stock level
    minimum_stock = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)])

    # Units of quantity for this part. Default is "pcs"
    units = models.CharField(max_length=20, default="pcs", blank=True)

    # Is this part "trackable"?
    # Trackable parts can have unique instances which are assigned serial numbers
    # and can have their movements tracked
    trackable = models.BooleanField(default=False)

    def __str__(self):
        if self.IPN:
            return "{name} ({ipn})".format(
                ipn=self.IPN,
                name=self.name)
        else:
            return self.name

    class Meta:
        verbose_name = "Part"
        verbose_name_plural = "Parts"
        #unique_together = (("name", "category"),)

    @property
    def stock(self):
        """ Return the total stock quantity for this part.
        Part may be stored in multiple locations
        """

        stocks = self.locations.all()
        if len(stocks) == 0:
            return 0

        result = stocks.aggregate(total=Sum('quantity'))
        return result['total']

    @property
    def bomItemCount(self):
        return self.bom_items.all().count()


    @property
    def usedInCount(self):
        return self.used_in.all().count()

    """
    @property
    def projects(self):
        " Return a list of unique projects that this part is associated with.
        A part may be used in zero or more projects.
        "

        project_ids = set()
        project_parts = self.projectpart_set.all()

        projects = []

        for pp in project_parts:
            if pp.project.id not in project_ids:
                project_ids.add(pp.project.id)
                projects.append(pp.project)

        return projects
    """

def attach_file(instance, filename):

    base='part_files'

    # TODO - For a new PartAttachment object, PK is NULL!!

    # Prefix the attachment ID to the filename
    fn = "{id}_{fn}".format(id=instance.pk, fn=filename)

    return os.path.join(base, fn)

class PartAttachment(models.Model):
    """ A PartAttachment links a file to a part
    Parts can have multiple files such as datasheets, etc
    """


    part = models.ForeignKey(Part, on_delete=models.CASCADE,
                             related_name='attachments')

    attachment = models.FileField(upload_to=attach_file, null=True, blank=True)



class BomItem(models.Model):
    """ A BomItem links a part to its component items.
    A part can have a BOM (bill of materials) which defines
    which parts are required (and in what quatity) to make it
    """

    # A link to the parent part
    # Each part will get a reverse lookup field 'bom_items'
    part = models.ForeignKey(Part, on_delete=models.CASCADE, related_name='bom_items')

    # A link to the child item (sub-part)
    # Each part will get a reverse lookup field 'used_in'
    sub_part = models.ForeignKey(Part, on_delete=models.CASCADE, related_name='used_in')

    # Quantity required
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(0)])


    class Meta:
        verbose_name = "BOM Item"

        # Prevent duplication of parent/child rows
        unique_together = ('part', 'sub_part')

    def __str__(self):
        return "{par} -> {child} ({n})".format(
            par=self.part.name,
            child=self.sub_part.name,
            n=self.quantity)
