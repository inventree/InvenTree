"""
Label printing models
"""

import sys
import os
import logging
import datetime

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.core.validators import FileExtensionValidator, MinValueValidator
from django.core.exceptions import ValidationError, FieldError

from django.template import Template, Context
from django.template.loader import render_to_string

from django.utils.translation import gettext_lazy as _

from InvenTree.helpers import validateFilterString, normalize

import common.models
import stock.models
import part.models


try:
    from django_weasyprint import WeasyTemplateResponseMixin
except OSError as err:  # pragma: no cover
    print("OSError: {e}".format(e=err))
    print("You may require some further system packages to be installed.")
    sys.exit(1)


logger = logging.getLogger("inventree")


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


def validate_part_filters(filters):

    filters = validateFilterString(filters, model=part.models.Part)

    return filters


class WeasyprintLabelMixin(WeasyTemplateResponseMixin):
    """
    Class for rendering a label to a PDF
    """

    pdf_filename = 'label.pdf'
    pdf_attachment = True

    def __init__(self, request, template, **kwargs):

        self.request = request
        self.template_name = template
        self.pdf_filename = kwargs.get('filename', 'label.pdf')


class LabelTemplate(models.Model):
    """
    Base class for generic, filterable labels.
    """

    class Meta:
        abstract = True

    # Each class of label files will be stored in a separate subdirectory
    SUBDIR = "label"

    # Object we will be printing against (will be filled out later)
    object_to_print = None

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

    width = models.FloatField(
        default=50,
        verbose_name=_('Width [mm]'),
        help_text=_('Label width, specified in mm'),
        validators=[MinValueValidator(2)]
    )

    height = models.FloatField(
        default=20,
        verbose_name=_('Height [mm]'),
        help_text=_('Label height, specified in mm'),
        validators=[MinValueValidator(2)]
    )

    filename_pattern = models.CharField(
        default="label.pdf",
        verbose_name=_('Filename Pattern'),
        help_text=_('Pattern for generating label filenames'),
        max_length=100,
    )

    @property
    def template_name(self):
        """
        Returns the file system path to the template file.
        Required for passing the file to an external process
        """

        template = self.label.name
        template = template.replace('/', os.path.sep)
        template = template.replace('\\', os.path.sep)

        template = os.path.join(settings.MEDIA_ROOT, template)

        return template

    def get_context_data(self, request):
        """
        Supply custom context data to the template for rendering.

        Note: Override this in any subclass
        """

        return {}

    def generate_filename(self, request, **kwargs):
        """
        Generate a filename for this label
        """

        template_string = Template(self.filename_pattern)

        ctx = self.context(request)

        context = Context(ctx)

        return template_string.render(context)

    def context(self, request):
        """
        Provides context data to the template.
        """

        context = self.get_context_data(request)

        # Add "basic" context data which gets passed to every label
        context['base_url'] = common.models.InvenTreeSetting.get_setting('INVENTREE_BASE_URL')
        context['date'] = datetime.datetime.now().date()
        context['datetime'] = datetime.datetime.now()
        context['request'] = request
        context['user'] = request.user
        context['width'] = self.width
        context['height'] = self.height

        return context

    def render_as_string(self, request, **kwargs):
        """
        Render the label to a HTML string

        Useful for debug mode (viewing generated code)
        """

        return render_to_string(self.template_name, self.context(request), request)

    def render(self, request, **kwargs):
        """
        Render the label template to a PDF file

        Uses django-weasyprint plugin to render HTML template
        """

        wp = WeasyprintLabelMixin(
            request,
            self.template_name,
            base_url=request.build_absolute_uri("/"),
            presentational_hints=True,
            filename=self.generate_filename(request),
            **kwargs
        )

        return wp.render_to_response(
            self.context(request),
            **kwargs
        )


class StockItemLabel(LabelTemplate):
    """
    Template for printing StockItem labels
    """

    @staticmethod
    def get_api_url():
        return reverse('api-stockitem-label-list')

    SUBDIR = "stockitem"

    filters = models.CharField(
        blank=True, max_length=250,
        help_text=_('Query filters (comma-separated list of key=value pairs),'),
        verbose_name=_('Filters'),
        validators=[
            validate_stock_item_filters
        ]
    )

    def matches_stock_item(self, item):
        """
        Test if this label template matches a given StockItem object
        """

        try:
            filters = validateFilterString(self.filters)
            items = stock.models.StockItem.objects.filter(**filters)
        except (ValidationError, FieldError):
            # If an error exists with the "filters" field, return False
            return False

        items = items.filter(pk=item.pk)

        return items.exists()

    def get_context_data(self, request):
        """
        Generate context data for each provided StockItem
        """

        stock_item = self.object_to_print

        return {
            'item': stock_item,
            'part': stock_item.part,
            'name': stock_item.part.full_name,
            'ipn': stock_item.part.IPN,
            'revision': stock_item.part.revision,
            'quantity': normalize(stock_item.quantity),
            'serial': stock_item.serial,
            'uid': stock_item.uid,
            'qr_data': stock_item.format_barcode(brief=True),
            'qr_url': stock_item.format_barcode(url=True, request=request),
            'tests': stock_item.testResultMap(),
            'parameters': stock_item.part.parameters_map(),

        }


class StockLocationLabel(LabelTemplate):
    """
    Template for printing StockLocation labels
    """

    @staticmethod
    def get_api_url():
        return reverse('api-stocklocation-label-list')

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

        try:
            filters = validateFilterString(self.filters)
            locs = stock.models.StockLocation.objects.filter(**filters)
        except (ValidationError, FieldError):
            return False

        locs = locs.filter(pk=location.pk)

        return locs.exists()

    def get_context_data(self, request):
        """
        Generate context data for each provided StockLocation
        """

        location = self.object_to_print

        return {
            'location': location,
            'qr_data': location.format_barcode(brief=True),
        }


class PartLabel(LabelTemplate):
    """
    Template for printing Part labels
    """

    @staticmethod
    def get_api_url():
        return reverse('api-part-label-list')

    SUBDIR = 'part'

    filters = models.CharField(
        blank=True, max_length=250,
        help_text=_('Part query filters (comma-separated value of key=value pairs)'),
        verbose_name=_('Filters'),
        validators=[
            validate_part_filters
        ]
    )

    def matches_part(self, part):
        """
        Test if this label template matches a given Part object
        """

        try:
            filters = validateFilterString(self.filters)
            parts = part.models.Part.objects.filter(**filters)
        except (ValidationError, FieldError):
            return False

        parts = parts.filter(pk=part.pk)

        return parts.exists()

    def get_context_data(self, request):
        """
        Generate context data for each provided Part object
        """

        part = self.object_to_print

        return {
            'part': part,
            'category': part.category,
            'name': part.name,
            'description': part.description,
            'IPN': part.IPN,
            'revision': part.revision,
            'qr_data': part.format_barcode(brief=True),
            'qr_url': part.format_barcode(url=True, request=request),
            'parameters': part.parameters_map(),
        }
