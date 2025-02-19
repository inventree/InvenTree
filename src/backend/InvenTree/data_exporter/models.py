"""Data export model definitions."""

from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _


class ExportOutput(models.Model):
    """Model representing a data export session."""

    class Meta:
        """Meta class options."""

    created = models.DateTimeField(auto_now_add=True, editable=False)

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='export_sessions',
    )

    plugin = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Plugin'),
        help_text=_('Export plugin name'),
    )

    complete = models.BooleanField(
        verbose_name=_('Complete'), help_text=_('Data export is complete')
    )

    progress = models.PositiveIntegerField(
        default=0, verbose_name=_('Progress'), help_text=_('Export progress percentage')
    )

    output = models.FileField(
        upload_to='export/output',
        blank=True,
        null=True,
        verbose_name=_('Output File'),
        help_text=_('Generated output file'),
    )
