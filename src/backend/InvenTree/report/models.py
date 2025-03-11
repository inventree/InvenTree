"""Report template model definitions."""

import logging
import os
import sys

from django.conf import settings
from django.contrib.auth.models import AnonymousUser, User
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.validators import FileExtensionValidator, MinValueValidator
from django.db import models
from django.http import HttpRequest
from django.template import Context, Template
from django.template.exceptions import TemplateDoesNotExist
from django.template.loader import render_to_string
from django.test.client import RequestFactory
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

import InvenTree.exceptions
import InvenTree.helpers
import InvenTree.models
import report.helpers
import report.validators
from common.settings import get_global_setting
from InvenTree.helpers_model import get_base_url
from InvenTree.models import MetadataMixin
from plugin import InvenTreePlugin
from plugin.registry import registry

try:
    from django_weasyprint import WeasyTemplateResponseMixin
except OSError as err:  # pragma: no cover
    print(f'OSError: {err}')
    print("Unable to import 'django_weasyprint' module.")
    print('You may require some further system packages to be installed.')
    sys.exit(1)


logger = logging.getLogger('inventree')


def dummy_print_request() -> HttpRequest:
    """Generate a dummy HTTP request object.

    This is required for internal print calls, as WeasyPrint *requires* a request object.
    """
    factory = RequestFactory()
    request = factory.get('/')
    request.user = AnonymousUser()
    return request


class WeasyprintReport(WeasyTemplateResponseMixin):
    """Class for rendering a HTML template to a PDF."""

    def __init__(self, request, template, **kwargs):
        """Initialize the report mixin with some standard attributes."""
        self.request = request
        self.template_name = template
        self.pdf_filename = kwargs.get('filename', 'output.pdf')


def rename_template(instance, filename):
    """Function to rename a report template once uploaded.

    - Retains the original uploaded filename
    - Checks for duplicate filenames across instance class
    """
    path = instance.get_upload_path(filename)

    # Throw error if any other model instances reference this path
    instance.check_existing_file(path, raise_error=True)

    # Delete file with this name if it already exists
    if default_storage.exists(path):
        logger.info(f'Deleting existing template file: {path}')
        default_storage.delete(path)

    return path


