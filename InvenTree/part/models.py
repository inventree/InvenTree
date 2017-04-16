from __future__ import unicode_literals
from django.utils.translation import ugettext as _
from django.db import models
from django.db.models import Sum
from django.core.validators import MinValueValidator

from InvenTree.models import InvenTreeTree


class PartCategory(InvenTreeTree):
    """ PartCategory provides hierarchical organization of Part objects.
    """

    class Meta:
        verbose_name = "Part Category"
        verbose_name_plural = "Part Categories"

    @property
    def parts(self):
        return self.part_set.all()


class Part(models.Model):
    """ Represents a """

    # Short name of the part
    name = models.CharField(max_length=100)

    # Longer description of the part (optional)
    description = models.CharField(max_length=250, blank=True)

    # Internal Part Number (optional)
    IPN = models.CharField(max_length=100, blank=True)

    # Part category - all parts must be assigned to a category
    category = models.ForeignKey(PartCategory, on_delete=models.CASCADE)

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
        unique_together = (("name", "category"),
                           ("IPN", "category"))

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
    def projects(self):
        """ Return a list of unique projects that this part is associated with.
        A part may be used in zero or more projects.
        """

        project_ids = set()
        project_parts = self.projectpart_set.all()

        projects = []

        for pp in project_parts:
            if pp.project.id not in project_ids:
                project_ids.add(pp.project.id)
                projects.append(pp.project)

        return projects


class PartParameterTemplate(models.Model):
    """ A PartParameterTemplate pre-defines a parameter field,
    ready to be copied for use with a given Part.
    A PartParameterTemplate can be optionally associated with a PartCategory
    """
    name = models.CharField(max_length=20, unique=True)
    units = models.CharField(max_length=10, blank=True)

    # Parameter format
    PARAM_NUMERIC = 10
    PARAM_TEXT = 20
    PARAM_BOOL = 30

    PARAM_TYPE_CODES = {
        PARAM_NUMERIC: _("Numeric"),
        PARAM_TEXT: _("Text"),
        PARAM_BOOL: _("Bool")
    }

    format = models.PositiveIntegerField(
        default=PARAM_NUMERIC,
        choices=PARAM_TYPE_CODES.items(),
        validators=[MinValueValidator(0)])

    def __str__(self):
        return "{name} ({units})".format(
            name=self.name,
            units=self.units)

    class Meta:
        verbose_name = "Parameter Template"
        verbose_name_plural = "Parameter Templates"


class CategoryParameterLink(models.Model):
    """ Links a PartParameterTemplate to a PartCategory
    """
    category = models.ForeignKey(PartCategory, on_delete=models.CASCADE)
    template = models.ForeignKey(PartParameterTemplate, on_delete=models.CASCADE)

    def __str__(self):
        return "{name} - {cat}".format(
            name=self.template.name,
            cat=self.category)

    class Meta:
        verbose_name = "Category Parameter"
        verbose_name_plural = "Category Parameters"
        unique_together = ('category', 'template')


class PartParameter(models.Model):
    """ PartParameter is associated with a single part
    """

    part = models.ForeignKey(Part, on_delete=models.CASCADE, related_name='parameters')
    template = models.ForeignKey(PartParameterTemplate)

    # Value data
    value = models.CharField(max_length=50, blank=True)
    min_value = models.CharField(max_length=50, blank=True)
    max_value = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return "{name} : {val}{units}".format(
            name=self.template.name,
            val=self.value,
            units=self.template.units)

    @property
    def units(self):
        return self.template.units

    @property
    def name(self):
        return self.template.name

    class Meta:
        verbose_name = "Part Parameter"
        verbose_name_plural = "Part Parameters"
        unique_together = ('part', 'template')
