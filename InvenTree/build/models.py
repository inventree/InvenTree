# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.core.validators import MinValueValidator

from InvenTree.helpers import ChoiceEnum

from part.models import Part

class Build(models.Model):
    """ A Build object organises the creation of new parts from the component parts
    It uses the part BOM to generate new parts.
    Parts are then taken from stock
    """

    class BUILD_STATUS(ChoiceEnum):
        # The build is 'pending' - no action taken yet
        Pending = 10

        # The parts required for this build have been allocated
        Allocated = 20

        # The build has been cancelled (parts unallocated)
        Cancelled = 30

        # The build is complete!
        Complete = 40

    # Status of the build
    status = models.PositiveIntegerField(default=BUILD_STATUS.Pending.value,
                                         choices=BUILD_STATUS.choices())

    part = models.ForeignKey(Part, on_delete=models.CASCADE,
                             related_name='builds')

    quantity = models.PositiveIntegerField(default=1,
                                           validators=[MinValueValidator(1)],
                                           help_text='Number of parts to build')