class TemplateUploadMixin:
    """Mixin class for providing template path management functions.

    - Provides generic method for determining the upload path for a template
    - Provides generic method for checking for duplicate filenames

    Classes which inherit this mixin can guarantee that uploaded templates are unique,
    and that the same filename will be retained when uploaded.
    """

    # Directory in which to store uploaded templates
    SUBDIR = ''

    # Name of the template field
    TEMPLATE_FIELD = 'template'

    def __str__(self) -> str:
        """String representation of a TemplateUploadMixin instance."""
        return str(os.path.basename(self.template_name))

    @property
    def template_name(self):
        """Return the filename of the template associated with this model class."""
        template = getattr(self, self.TEMPLATE_FIELD).name
        template = template.replace('/', os.path.sep)
        template = template.replace('\\', os.path.sep)

        template = settings.MEDIA_ROOT.joinpath(template)

        return str(template)

    @property
    def extension(self):
        """Return the filename extension of the associated template file."""
        return os.path.splitext(self.template.name)[1].lower()

    def get_upload_path(self, filename):
        """Generate an upload path for the given filename."""
        fn = os.path.basename(filename)
        return os.path.join('report', self.SUBDIR, fn)

    def check_existing_file(self, path, raise_error=False):
        """Check if a file already exists with the given filename."""
        filters = {self.TEMPLATE_FIELD: self.get_upload_path(path)}

        exists = self.__class__.objects.filter(**filters).exclude(pk=self.pk).exists()

        if exists and raise_error:
            raise ValidationError({
                self.TEMPLATE_FIELD: _('Template file with this name already exists')
            })

        return exists

    def validate_unique(self, exclude=None):
        """Validate that this template is unique."""
        proposed_path = self.get_upload_path(self.template_name)
        self.check_existing_file(proposed_path, raise_error=True)
        return super().validate_unique(exclude)


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

    name = models.CharField(
        blank=False,
        max_length=100,
        verbose_name=_('Name'),
        help_text=_('Template name'),
    )

    description = models.CharField(
        max_length=250,
        verbose_name=_('Description'),
        help_text=_('Template description'),
    )

    revision = models.PositiveIntegerField(
        default=1,
        verbose_name=_('Revision'),
        help_text=_('Revision number (auto-increments)'),
        editable=False,
    )

    attach_to_model = models.BooleanField(
        default=False,
        verbose_name=_('Attach to Model on Print'),
        help_text=_(
            'Save report output as an attachment against linked model instance when printing'
        ),
    )

    def generate_filename(self, context, **kwargs):
        """Generate a filename for this report."""
        template_string = Template(self.filename_pattern)

        return template_string.render(Context(context))

    def render_as_string(self, instance, request=None, **kwargs):
        """Render the report to a HTML string.

        Useful for debug mode (viewing generated code)
        """
        context = self.get_context(instance, request, **kwargs)

        return render_to_string(self.template_name, context, request)

    def render(self, instance, request=None, **kwargs):
        """Render the template to a PDF file.

        Uses django-weasyprint plugin to render HTML template against Weasyprint
        """
        context = self.get_context(instance, request)

        # Render HTML template to PDF
        wp = WeasyprintReport(
            request,
            self.template_name,
            base_url=get_base_url(request=request),
            presentational_hints=True,
            filename=self.generate_filename(context),
            **kwargs,
        )

        return wp.render_to_response(context, **kwargs)

    filename_pattern = models.CharField(
        default='output.pdf',
        verbose_name=_('Filename Pattern'),
        help_text=_('Pattern for generating filenames'),
        max_length=100,
    )

    enabled = models.BooleanField(
        default=True, verbose_name=_('Enabled'), help_text=_('Template is enabled')
    )

    model_type = models.CharField(
        max_length=100,
        validators=[report.validators.validate_report_model_type],
        help_text=_('Target model type for template'),
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

    def base_context(self, request=None):
        """Return base context data (available to all templates)."""
        return {
            'base_url': get_base_url(request=request),
            'date': InvenTree.helpers.current_date(),
            'datetime': InvenTree.helpers.current_time(),
            'template': self,
            'template_description': self.description,
            'template_name': self.name,
            'template_revision': self.revision,
            'user': request.user if request else None,
        }

    def get_context(self, instance, request=None, **kwargs):
        """Supply context data to the generic template for rendering.

        Arguments:
            instance: The model instance we are printing against
            request: The request object (optional)
        """
        # Provide base context information to all templates
        base_context = self.base_context(request=request)

        # Add in an context information provided by the model instance itself
        context = {**base_context, **instance.report_context()}

        return context


class ReportTemplate(TemplateUploadMixin, ReportTemplateBase):
    """Class representing the ReportTemplate database model."""

    SUBDIR = 'report'
    TEMPLATE_FIELD = 'template'

    @staticmethod
    def get_api_url():
        """Return the API endpoint for the ReportTemplate model."""
        return reverse('api-report-template-list')

    def __init__(self, *args, **kwargs):
        """Initialize the particular report instance."""
        super().__init__(*args, **kwargs)

        self._meta.get_field(
            'page_size'
        ).choices = report.helpers.report_page_size_options()

    template = models.FileField(
        upload_to=rename_template,
        verbose_name=_('Template'),
        help_text=_('Template file'),
        validators=[FileExtensionValidator(allowed_extensions=['html', 'htm'])],
    )

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
            page_size_default = get_global_setting(
                'REPORT_DEFAULT_PAGE_SIZE', 'A4', create=False
            )
        except Exception:
            page_size_default = 'A4'

        page_size = self.page_size or page_size_default

        if self.landscape:
            page_size = page_size + ' landscape'

        return page_size

    def get_context(self, instance, request=None, **kwargs):
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

    def print(self, items: list, request=None, **kwargs) -> 'ReportOutput':
        """Print reports for a list of items against this template.

        Arguments:
            items: A list of items to print reports for (model instance)
            request: The request object (optional)

        Returns:
            output: The ReportOutput object representing the generated report(s)

        Raises:
            ValidationError: If there is an error during report printing

        Notes:
            Currently, all items are rendered separately into PDF files,
            and then combined into a single PDF file.

            Further work is required to allow the following extended features:
            - Render a single PDF file with the collated items (optional per template)
            - Render a raw file (do not convert to PDF) - allows for other file types
            - Render using background worker, provide progress updates to UI
            - Run report generation in the background worker process
        """
        outputs = []

        debug_mode = get_global_setting('REPORT_DEBUG_MODE', False)

        # Start with a default report name
        report_name = None

        if request is None:
            # Generate a dummy request object
            request = dummy_print_request()

        report_plugins = registry.with_mixin('report')

        try:
            for instance in items:
                context = self.get_context(instance, request)

                if report_name is None:
                    report_name = self.generate_filename(context)

                # Render the report output
                try:
                    if debug_mode:
                        output = self.render_as_string(instance, request)
                    else:
                        output = self.render(instance, request)
                except TemplateDoesNotExist as e:
                    t_name = str(e) or self.template
                    raise ValidationError(f'Template file {t_name} does not exist')

                outputs.append(output)

                # Attach the generated report to the model instance (if required)
                if self.attach_to_model and not debug_mode:
                    data = output.get_document().write_pdf()
                    instance.create_attachment(
                        attachment=ContentFile(data, report_name),
                        comment=_(f'Report generated from template {self.name}'),
                        upload_user=request.user
                        if request.user.is_authenticated
                        else None,
                    )

                # Provide generated report to any interested plugins
                for plugin in report_plugins:
                    try:
                        plugin.report_callback(self, instance, output, request)
                    except Exception:
                        InvenTree.exceptions.log_error(
                            f'plugins.{plugin.slug}.report_callback'
                        )
        except Exception as exc:
            # Something went wrong during the report generation process
            if get_global_setting('REPORT_LOG_ERRORS', backup_value=True):
                InvenTree.exceptions.log_error('report.print')

            raise ValidationError({
                'error': _('Error generating report'),
                'detail': str(exc),
                'path': request.path,
            })

        if not report_name.endswith('.pdf'):
            report_name += '.pdf'

        # Combine all the generated reports into a single PDF file
        if debug_mode:
            data = '\n'.join(outputs)
            report_name = report_name.replace('.pdf', '.html')
        else:
            pages = []

            try:
                for output in outputs:
                    doc = output.get_document()
                    for page in doc.pages:
                        pages.append(page)

                data = outputs[0].get_document().copy(pages).write_pdf()
            except TemplateDoesNotExist as exc:
                t_name = str(exc) or self.template
                raise ValidationError(f'Template file {t_name} does not exist')

        # Save the generated report to the database
        output = ReportOutput.objects.create(
            template=self,
            items=len(items),
            user=request.user if request.user.is_authenticated else None,
            progress=100,
            complete=True,
            output=ContentFile(data, report_name),
        )

        return output


class LabelTemplate(TemplateUploadMixin, ReportTemplateBase):
    """Class representing the LabelTemplate database model."""

    SUBDIR = 'label'
    TEMPLATE_FIELD = 'template'

    @staticmethod
    def get_api_url():
        """Return the API endpoint for the LabelTemplate model."""
        return reverse('api-label-template-list')

    template = models.FileField(
        upload_to=rename_template,
        verbose_name=_('Template'),
        help_text=_('Template file'),
        validators=[FileExtensionValidator(allowed_extensions=['html', 'htm'])],
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

    def get_context(self, instance, request=None, **kwargs):
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
            try:
                plugin.add_label_context(self, instance, request, context)
            except Exception:
                InvenTree.exceptions.log_error(
                    f'plugins.{plugin.slug}.add_label_context'
                )

        return context

    def print(
        self, items: list, plugin: InvenTreePlugin, options=None, request=None, **kwargs
    ) -> 'LabelOutput':
        """Print labels for a list of items against this template.

        Arguments:
            items: A list of items to print labels for (model instance)
            plugin: The plugin to use for label rendering
            options: Additional options for the label printing plugin (optional)
            request: The request object (optional)

        Returns:
            output: The LabelOutput object representing the generated label(s)

        Raises:
            ValidationError: If there is an error during label printing
        """
        output = LabelOutput.objects.create(
            template=self,
            items=len(items),
            plugin=plugin.slug,
            user=request.user if request else None,
            progress=0,
            complete=False,
        )

        if options is None:
            options = {}

        if request is None:
            # If the request object is not provided, we need to create a dummy one
            # Otherwise, WeasyPrint throws an error
            request = dummy_print_request()

        try:
            if hasattr(plugin, 'before_printing'):
                plugin.before_printing()

            plugin.print_labels(self, output, items, request, printing_options=options)

            if hasattr(plugin, 'after_printing'):
                plugin.after_printing()
        except ValidationError as e:
            output.delete()
            raise e
        except Exception as e:
            output.delete()
            InvenTree.exceptions.log_error(f'plugins.{plugin.slug}.print_labels')
            raise ValidationError([_('Error printing labels'), str(e)])

        output.complete = True
        output.save()

        # Return the output object
        return output


class TemplateOutput(models.Model):
    """Base class representing a generated file from a template.

    As reports (or labels) may take a long time to render,
    this process is offloaded to the background worker process.

    The result is either a file made available for download,
    or a message indicating that the output is handled externally.
    """

    class Meta:
        """Metaclass options."""

        abstract = True

    created = models.DateField(auto_now_add=True, editable=False)

    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, blank=True, null=True, related_name='+'
    )

    items = models.PositiveIntegerField(
        default=0, verbose_name=_('Items'), help_text=_('Number of items to process')
    )

    complete = models.BooleanField(
        default=False,
        verbose_name=_('Complete'),
        help_text=_('Report generation is complete'),
    )

    progress = models.PositiveIntegerField(
        default=0, verbose_name=_('Progress'), help_text=_('Report generation progress')
    )


class ReportOutput(TemplateOutput):
    """Class representing a generated report output file."""

    template = models.ForeignKey(
        ReportTemplate, on_delete=models.CASCADE, verbose_name=_('Report Template')
    )

    output = models.FileField(
        upload_to='report/output',
        blank=True,
        null=True,
        verbose_name=_('Output File'),
        help_text=_('Generated output file'),
    )


class LabelOutput(TemplateOutput):
    """Class representing a generated label output file."""

    plugin = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Plugin'),
        help_text=_('Label output plugin'),
    )

    template = models.ForeignKey(
        LabelTemplate, on_delete=models.CASCADE, verbose_name=_('Label Template')
    )

    output = models.FileField(
        upload_to='label/output',
        blank=True,
        null=True,
        verbose_name=_('Output File'),
        help_text=_('Generated output file'),
    )


