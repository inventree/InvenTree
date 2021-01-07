"""
Report template model definitions
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import sys

import datetime

from django.db import models
from django.conf import settings

from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError

import stock.models

from InvenTree.helpers import validateFilterString

from django.utils.translation import gettext_lazy as _

try:
    from django_weasyprint import WeasyTemplateResponseMixin
except OSError as err:
    print("OSError: {e}".format(e=err))
    print("You may require some further system packages to be installed.")
    sys.exit(1)

# Conditional import if LaTeX templating is enabled
if settings.LATEX_ENABLED:
    try:
        from django_tex.shortcuts import render_to_pdf
        from django_tex.core import render_template_with_context
        from django_tex.exceptions import TexError
    except OSError as err:
        print("OSError: {e}".format(e=err))
        print("You may not have a working LaTeX toolchain installed?")
        sys.exit(1)

from django.http import HttpResponse


class TexResponse(HttpResponse):
    def __init__(self, content, filename=None):
        super().__init__(content_type="application/txt")
        self["Content-Disposition"] = 'filename="{}"'.format(filename)
        self.write(content)


def rename_template(instance, filename):

    filename = os.path.basename(filename)

    return os.path.join('report', 'report_template', instance.getSubdir(), filename)


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
        return "{n} - {d}".format(n=self.name, d=self.description)

    def getSubdir(self):
        return ''

    @property
    def extension(self):
        return os.path.splitext(self.template.name)[1].lower()

    @property
    def template_name(self):
        """
        Returns the file system path to the template file.
        Required for passing the file to an external process (e.g. LaTeX)
        """

        template = os.path.join('report_template', self.getSubdir(), os.path.basename(self.template.name))
        template = template.replace('/', os.path.sep)
        template = template.replace('\\', os.path.sep)

        return template

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
        context['user'] = request.user
        context['datetime'] = datetime.datetime.now()

        if self.extension == '.tex':
            # Render LaTeX template to PDF
            if settings.LATEX_ENABLED:
                # Attempt to render to LaTeX template
                # If there is a rendering error, return the (partially rendered) template,
                # so at least we can debug what is going on
                try:
                    rendered = render_template_with_context(self.template_name, context)
                    return render_to_pdf(request, self.template_name, context, filename=filename)
                except TexError:
                    return TexResponse(rendered, filename="error.tex")
            else:
                raise ValidationError("Enable LaTeX support in config.yaml")
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

    enabled = models.BooleanField(
        default=True,
        help_text=_('Report template is enabled'),
        verbose_name=_('Enabled')
    )

    filters = models.CharField(
        blank=True,
        max_length=250,
        help_text=_("Part query filters (comma-separated list of key=value pairs)"),
        validators=[validateFilterString]
    )

    class Meta:
        abstract = True


class TestReport(ReportTemplateBase):
    """
    Render a TestReport against a StockItem object.
    """

    def getSubdir(self):
        return 'test'

    # Requires a stock_item object to be given to it before rendering
    stock_item = None

    def matches_stock_item(self, item):
        """
        Test if this report template matches a given StockItem objects
        """

        filters = validateFilterString(self.filters)

        items = stock.models.StockItem.objects.filter(**filters)

        # Ensure the provided StockItem object matches the filters
        items = items.filter(pk=item.pk)

        return items.exists()

    def get_context_data(self, request):
        return {
            'stock_item': self.stock_item,
            'part': self.stock_item.part,
            'results': self.stock_item.testResultMap(),
            'result_list': self.stock_item.testResultList()
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
