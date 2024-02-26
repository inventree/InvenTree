"""Label printing models."""

import datetime
import logging
import os
import sys

from django.conf import settings
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator, MinValueValidator
from django.db import models
from django.template import Context, Template
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

import build.models
import InvenTree.models
import part.models
import stock.models
from InvenTree.helpers import normalize, validateFilterString
from InvenTree.helpers_model import get_base_url
from InvenTree.storage_backends import private_storage
from plugin.registry import registry

try:
    from django_weasyprint import WeasyTemplateResponseMixin
except OSError as err:  # pragma: no cover
    print(f'OSError: {err}')
    print('You may require some further system packages to be installed.')
    sys.exit(1)


logger = logging.getLogger('inventree')


def rename_label(instance, filename):
    """Place the label file into the correct subdirectory."""
    filename = os.path.basename(filename)

    return os.path.join('label', 'template', instance.SUBDIR, filename)


def rename_label_output(instance, filename):
    """Place the label output file into the correct subdirectory."""
    filename = os.path.basename(filename)

    return os.path.join('label', 'output', filename)


def validate_stock_item_filters(filters):
    """Validate query filters for the StockItemLabel model."""
    filters = validateFilterString(filters, model=stock.models.StockItem)

    return filters


def validate_stock_location_filters(filters):
    """Validate query filters for the StockLocationLabel model."""
    filters = validateFilterString(filters, model=stock.models.StockLocation)

    return filters


def validate_part_filters(filters):
    """Validate query filters for the PartLabel model."""
    filters = validateFilterString(filters, model=part.models.Part)

    return filters


def validate_build_line_filters(filters):
    """Validate query filters for the BuildLine model."""
    filters = validateFilterString(filters, model=build.models.BuildLine)

    return filters


class WeasyprintLabelMixin(WeasyTemplateResponseMixin):
    """Class for rendering a label to a PDF."""

    pdf_filename = 'label.pdf'
    pdf_attachment = True

    def __init__(self, request, template, **kwargs):
        """Initialize a label mixin with certain properties."""
        self.request = request
        self.template_name = template
        self.pdf_filename = kwargs.get('filename', 'label.pdf')


class LabelTemplate(InvenTree.models.InvenTreeMetadataModel):
    """Base class for generic, filterable labels."""

    class Meta:
        """Metaclass options. Abstract ensures no database table is created."""

        abstract = True

    # Each class of label files will be stored in a separate subdirectory
    SUBDIR = 'label'

    # Object we will be printing against (will be filled out later)
    object_to_print = None

    @property
    def template(self):
        """Return the file path of the template associated with this label instance."""
        return self.label.path

    def __str__(self):
        """Format a string representation of a label instance."""
        return f'{self.name} - {self.description}'

    name = models.CharField(
        blank=False, max_length=100, verbose_name=_('Name'), help_text=_('Label name')
    )

    description = models.CharField(
        max_length=250,
        blank=True,
        null=True,
        verbose_name=_('Description'),
        help_text=_('Label description'),
    )

    label = models.FileField(
        storage=private_storage,
        upload_to=rename_label,
        unique=True,
        blank=False,
        null=False,
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
        validators=[MinValueValidator(2)],
    )

    height = models.FloatField(
        default=20,
        verbose_name=_('Height [mm]'),
        help_text=_('Label height, specified in mm'),
        validators=[MinValueValidator(2)],
    )

    filename_pattern = models.CharField(
        default='label.pdf',
        verbose_name=_('Filename Pattern'),
        help_text=_('Pattern for generating label filenames'),
        max_length=100,
    )

    @property
    def template_name(self):
        """Returns the file system path to the template file.

        Required for passing the file to an external process
        """
        template = self.label.name
        template = template.replace('/', os.path.sep)
        template = template.replace('\\', os.path.sep)

        template = settings.MEDIA_ROOT.joinpath(template)

        return template

    def get_context_data(self, request):
        """Supply custom context data to the template for rendering.

        Note: Override this in any subclass
        """
        return {}  # pragma: no cover

    def generate_filename(self, request, **kwargs):
        """Generate a filename for this label."""
        template_string = Template(self.filename_pattern)

        ctx = self.context(request)

        context = Context(ctx)

        return template_string.render(context)

    def generate_page_style(self, **kwargs):
        """Generate @page style for the label template.

        This is inserted at the top of the style block for a given label
        """
        width = kwargs.get('width', self.width)
        height = kwargs.get('height', self.height)
        margin = kwargs.get('margin', 0)

        return f"""
        @page {{
            size: {width}mm {height}mm;
            margin: {margin}mm;
        }}
        """

    def context(self, request, **kwargs):
        """Provides context data to the template.

        Arguments:
            request: The HTTP request object
            kwargs: Additional keyword arguments
        """
        context = self.get_context_data(request)

        # By default, each label is supplied with '@page' data
        # However, it can be excluded, e.g. when rendering a label sheet
        if kwargs.get('insert_page_style', True):
            context['page_style'] = self.generate_page_style()

        # Add "basic" context data which gets passed to every label
        context['base_url'] = get_base_url(request=request)
        context['date'] = datetime.datetime.now().date()
        context['datetime'] = datetime.datetime.now()
        context['request'] = request
        context['user'] = request.user
        context['width'] = self.width
        context['height'] = self.height

        # Pass the context through to any registered plugins
        plugins = registry.with_mixin('report')

        for plugin in plugins:
            # Let each plugin add its own context data
            plugin.add_label_context(self, self.object_to_print, request, context)

        return context

    def render_as_string(self, request, target_object=None, **kwargs):
        """Render the label to a HTML string."""
        if target_object:
            self.object_to_print = target_object

        context = self.context(request, **kwargs)

        return render_to_string(self.template_name, context, request)

    def render(self, request, target_object=None, **kwargs):
        """Render the label template to a PDF file.

        Uses django-weasyprint plugin to render HTML template
        """
        if target_object:
            self.object_to_print = target_object

        context = self.context(request, **kwargs)

        wp = WeasyprintLabelMixin(
            request,
            self.template_name,
            base_url=request.build_absolute_uri('/'),
            presentational_hints=True,
            filename=self.generate_filename(request),
            **kwargs,
        )

        return wp.render_to_response(context, **kwargs)