class ReportSnippet(TemplateUploadMixin, models.Model):
    """Report template 'snippet' which can be used to make templates that can then be included in other reports.

    Useful for 'common' template actions, sub-templates, etc
    """

    SUBDIR = 'snippets'
    TEMPLATE_FIELD = 'snippet'

    snippet = models.FileField(
        upload_to=rename_template,
        verbose_name=_('Snippet'),
        help_text=_('Report snippet file'),
        validators=[FileExtensionValidator(allowed_extensions=['html', 'htm'])],
    )

    description = models.CharField(
        max_length=250,
        verbose_name=_('Description'),
        help_text=_('Snippet file description'),
    )


class ReportAsset(TemplateUploadMixin, models.Model):
    """Asset file for use in report templates.

    For example, an image to use in a header file.
    Uploaded asset files appear in MEDIA_ROOT/report/assets,
    and can be loaded in a template using the {% report_asset <filename> %} tag.
    """

    SUBDIR = 'assets'
    TEMPLATE_FIELD = 'asset'

    # Asset file
    asset = models.FileField(
        upload_to=rename_template,
        verbose_name=_('Asset'),
        help_text=_('Report asset file'),
    )

    # Asset description (user facing string, not used internally)
    description = models.CharField(
        max_length=250,
        verbose_name=_('Description'),
        help_text=_('Asset file description'),
    )
