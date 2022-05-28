"""Report template model definitions"""

import datetime
import logging
import os
import sys

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import FieldError, ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models
from django.template import Context, Template
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

import build.models
import common.models
import order.models
import part.models
import stock.models
from InvenTree.helpers import validateFilterString

try:
    from django_weasyprint import WeasyTemplateResponseMixin
except OSError as err:  # pragma: no cover
    print("OSError: {e}".format(e=err))
    print("You may require some further system packages to be installed.")
    sys.exit(1)


logger = logging.getLogger("inventree")


def rename_template(instance, filename):
    """Helper function for 'renaming' uploaded report files.

    Pass responsibility back to the calling class,
    to ensure that files are uploaded to the correct directory.
    """
    return instance.rename_file(filename)


def validate_stock_item_report_filters(filters):
    """Validate filter string against StockItem model"""
    return validateFilterString(filters, model=stock.models.StockItem)


def validate_part_report_filters(filters):
    """Validate filter string against Part model"""
    return validateFilterString(filters, model=part.models.Part)


def validate_build_report_filters(filters):
    """Validate filter string against Build model"""
    return validateFilterString(filters, model=build.models.Build)


def validate_purchase_order_filters(filters):
    """Validate filter string against PurchaseOrder model"""
    return validateFilterString(filters, model=order.models.PurchaseOrder)


def validate_sales_order_filters(filters):
    """Validate filter string against SalesOrder model"""
    return validateFilterString(filters, model=order.models.SalesOrder)


class WeasyprintReportMixin(WeasyTemplateResponseMixin):
    """Class for rendering a HTML template to a PDF."""

    pdf_filename = 'report.pdf'
    pdf_attachment = True

    def __init__(self, request, template, **kwargs):

        self.request = request
        self.template_name = template
        self.pdf_filename = kwargs.get('filename', 'report.pdf')


class ReportBase(models.Model):
    """Base class for uploading html templates"""

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):

        # Increment revision number
        self.revision += 1

        super().save()

    def __str__(self):
        return "{n} - {d}".format(n=self.name, d=self.description)

    @classmethod
    def getSubdir(cls):
        return ''

    def rename_file(self, filename):
        # Function for renaming uploaded file

        filename = os.path.basename(filename)

        path = os.path.join('report', 'report_template', self.getSubdir(), filename)

        fullpath = os.path.join(settings.MEDIA_ROOT, path)
        fullpath = os.path.abspath(fullpath)

        # If the report file is the *same* filename as the one being uploaded,
        # remove the original one from the media directory
        if str(filename) == str(self.template):

            if os.path.exists(fullpath):
                logger.info(f"Deleting existing report template: '{filename}'")
                os.remove(fullpath)

        # Ensure that the cache is cleared for this template!
        cache.delete(fullpath)

        return path

    @property
    def extension(self):
        return os.path.splitext(self.template.name)[1].lower()

    @property
    def template_name(self):
        """Returns the file system path to the template file.

        Required for passing the file to an external process
        """
        template = self.template.name
        template = template.replace('/', os.path.sep)
        template = template.replace('\\', os.path.sep)

        template = os.path.join(settings.MEDIA_ROOT, template)

        return template

    name = models.CharField(
        blank=False, max_length=100,
        verbose_name=_('Name'),
        help_text=_('Template name'),
    )

    template = models.FileField(
        upload_to=rename_template,
        verbose_name=_('Template'),
        help_text=_("Report template file"),
        validators=[FileExtensionValidator(allowed_extensions=['html', 'htm'])],
    )

    description = models.CharField(
        max_length=250,
        verbose_name=_('Description'),
        help_text=_("Report template description")
    )

    revision = models.PositiveIntegerField(
        default=1,
        verbose_name=_("Revision"),
        help_text=_("Report revision number (auto-increments)"),
        editable=False,
    )