class LabelOutput(models.Model):
    """Class representing a label output file.

    'Printing' a label may generate a file object (such as PDF)
    which is made available for download.

    Future work will offload this task to the background worker,
    and provide a 'progress' bar for the user.
    """

    # File will be stored in a subdirectory
    label = models.FileField(
        storage=private_storage,
        upload_to=rename_label_output,
        unique=True,
        blank=False,
        null=False,
    )

    # Creation date of label output
    created = models.DateField(auto_now_add=True, editable=False)

    # User who generated the label
    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)


class StockItemLabel(LabelTemplate):
    """Template for printing StockItem labels."""

    @staticmethod
    def get_api_url():
        """Return the API URL associated with the StockItemLabel model."""
        return reverse('api-stockitem-label-list')  # pragma: no cover

    SUBDIR = 'stockitem'

    filters = models.CharField(
        blank=True,
        max_length=250,
        help_text=_('Query filters (comma-separated list of key=value pairs)'),
        verbose_name=_('Filters'),
        validators=[validate_stock_item_filters],
    )

    def get_context_data(self, request):
        """Generate context data for each provided StockItem."""
        stock_item = self.object_to_print

        return {
            'item': stock_item,
            'part': stock_item.part,
            'name': stock_item.part.full_name,
            'ipn': stock_item.part.IPN,
            'revision': stock_item.part.revision,
            'quantity': normalize(stock_item.quantity),
            'serial': stock_item.serial,
            'barcode_data': stock_item.barcode_data,
            'barcode_hash': stock_item.barcode_hash,
            'qr_data': stock_item.format_barcode(brief=True),
            'qr_url': request.build_absolute_uri(stock_item.get_absolute_url()),
            'tests': stock_item.testResultMap(),
            'parameters': stock_item.part.parameters_map(),
        }


class StockLocationLabel(LabelTemplate):
    """Template for printing StockLocation labels."""

    @staticmethod
    def get_api_url():
        """Return the API URL associated with the StockLocationLabel model."""
        return reverse('api-stocklocation-label-list')  # pragma: no cover

    SUBDIR = 'stocklocation'

    filters = models.CharField(
        blank=True,
        max_length=250,
        help_text=_('Query filters (comma-separated list of key=value pairs)'),
        verbose_name=_('Filters'),
        validators=[validate_stock_location_filters],
    )

    def get_context_data(self, request):
        """Generate context data for each provided StockLocation."""
        location = self.object_to_print

        return {'location': location, 'qr_data': location.format_barcode(brief=True)}


class PartLabel(LabelTemplate):
    """Template for printing Part labels."""

    @staticmethod
    def get_api_url():
        """Return the API url associated with the PartLabel model."""
        return reverse('api-part-label-list')  # pragma: no cover

    SUBDIR = 'part'

    filters = models.CharField(
        blank=True,
        max_length=250,
        help_text=_('Query filters (comma-separated list of key=value pairs)'),
        verbose_name=_('Filters'),
        validators=[validate_part_filters],
    )

    def get_context_data(self, request):
        """Generate context data for each provided Part object."""
        part = self.object_to_print

        return {
            'part': part,
            'category': part.category,
            'name': part.name,
            'description': part.description,
            'IPN': part.IPN,
            'revision': part.revision,
            'qr_data': part.format_barcode(brief=True),
            'qr_url': request.build_absolute_uri(part.get_absolute_url()),
            'parameters': part.parameters_map(),
        }


class BuildLineLabel(LabelTemplate):
    """Template for printing labels against BuildLine objects."""

    @staticmethod
    def get_api_url():
        """Return the API URL associated with the BuildLineLabel model."""
        return reverse('api-buildline-label-list')

    SUBDIR = 'buildline'

    filters = models.CharField(
        blank=True,
        max_length=250,
        help_text=_('Query filters (comma-separated list of key=value pairs)'),
        verbose_name=_('Filters'),
        validators=[validate_build_line_filters],
    )

    def get_context_data(self, request):
        """Generate context data for each provided BuildLine object."""
        build_line = self.object_to_print

        return {
            'build_line': build_line,
            'build': build_line.build,
            'bom_item': build_line.bom_item,
            'part': build_line.bom_item.sub_part,
            'quantity': build_line.quantity,
            'allocated_quantity': build_line.allocated_quantity,
            'allocations': build_line.allocations,
        }
