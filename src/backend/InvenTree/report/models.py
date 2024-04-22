"""Report template model definitions."""

import logging
import os
import sys

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator, MinValueValidator
from django.db import models
from django.template import Context, Template
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

import common.models
import InvenTree.exceptions
import InvenTree.helpers
import InvenTree.models
import report.helpers
import report.validators
from InvenTree.helpers_model import get_base_url
from InvenTree.models import MetadataMixin
from plugin.registry import registry

try:
    from django_weasyprint import WeasyTemplateResponseMixin
except OSError as err:  # pragma: no cover
    print(f'OSError: {err}')
    print('You may require some further system packages to be installed.')
    sys.exit(1)


logger = logging.getLogger('inventree')


class WeasyprintReportMixin(WeasyTemplateResponseMixin):
    """Class for rendering a HTML template to a PDF."""

    pdf_filename = 'report.pdf'
    pdf_attachment = True

    def __init__(self, request, template, **kwargs):
        """Initialize the report mixin with some standard attributes."""
        self.request = request
        self.template_name = template
        self.pdf_filename = kwargs.get('filename', 'report.pdf')


def rename_template(instance, filename):
    """Upload the template to the desired directory."""
    filename = os.path.basename(filename)
    return os.path.join(instance.UPLOAD_DIR, filename)


class ReportTemplateBase(MetadataMixin, InvenTree.models.InvenTreeModel):
    """Base class for reports, labels."""

    class Meta:
        """Metaclass options."""

        abstract = True
        unique_together = ('name', 'model_type')

    def save(self, *args, **kwargs):
        """Perform additional actions when the report is saved."""
        # Increment revision number
        self.revision += 1

        super().save()

    def __str__(self):
        """Format a string representation of a report instance."""
        return f'{self.name} - {self.description}'

    @property
    def extension(self):
        """Return the filename extension of the associated template file."""
        return os.path.splitext(self.template.name)[1].lower()

    @property
    def template_name(self):
        """Returns the file system path to the template file.

        Required for passing the file to an external process
        """
        template = self.template.name

        # TODO @matmair change to using new file objects
        template = template.replace('/', os.path.sep)
        template = template.replace('\\', os.path.sep)

        template = settings.MEDIA_ROOT.joinpath(template)

        return template

    name = models.CharField(
        blank=False,
        max_length=100,
        verbose_name=_('Name'),
        help_text=_('Template name'),
        unique=True,
    )

    description = models.CharField(
        max_length=250,
        verbose_name=_('Description'),
        help_text=_('Template description'),
    )

    template = models.FileField(
        upload_to=rename_template,
        verbose_name=_('Template'),
        help_text=_('Template file'),
        validators=[FileExtensionValidator(allowed_extensions=['html', 'htm'])],
    )

    revision = models.PositiveIntegerField(
        default=1,
        verbose_name=_('Revision'),
        help_text=_('Revision number (auto-increments)'),
        editable=False,
    )

    def generate_filename(self, context, **kwargs):
        """Generate a filename for this report."""
        template_string = Template(self.filename_pattern)

        return template_string.render(Context(context))

    def render_as_string(self, instance, request, **kwargs):
        """Render the report to a HTML string.

        Useful for debug mode (viewing generated code)
        """
        context = self.get_context(instance, request, **kwargs)

        return render_to_string(self.template_name, context, request)

    def render(self, instance, request, **kwargs):
        """Render the template to a PDF file.

        Uses django-weasyprint plugin to render HTML template against Weasyprint
        """
        context = self.get_context(instance, request)

        # Render HTML template to PDF
        wp = WeasyprintReportMixin(
            request,
            self.template_name,
            base_url=request.build_absolute_uri('/'),
            presentational_hints=True,
            filename=self.generate_filename(context),
            **kwargs,
        )

        return wp.render_to_response(context, **kwargs)

    filename_pattern = models.CharField(
        default='report.pdf',
        verbose_name=_('Filename Pattern'),
        help_text=_('Pattern for generating filenames'),
        max_length=100,
    )

    enabled = models.BooleanField(
        default=True, verbose_name=_('Enabled'), help_text=_('Template is enabled')
    )

    model_type = models.CharField(
        max_length=100, validators=[report.validators.validate_report_model_type]
    )

    def clean(self):
        """Clean model instance, and ensure validity."""
        super().clean()

        model = self.get_model()
        filters = self.filters

        if model and filters:
            report.validators.validate_filters(filters, model=model)

    def get_model(self):
        """Return the database model class associated with this report template."""
        return report.helpers.report_model_from_name(self.model_type)

    filters = models.CharField(
        blank=True,
        max_length=250,
        verbose_name=_('Filters'),
        help_text=_('Template query filters (comma-separated list of key=value pairs)'),
        validators=[report.validators.validate_filters],
    )

    def get_filters(self):
        """Return a filter dict which can be applied to the target model."""
        return report.validators.validate_filters(self.filters, model=self.get_model())

    def get_context(self, instance, request, **kwargs):
        """Supply context data to the generic template for rendering.

        Arguments:
            instance: The model instance we are printing against
            request: The request object
        """
        # Provide base context information to all templates
        base_context = {
            'base_url': get_base_url(request=request),
            'date': InvenTree.helpers.current_date(),
            'datetime': InvenTree.helpers.current_time(),
            'template': self,
            'template_description': self.description,
            'template_name': self.name,
            'template_revision': self.revision,
            'request': request,
            'user': request.user,
        }

        # Add in an context information provided by the model instance itself
        context = {**base_context, **instance.report_context()}

        return context


