"""
Label printing models
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import io

from blabel import LabelWriter

from django.db import models
from django.core.validators import FileExtensionValidator

from django.utils.translation import gettext_lazy as _

from InvenTree.helpers import validateFilterString, normalize

import stock.models


def rename_label(instance, filename):
    """ Place the label file into the correct subdirectory """

    filename = os.path.basename(filename)

    return os.path.join('label', 'template', instance.SUBDIR, filename)


def validate_stock_item_filters(filters):
    
    filters = validateFilterString(filters, model=stock.models.StockItem)

    return filters


def validate_stock_location_filters(filters):

    filters = validateFilterString(filters, model=stock.models.StockLocation)

    return filters


class LabelTemplate(models.Model):
    """
    Base class for generic, filterable labels.
    """

    class Meta:
        abstract = True

    # Each class of label files will be stored in a separate subdirectory
    SUBDIR = "label"

    @property
    def template(self):
        return self.label.path

    def __str__(self):
        return "{n} - {d}".format(
            n=self.name,
            d=self.description
        )

    name = models.CharField(
        blank=False, max_length=100,
        verbose_name=_('Name'),
        help_text=_('Label name'),
    )

    description = models.CharField(
        max_length=250,
        blank=True, null=True,
        verbose_name=_('Description'),
        help_text=_('Label description'),
    )

    label = models.FileField(
        upload_to=rename_label,
        unique=True,
        blank=False, null=False,
        verbose_name=_('Label'),
        help_text=_('Label template file'),
        validators=[FileExtensionValidator(allowed_extensions=['html'])],
    )

    enabled = models.BooleanField(
        default=True,
        verbose_name=_('Enabled'),
        help_text=_('Label template is enabled'),
    )

    def get_record_data(self, items):
        """
        Return a list of dict objects, one for each item.
        """

        return []

    def render_to_file(self, filename, items, **kwargs):
        """
        Render labels to a PDF file
        """

        records = self.get_record_data(items)

        writer = LabelWriter(self.template)

        writer.write_labels(records, filename)

    def render(self, items, **kwargs):
        """
        Render labels to an in-memory PDF object, and return it
        """

        records = self.get_record_data(items)

        writer = LabelWriter(self.template)

        buffer = io.BytesIO()

        writer.write_labels(records, buffer)

        return buffer


class StockItemLabel(LabelTemplate):
    """
    Template for printing StockItem labels
    """

    SUBDIR = "stockitem"

    filters = models.CharField(
        blank=True, max_length=250,
        help_text=_('Query filters (comma-separated list of key=value pairs'),
        verbose_name=_('Filters'),
        validators=[
            validate_stock_item_filters]
    )

    def matches_stock_item(self, item):
        """
        Test if this label template matches a given StockItem object
        """

        filters = validateFilterString(self.filters)

        items = stock.models.StockItem.objects.filter(**filters)

        items = items.filter(pk=item.pk)

        return items.exists()

    def get_record_data(self, items):
        """
        Generate context data for each provided StockItem
        """
        records = []
        
        for item in items:

            # Add some basic information
            records.append({
                'item': item,
                'part': item.part,
                'name': item.part.name,
                'ipn': item.part.IPN,
                'quantity': normalize(item.quantity),
                'serial': item.serial,
                'uid': item.uid,
                'pk': item.pk,
                'qr_data': item.format_barcode(brief=True),
                'tests': item.testResultMap()
            })

        return records


class StockLocationLabel(LabelTemplate):
    """
    Template for printing StockLocation labels
    """

    SUBDIR = "stocklocation"

    filters = models.CharField(
        blank=True, max_length=250,
        help_text=_('Query filters (comma-separated list of key=value pairs'),
        verbose_name=_('Filters'),
        validators=[
            validate_stock_location_filters]
    )

    def matches_stock_location(self, location):
        """
        Test if this label template matches a given StockLocation object
        """

        filters = validateFilterString(self.filters)

        locs = stock.models.StockLocation.objects.filter(**filters)

        locs = locs.filter(pk=location.pk)

        return locs.exists()

    def get_record_data(self, locations):
        """
        Generate context data for each provided StockLocation
        """

        records = []
        
        for loc in locations:

            records.append({
                'location': loc,
            })

        return records
