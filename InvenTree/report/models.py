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

    return os.path.join('report', 'template', filename)


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