class ReportTemplateBase(ReportBase):
    """Reporting template model.

    Able to be passed context data
    """

    # Pass a single top-level object to the report template
    object_to_print = None

    def get_context_data(self, request):
        """Supply context data to the template for rendering"""
        return {}

    def context(self, request):
        """All context to be passed to the renderer."""
        # Generate custom context data based on the particular report subclass
        context = self.get_context_data(request)

        context['base_url'] = common.models.InvenTreeSetting.get_setting('INVENTREE_BASE_URL')
        context['date'] = datetime.datetime.now().date()
        context['datetime'] = datetime.datetime.now()
        context['default_page_size'] = common.models.InvenTreeSetting.get_setting('REPORT_DEFAULT_PAGE_SIZE')
        context['report_description'] = self.description
        context['report_name'] = self.name
        context['report_revision'] = self.revision
        context['request'] = request
        context['user'] = request.user

        return context

    def generate_filename(self, request, **kwargs):
        """Generate a filename for this report"""
        template_string = Template(self.filename_pattern)

        ctx = self.context(request)

        context = Context(ctx)

        return template_string.render(context)

    def render_as_string(self, request, **kwargs):
        """Render the report to a HTML string.

        Useful for debug mode (viewing generated code)
        """
        return render_to_string(self.template_name, self.context(request), request)

    def render(self, request, **kwargs):
        """Render the template to a PDF file.

        Uses django-weasyprint plugin to render HTML template against Weasyprint
        """
        # TODO: Support custom filename generation!
        # filename = kwargs.get('filename', 'report.pdf')

        # Render HTML template to PDF
        wp = WeasyprintReportMixin(
            request,
            self.template_name,
            base_url=request.build_absolute_uri("/"),
            presentational_hints=True,
            filename=self.generate_filename(request),
            **kwargs)

        return wp.render_to_response(
            self.context(request),
            **kwargs)

    filename_pattern = models.CharField(
        default="report.pdf",
        verbose_name=_('Filename Pattern'),
        help_text=_('Pattern for generating report filenames'),
        max_length=100,
    )

    enabled = models.BooleanField(
        default=True,
        verbose_name=_('Enabled'),
        help_text=_('Report template is enabled'),
    )

    class Meta:
        abstract = True


class TestReport(ReportTemplateBase):
    """Render a TestReport against a StockItem object."""

    @staticmethod
    def get_api_url():
        return reverse('api-stockitem-testreport-list')

    @classmethod
    def getSubdir(cls):
        return 'test'

    filters = models.CharField(
        blank=True,
        max_length=250,
        verbose_name=_('Filters'),
        help_text=_("StockItem query filters (comma-separated list of key=value pairs)"),
        validators=[
            validate_stock_item_report_filters
        ]
    )

    include_installed = models.BooleanField(
        default=False,
        verbose_name=_('Include Installed Tests'),
        help_text=_('Include test results for stock items installed inside assembled item')
    )

    def matches_stock_item(self, item):
        """Test if this report template matches a given StockItem objects"""
        try:
            filters = validateFilterString(self.filters)
            items = stock.models.StockItem.objects.filter(**filters)
        except (ValidationError, FieldError):
            return False

        # Ensure the provided StockItem object matches the filters
        items = items.filter(pk=item.pk)

        return items.exists()

    def get_context_data(self, request):

        stock_item = self.object_to_print

        return {
            'stock_item': stock_item,
            'serial': stock_item.serial,
            'part': stock_item.part,
            'parameters': stock_item.part.parameters_map(),
            'results': stock_item.testResultMap(include_installed=self.include_installed),
            'result_list': stock_item.testResultList(include_installed=self.include_installed),
            'installed_items': stock_item.get_installed_items(cascade=True),
        }


class BuildReport(ReportTemplateBase):
    """Build order / work order report"""

    @staticmethod
    def get_api_url():
        return reverse('api-build-report-list')

    @classmethod
    def getSubdir(cls):
        return 'build'

    filters = models.CharField(
        blank=True,
        max_length=250,
        verbose_name=_('Build Filters'),
        help_text=_('Build query filters (comma-separated list of key=value pairs'),
        validators=[
            validate_build_report_filters,
        ]
    )

    def get_context_data(self, request):
        """Custom context data for the build report"""
        my_build = self.object_to_print

        if type(my_build) != build.models.Build:
            raise TypeError('Provided model is not a Build object')

        return {
            'build': my_build,
            'part': my_build.part,
            'bom_items': my_build.part.get_bom_items(),
            'reference': my_build.reference,
            'quantity': my_build.quantity,
            'title': str(my_build),
        }


