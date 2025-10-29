"""Database model definitions for the 'web' app."""

import uuid

from django.contrib.auth.models import User
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

import structlog

import InvenTree.models

logger = structlog.get_logger('inventree')


class GuideDefinition(InvenTree.models.MetadataMixin):
    """Model that represents a guide definition."""

    class GuideType(models.TextChoices):
        """Enumeration for guide types."""

        Tipp = 'tipp', _('Tipp')
        FirstUseTipp = 'firstuse', _('First Use Tipp')
        FirstAdminGuide = 'firstadmin', _('First Admin Guide')
        Guide = 'guide', _('Guide')

    uid = models.CharField(
        max_length=255,
        verbose_name=_('Endpoint'),
        help_text=_('Unique uuid4 identifier for this guide definition'),
        default=uuid.uuid4,
        editable=False,
    )
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_('Name'),
        help_text=_('Name of the guide'),
    )
    slug = models.SlugField(
        max_length=100,
        unique=True,
        verbose_name=_('Slug'),
        help_text=_('URL-friendly unique identifier for the guide'),
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Description'),
        help_text=_('Optional description of the guide'),
    )
    guide_type = models.CharField(
        max_length=20,
        choices=GuideType.choices,
        verbose_name=_('Guide Type'),
        help_text=_('Type of the guide'),
    )
    data = models.JSONField(
        blank=True,
        null=True,
        verbose_name=_('Data'),
        help_text=_('JSON data field for storing extra information'),
    )

    def __str__(self):
        """String representation of the guide."""
        return f'{self.name} ({self.guide_type})'

    def save(self, *args, **kwargs):
        """Ensure required fields are set before saving."""
        if not self.guide_type:
            raise ValueError('guide_type must be set before saving GuideDefinition')
        if not self.slug:
            self.slug = slugify(self.name)

        # TODO ensure guide type and slug can not be edited once created
        return super().save(*args, **kwargs)

    class Meta:
        """Meta options for the GuideDefinition model."""

        verbose_name = _('Guide Definition')
        verbose_name_plural = _('Guide Definitions')


class GuideExecution(InvenTree.models.MetadataMixin):
    """Model that represents a user specific execution of a guide."""

    uid = models.CharField(
        max_length=255,
        verbose_name=_('UID'),
        help_text=_('Unique identifier for this guide execution'),
        default=uuid.uuid4,
        editable=False,
    )
    guide = models.ForeignKey(
        GuideDefinition,
        on_delete=models.CASCADE,
        related_name='executions',
        verbose_name=_('Guide'),
        help_text=_('The guide definition associated with this execution'),
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='guide_executions',
        verbose_name=_('User'),
        help_text=_('The user who is executing the guide'),
    )
    started_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Started At'),
        help_text=_('Timestamp when the guide execution started'),
    )
    completed_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('Completed At'),
        help_text=_('Timestamp when the guide execution was completed'),
    )
    progres_data = models.JSONField(
        blank=True,
        null=True,
        verbose_name=_('Progress'),
        help_text=_('JSON field to track progress of the guide execution'),
    )
    done = models.BooleanField(
        default=False,
        verbose_name=_('Done'),
        help_text=_('Indicates whether the guide execution is completed'),
    )

    def __str__(self):
        """String representation of the guide execution."""
        return f'{self.guide.name} for {self.user.username}'

    class Meta:
        """Meta options for the GuideExecution model."""

        verbose_name = _('Guide Execution')
        verbose_name_plural = _('Guide Executions')
