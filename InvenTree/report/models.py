"""
Report template model definitions
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os

from django.db import models
from django.core.validators import FileExtensionValidator

from django.utils.translation import gettext_lazy as _

from django_tex.shortcuts import render_to_pdf


def rename_template(instance, filename):

    filename = os.path.basename(filename)

    return os.path.join('report', 'report_template', filename)


class ReportTemplate(models.Model):
    """
    Reporting template model.
    """

    def __str__(self):
        return os.path.basename(self.template.name)

    @property
    def extension(self):
        return os.path.splitext(self.template.name)[1].lower()

    def render(self, request, context={}, **kwargs):
        """
        Render to template.
        """

        filename = kwargs.get('filename', 'report.pdf')

        template = os.path.join('report_template', os.path.basename(self.template.name))

        if 1 or self.extension == '.tex':
            return render_to_pdf(request, template, context, filename=filename)

    name = models.CharField(
        blank=False, max_length=100,
        help_text=_('Template name'),
        unique=True,
    )

    template = models.FileField(
        upload_to=rename_template,
        help_text=_("Report template file"),
        validators=[FileExtensionValidator(allowed_extensions=['html', 'tex'])],
    )

    description = models.CharField(max_length=250, help_text=_("Report template description"))

    filters = models.CharField(
        blank=True,
        max_length=250,
        help_text=_("Query filters (comma-separated list of key=value pairs)"),
        validators=[validate_filter_string]
    )


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