class BillOfMaterialsReport(ReportTemplateBase):
    """Render a Bill of Materials against a Part object"""

    @staticmethod
    def get_api_url():
        return reverse('api-bom-report-list')

    @classmethod
    def getSubdir(cls):
        return 'bom'

    filters = models.CharField(
        blank=True,
        max_length=250,
        verbose_name=_('Part Filters'),
        help_text=_('Part query filters (comma-separated list of key=value pairs'),
        validators=[
            validate_part_report_filters
        ]
    )

    def get_context_data(self, request):

        part = self.object_to_print

        return {
            'part': part,
            'category': part.category,
            'bom_items': part.get_bom_items(),
        }


class PurchaseOrderReport(ReportTemplateBase):
    """Render a report against a PurchaseOrder object"""

    @staticmethod
    def get_api_url():
        return reverse('api-po-report-list')

    @classmethod
    def getSubdir(cls):
        return 'purchaseorder'

    filters = models.CharField(
        blank=True,
        max_length=250,
        verbose_name=_('Filters'),
        help_text=_('Purchase order query filters'),
        validators=[
            validate_purchase_order_filters,
        ]
    )

    def get_context_data(self, request):

        order = self.object_to_print

        return {
            'description': order.description,
            'lines': order.lines,
            'extra_lines': order.extra_lines,
            'order': order,
            'reference': order.reference,
            'supplier': order.supplier,
            'prefix': common.models.InvenTreeSetting.get_setting('PURCHASEORDER_REFERENCE_PREFIX'),
            'title': str(order),
        }


class SalesOrderReport(ReportTemplateBase):
    """Render a report against a SalesOrder object"""

    @staticmethod
    def get_api_url():
        return reverse('api-so-report-list')

    @classmethod
    def getSubdir(cls):
        return 'salesorder'

    filters = models.CharField(
        blank=True,
        max_length=250,
        verbose_name=_('Filters'),
        help_text=_('Sales order query filters'),
        validators=[
            validate_sales_order_filters
        ]
    )

    def get_context_data(self, request):

        order = self.object_to_print

        return {
            'customer': order.customer,
            'description': order.description,
            'lines': order.lines,
            'extra_lines': order.extra_lines,
            'order': order,
            'prefix': common.models.InvenTreeSetting.get_setting('SALESORDER_REFERENCE_PREFIX'),
            'reference': order.reference,
            'title': str(order),
        }


def rename_snippet(instance, filename):

    filename = os.path.basename(filename)

    path = os.path.join('report', 'snippets', filename)

    fullpath = os.path.join(settings.MEDIA_ROOT, path)
    fullpath = os.path.abspath(fullpath)

    # If the snippet file is the *same* filename as the one being uploaded,
    # delete the original one from the media directory
    if str(filename) == str(instance.snippet):

        if os.path.exists(fullpath):
            logger.info(f"Deleting existing snippet file: '{filename}'")
            os.remove(fullpath)

    # Ensure that the cache is deleted for this snippet
    cache.delete(fullpath)

    return path


class ReportSnippet(models.Model):
    """Report template 'snippet' which can be used to make templates that can then be included in other reports.

    Useful for 'common' template actions, sub-templates, etc
    """

    snippet = models.FileField(
        upload_to=rename_snippet,
        verbose_name=_('Snippet'),
        help_text=_('Report snippet file'),
        validators=[FileExtensionValidator(allowed_extensions=['html', 'htm'])],
    )

    description = models.CharField(max_length=250, verbose_name=_('Description'), help_text=_("Snippet file description"))


def rename_asset(instance, filename):

    filename = os.path.basename(filename)

    path = os.path.join('report', 'assets', filename)

    # If the asset file is the *same* filename as the one being uploaded,
    # delete the original one from the media directory
    if str(filename) == str(instance.asset):
        fullpath = os.path.join(settings.MEDIA_ROOT, path)
        fullpath = os.path.abspath(fullpath)

        if os.path.exists(fullpath):
            logger.info(f"Deleting existing asset file: '{filename}'")
            os.remove(fullpath)

    return path


class ReportAsset(models.Model):
    """Asset file for use in report templates.

    For example, an image to use in a header file.
    Uploaded asset files appear in MEDIA_ROOT/report/assets,
    and can be loaded in a template using the {% report_asset <filename> %} tag.
    """

    def __str__(self):
        return os.path.basename(self.asset.name)

    asset = models.FileField(
        upload_to=rename_asset,
        verbose_name=_('Asset'),
        help_text=_("Report asset file"),
    )

    description = models.CharField(max_length=250, verbose_name=_('Description'), help_text=_("Asset file description"))
