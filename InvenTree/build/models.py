"""
Build models

Defines the database models for part Builds
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.translation import ugettext as _

from django.urls import reverse
from django.db import models
from django.core.validators import MinValueValidator


class Build(models.Model):
    """ A Build object organises the creation of new parts from the component parts.
    """

    def get_absolute_url(self):
        return reverse('build-detail', kwargs={'pk': self.id})

    part = models.ForeignKey('part.Part', on_delete=models.CASCADE,
                             related_name='builds',
                             limit_choices_to={'buildable': True},
                             )
    """ A reference to the part being built - only parts marked as 'buildable' may be selected """
    
    #: Brief title describing the build
    title = models.CharField(max_length=100, help_text='Brief description of the build')
    
    #: Number of output parts to build
    quantity = models.PositiveIntegerField(default=1,
                                           validators=[MinValueValidator(1)],
                                           help_text='Number of parts to build')

    # Build status codes
    PENDING = 10  # Build is pending / active
    HOLDING = 20  # Build is currently being held
    CANCELLED = 30  # Build was cancelled
    COMPLETE = 40  # Build is complete

    #: Build status codes
    BUILD_STATUS_CODES = {PENDING: _("Pending"),
                          HOLDING: _("Holding"),
                          CANCELLED: _("Cancelled"),
                          COMPLETE: _("Complete"),
                          }

    #: Status of the build (ref BUILD_STATUS_CODES)
    status = models.PositiveIntegerField(default=PENDING,
                                         choices=BUILD_STATUS_CODES.items(),
                                         validators=[MinValueValidator(0)])

    #: Batch number for the build (optional)
    batch = models.CharField(max_length=100, blank=True, null=True,
                             help_text='Batch code for this build output')


    #: Date the build model was 'created'
    creation_date = models.DateField(auto_now=True, editable=False)

    #: Date the build was 'completed' (and parts removed from stock)
    completion_date = models.DateField(null=True, blank=True)

    #: Notes attached to each build output
    notes = models.TextField(blank=True)

    @property
    def required_parts(self):
        """ Returns a dict of parts required to build this part (BOM) """
        parts = []

        for item in self.part.bom_items.all():
            part = {'part': item.sub_part,
                    'per_build': item.quantity,
                    'quantity': item.quantity * self.quantity
                    }

            parts.append(part)

        return parts

    @property
    def can_build(self):
        """ Return true if there are enough parts to supply build """

        for item in self.required_parts:
            if item['part'].total_stock < item['quantity']:
                return False

        return True

    @property
    def is_active(self):
        """ Is this build active? An active build is either:

        - PENDING
        - HOLDING
        """

        return self.status in [
            self.PENDING,
            self.HOLDING
        ]

    @property
    def is_complete(self):
        """ Returns True if the build status is COMPLETE """
        return self.status == self.COMPLETE
