from __future__ import unicode_literals

from django.db import models

from InvenTree.models import InvenTreeTree
from part.models import Part


class ProjectCategory(InvenTreeTree):
    """ ProjectCategory provides hierarchical organization of Project objects.
    Each ProjectCategory can contain zero-or-more child categories,
    and in turn can have zero-or-one parent category.
    """
    
    class Meta:
        verbose_name = "Project Category"
        verbose_name_plural = "Project Categories"


class Project(models.Model):
    """ A Project takes multiple Part objects.
    A project can output zero-or-more Part objects
    """
    
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=500, blank=True)
    category = models.ForeignKey(ProjectCategory, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.name
        
    @property
    def projectParts(self):
        """ Return a list of all project parts associated with this project
        """
        return self.projectpart_set.all()


class ProjectPart(models.Model):
    """ A project part associates a single part with a project
    The quantity of parts required for a single-run of that project is stored.
    The overage is the number of extra parts that are generally used for a single run.
    """    
    
    # Overage types
    OVERAGE_PERCENT = 0
    OVERAGE_ABSOLUTE = 1
    
    part = models.ForeignKey(Part, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    overage = models.FloatField(default=0)
    overage_type = models.IntegerField(
        default=1,
        choices=[
        (OVERAGE_PERCENT, "Percent"),
        (OVERAGE_ABSOLUTE, "Absolute")
        ])
    
    def __str__(self):
        return "{quan} x {name}".format(
            name=self.part.name,
            quan=self.quantity)
