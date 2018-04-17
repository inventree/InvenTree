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

    def get_absolute_url(self):
        return '/build/{pk}/'.format(pk=self.id)

    # Build status codes
    PENDING = 10  # Build is pending / active
    HOLDING = 20  # Build is currently being held
    CANCELLED = 30  # Build was cancelled
    COMPLETE = 40  # Build is complete

    BUILD_STATUS_CODES = {PENDING: _("Pending"),
                          HOLDING: _("Holding"),
                          CANCELLED: _("Cancelled"),
                          COMPLETE: _("Complete"),
                          }

    batch = models.CharField(max_length=100, blank=True, null=True,
                             help_text='Batch code for this build output')

    # Status of the build
    status = models.PositiveIntegerField(default=PENDING,
                                         choices=BUILD_STATUS_CODES.items(),
                                         validators=[MinValueValidator(0)])

    # Date the build model was 'created'
    creation_date = models.DateField(auto_now=True, editable=False)

    # Date the build was 'completed'
    completion_date = models.DateField(null=True, blank=True)

    # Brief build title
    title = models.CharField(max_length=100, help_text='Brief description of the build')

    # A reference to the part being built
    # Only 'buildable' parts can be selected
    part = models.ForeignKey(Part, on_delete=models.CASCADE,
                             related_name='builds',
                             limit_choices_to={'buildable': True},
                             )

    # How many parts to build?
    quantity = models.PositiveIntegerField(default=1,
                                           validators=[MinValueValidator(1)],
                                           help_text='Number of parts to build')

    # Notes can be attached to each build output
    notes = models.CharField(max_length=500, blank=True)

    @property
    def is_active(self):
        """ Is this build active?
        An active build is either:
        - Pending
        - Holding
        """

        return self.status in [
            self.PENDING,
            self.HOLDING
        ]

    @property
    def is_complete(self):
        return self.status == self.COMPLETE
