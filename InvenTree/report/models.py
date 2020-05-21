"""
Report template model definitions
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os

from django.db import models
from django.core.validators import FileExtensionValidator

from django.utils.translation import gettext_lazy as _


def rename_template(instance, filename):

    filename = os.path.basename(filename)

    return os.path.join('report', 'report_template', filename)


class ReportTemplate(models.Model):
    """
    Reporting template model.
    """

    def __str__(self):
        return os.path.basename(self.template.name)

    template = models.FileField(
        upload_to=rename_template,
        help_text=_("Report template file"),
        validators=[FileExtensionValidator(allowed_extensions=['html', 'tex'])],
    )

    description = models.CharField(max_length=250, help_text=_("Report template description"))


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