class ReportTemplate(ReportTemplateBase):
    """Class representing the ReportTemplate database model."""

    UPLOAD_DIR = 'report_template'

    def __init__(self, *args, **kwargs):
        """Initialize the particular report instance."""
        super().__init__(*args, **kwargs)

        self._meta.get_field(
            'page_size'
        ).choices = report.helpers.report_page_size_options()

    page_size = models.CharField(
        max_length=20,
        default=report.helpers.report_page_size_default,
        verbose_name=_('Page Size'),
        help_text=_('Page size for PDF reports'),
    )

    landscape = models.BooleanField(
        default=False,
        verbose_name=_('Landscape'),
        help_text=_('Render report in landscape orientation'),
    )

    def get_report_size(self):
        """Return the printable page size for this report."""
        try:
            page_size_default = common.models.InvenTreeSetting.get_setting(
                'REPORT_DEFAULT_PAGE_SIZE', 'A4'
            )
        except Exception:
            page_size_default = 'A4'

        page_size = self.page_size or page_size_default

        if self.landscape:
            page_size = page_size + ' landscape'

        return page_size

    def get_context(self, instance, request, **kwargs):
        """Supply context data to the report template for rendering."""
        context = {
            **super().get_context(instance, request),
            'page_size': self.get_report_size(),
            'landscape': self.landscape,
        }

        # Pass the context through to the plugin registry for any additional information
        for plugin in registry.with_mixin('report'):
            try:
                plugin.add_report_context(self, instance, request, context)
            except Exception:
                InvenTree.exceptions.log_error(
                    f'plugins.{plugin.slug}.add_report_context'
                )

        return context


class LabelTemplate(ReportTemplateBase):
    """Class representing the LabelTemplate database model."""

    UPLOAD_DIR = 'label_template'

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

    def generate_page_style(self, **kwargs):
        """Generate @page style for the label template.

        This is inserted at the top of the style block for a given label
        """
        width = kwargs.get('width', self.width)
        height = kwargs.get('height', self.height)
        margin = kwargs.get('margin', 0)

        return f"""
        @page {{
            {{% localize off %}}
            size: {width}mm {height}mm;
            margin: {margin}mm;
            {{% endlocalize %}}
        }}
        """

    def get_context(self, instance, request, **kwargs):
        """Supply context data to the label template for rendering."""
        context = {
            **super().get_context(instance, request, **kwargs),
            'width': self.width,
            'height': self.height,
        }

        if kwargs.pop('insert_page_style', True):
            context['page_style'] = self.generate_page_style()

        # Pass the context through to any registered plugins
        plugins = registry.with_mixin('report')

        for plugin in plugins:
            # Let each plugin add its own context data
            plugin.add_label_context(self, self.object_to_print, request, context)

        return context


