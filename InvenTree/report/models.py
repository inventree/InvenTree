"""
Report template model definitions
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os

from django.db import models
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError

from django.utils.translation import gettext_lazy as _

from part.models import Part

from django_tex.shortcuts import render_to_pdf
from django_weasyprint import WeasyTemplateResponseMixin


def rename_template(instance, filename):

    filename = os.path.basename(filename)

    return os.path.join('report', 'report_template', instance.getSubdir(), filename)


def validateFilterString(value):
    """
    Validate that a provided filter string looks like a list of comma-separated key=value pairs

    These should nominally match to a valid database filter based on the model being filtered.

    e.g. "category=6, IPN=12"
    e.g. "part__name=widget"

    The ReportTemplate class uses the filter string to work out which items a given report applies to.
    For example, an acceptance test report template might only apply to stock items with a given IPN,
    so the string could be set to:

    filters = "IPN = ACME0001"

    Returns a map of key:value pairs
    """

    # Empty results map
    results = {}

    value = str(value).strip()

    if not value or len(value) == 0:
        return results

    groups = value.split(',')

    for group in groups:
        group = group.strip()

        pair = group.split('=')

        if not len(pair) == 2:
            raise ValidationError(
                "Invalid group: {g}".format(g=group)
            )

        k, v = pair

        k = k.strip()
        v = v.strip()

        if not k or not v:
            raise ValidationError(
                "Invalid group: {g}".format(g=group)
            )

        results[k] = v

    return results


class WeasyprintReportMixin(WeasyTemplateResponseMixin):
    """
    Class for rendering a HTML template to a PDF.
    """

    pdf_filename = 'report.pdf'
    pdf_attachment = True

    def __init__(self, request, template, **kwargs):

        self.request = request
        self.template_name = template
        self.pdf_filename = kwargs.get('filename', 'report.pdf')


class ReportTemplateBase(models.Model):
    """
    Reporting template model.
    """

    def __str__(self):
        return os.path.basename(self.template.name)

    def getSubdir(self):
        return ''

    @property
    def extension(self):
        return os.path.splitext(self.template.name)[1].lower()

    @property
    def template_name(self):
        return os.path.join('report_template', self.getSubdir(), os.path.basename(self.template.name))

    def get_context_data(self, request):
        """
        Supply context data to the template for rendering
        """

        return {}

    def render(self, request, **kwargs):
        """
        Render the template to a PDF file.

        Supported template formats:
            .tex - Uses django-tex plugin to render LaTeX template against an installed LaTeX engine
            .html - Uses django-weasyprint plugin to render HTML template against Weasyprint
        """

        filename = kwargs.get('filename', 'report.pdf')

        context = self.get_context_data(request)

        context['request'] = request

        if self.extension == '.tex':
            # Render LaTeX template to PDF
            return render_to_pdf(request, self.template_name, context, filename=filename)
        elif self.extension in ['.htm', '.html']:
            # Render HTML template to PDF
            wp = WeasyprintReportMixin(request, self.template_name, **kwargs)
            return wp.render_to_response(context, **kwargs)

    name = models.CharField(
        blank=False, max_length=100,
        help_text=_('Template name'),
        unique=True,
    )

    template = models.FileField(
        upload_to=rename_template,
        help_text=_("Report template file"),
        validators=[FileExtensionValidator(allowed_extensions=['html', 'htm', 'tex'])],
    )

    description = models.CharField(max_length=250, help_text=_("Report template description"))

    class Meta:
        abstract = True


class ReportTemplate(ReportTemplateBase):
    """
    A simple reporting template which is used to upload template files,
    which can then be used in other concrete template classes.
    """

    pass


class PartFilterMixin(models.Model):
    """
    A model mixin used for matching a report type against a Part object.
    Used to assign a report to a given part using custom filters.
    """

    class Meta:
        abstract = True

    def matches_part(self, part):
        """
        Test if this report matches a given part.
        """

        filters = self.get_part_filters()

        parts = Part.objects.filter(**filters)

        parts = parts.filter(pk=part.pk)

        return parts.exists()


    def get_part_filters(self):
        """ Return a map of filters to be used for Part filtering """
        return validateFilterString(self.part_filters)

    part_filters = models.CharField(
        blank=True,
        max_length=250,
        help_text=_("Part query filters (comma-separated list of key=value pairs)"),
        validators=[validateFilterString]
    )


class TestReport(ReportTemplateBase, PartFilterMixin):
    """
    Render a TestReport against a StockItem object.
    """

    def getSubdir(self):
        return 'test'

    stock_item = None

    def get_context_data(self, request):
        return {
            'stock_item': self.stock_item,
            'results': self.stock_item.testResultMap()
        }


def rename_asset(instance, filename):

    filename = os.path.basename(filename)

    return os.path.join('report', 'assets', filename)


class ReportAsset(models.Model):
    """
    Asset file for use in report templates.
    For example, an image to use in a header file.
    Uploaded asset files appear in MEDIA_ROOT/report/assets,
    and can be loaded in a template using the {% report_asset <filename> %} tag.
    """

    def __str__(self):
        return os.path.basename(self.asset.name)

    asset = models.FileField(
        upload_to=rename_asset,
        help_text=_("Report asset file"),
    )

    description = models.CharField(max_length=250, help_text=_("Asset file description"))
