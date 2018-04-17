# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.translation import ugettext as _

from django.db import models
from django.core.validators import MinValueValidator

from part.models import Part

class Build(models.Model):
    """ A Build object organises the creation of new parts from the component parts
    It uses the part BOM to generate new parts.
    Parts are then taken from stock
    """

    # Build status codes
    PENDING = 10
    ALLOCATED = 20
    HOLDING = 30
    CANCELLED = 40
    COMPLETE = 50

    BUILD_STATUS_CODES = {
       PENDING : _("Pending"),
       ALLOCATED : _("Allocated"),
       HOLDING : _("Holding"),
       CANCELLED : _("Cancelled"),
       COMPLETE : _("Complete"),
    }

    # Status of the build
    status = models.PositiveIntegerField(default=PENDING,
                                         choices=BUILD_STATUS_CODES.items(),
                                         validators=[MinValueValidator(0)])


class BuildOutput(models.Model):
    """
    A build output represents a single build part/quantity combination
    """

    batch = models.CharField(max_length=100, blank=True,
                             help_text='Batch code for this build output')

    # Reference to the build object of which this output is a part
    # A build can have multiple outputs
    build = models.ForeignKey(Build, on_delete=models.CASCADE,
                              related_name='outputs')

    # A reference to the part being built
    part = models.ForeignKey(Part, on_delete=models.CASCADE,
                             related_name='builds')

    # How many parts to build?
    quantity = models.PositiveIntegerField(default=1,
                                           validators=[MinValueValidator(1)],
                                           help_text='Number of parts to build')