def rename_snippet(instance, filename):
    """Function to rename a report snippet once uploaded."""
    path = ReportSnippet.snippet_path(filename)
    fullpath = settings.MEDIA_ROOT.joinpath(path).resolve()

    # If the snippet file is the *same* filename as the one being uploaded,
    # delete the original one from the media directory
    if str(filename) == str(instance.snippet):
        if fullpath.exists():
            logger.info("Deleting existing snippet file: '%s'", filename)
            os.remove(fullpath)

    # Ensure that the cache is deleted for this snippet
    cache.delete(fullpath)

    return path


class ReportSnippet(models.Model):
    """Report template 'snippet' which can be used to make templates that can then be included in other reports.

    Useful for 'common' template actions, sub-templates, etc
    """

    def __str__(self) -> str:
        """String representation of a ReportSnippet instance."""
        return f'snippets/{self.filename}'

    @property
    def filename(self):
        """Return the filename of the asset."""
        path = self.snippet.name
        if path:
            return os.path.basename(path)
        else:
            return '-'

    @staticmethod
    def snippet_path(filename):
        """Return the fully-qualified snippet path for the given filename."""
        return os.path.join('report', 'snippets', os.path.basename(str(filename)))

    def validate_unique(self, exclude=None):
        """Validate that this report asset is unique."""
        proposed_path = self.snippet_path(self.snippet)

        if (
            ReportSnippet.objects.filter(snippet=proposed_path)
            .exclude(pk=self.pk)
            .count()
            > 0
        ):
            raise ValidationError({
                'snippet': _('Snippet file with this name already exists')
            })

        return super().validate_unique(exclude)

    snippet = models.FileField(
        upload_to=rename_snippet,
        verbose_name=_('Snippet'),
        help_text=_('Report snippet file'),
        validators=[FileExtensionValidator(allowed_extensions=['html', 'htm'])],
    )

    description = models.CharField(
        max_length=250,
        verbose_name=_('Description'),
        help_text=_('Snippet file description'),
    )


def rename_asset(instance, filename):
    """Function to rename an asset file when uploaded."""
    path = ReportAsset.asset_path(filename)
    fullpath = settings.MEDIA_ROOT.joinpath(path).resolve()

    # If the asset file is the *same* filename as the one being uploaded,
    # delete the original one from the media directory
    if str(filename) == str(instance.asset):
        if fullpath.exists():
            # Check for existing asset file with the same name
            logger.info("Deleting existing asset file: '%s'", filename)
            os.remove(fullpath)

    # Ensure the cache is deleted for this asset
    cache.delete(fullpath)

    return path


class ReportAsset(models.Model):
    """Asset file for use in report templates.

    For example, an image to use in a header file.
    Uploaded asset files appear in MEDIA_ROOT/report/assets,
    and can be loaded in a template using the {% report_asset <filename> %} tag.
    """

    def __str__(self):
        """String representation of a ReportAsset instance."""
        return f'assets/{self.filename}'

    @property
    def filename(self):
        """Return the filename of the asset."""
        path = self.asset.name
        if path:
            return os.path.basename(path)
        else:
            return '-'

    @staticmethod
    def asset_path(filename):
        """Return the fully-qualified asset path for the given filename."""
        return os.path.join('report', 'assets', os.path.basename(str(filename)))

    def validate_unique(self, exclude=None):
        """Validate that this report asset is unique."""
        proposed_path = self.asset_path(self.asset)

        if (
            ReportAsset.objects.filter(asset=proposed_path).exclude(pk=self.pk).count()
            > 0
        ):
            raise ValidationError({
                'asset': _('Asset file with this name already exists')
            })

        return super().validate_unique(exclude)

    # Asset file
    asset = models.FileField(
        upload_to=rename_asset,
        verbose_name=_('Asset'),
        help_text=_('Report asset file'),
    )

    # Asset description (user facing string, not used internally)
    description = models.CharField(
        max_length=250,
        verbose_name=_('Description'),
        help_text=_('Asset file description'),
    )
