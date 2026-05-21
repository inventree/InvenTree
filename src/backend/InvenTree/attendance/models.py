"""Database models for the attendance / time-tracking app."""

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class ClockEntry(models.Model):
    """Records a clock-in / clock-out session for a user."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='clock_entries',
        verbose_name=_('User'),
    )

    clock_in = models.DateTimeField(verbose_name=_('Clock In'))

    clock_out = models.DateTimeField(null=True, blank=True, verbose_name=_('Clock Out'))

    location = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Location'),
        help_text=_('Stand or area identifier'),
    )

    notes = models.TextField(blank=True, verbose_name=_('Notes'))

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Model metadata for ClockEntry."""

        verbose_name = _('Clock Entry')
        verbose_name_plural = _('Clock Entries')
        ordering = ['-clock_in']

    def __str__(self):
        """Return string representation."""
        return f'{self.user.username} — {self.clock_in}'

    @property
    def is_clocked_in(self):
        """True when this entry is still open (no clock_out)."""
        return self.clock_in is not None and self.clock_out is None

    @property
    def duration(self):
        """Elapsed time for this entry."""
        if self.clock_out:
            return self.clock_out - self.clock_in
        return timezone.now() - self.clock_in


class Shift(models.Model):
    """Defines a recurring work-shift template."""

    name = models.CharField(max_length=100, verbose_name=_('Name'))

    start_time = models.TimeField(verbose_name=_('Start Time'))

    end_time = models.TimeField(verbose_name=_('End Time'))

    days_of_week = models.JSONField(
        default=list,
        verbose_name=_('Days of Week'),
        help_text=_('List of day indices (0=Mon, …, 6=Sun)'),
    )

    active = models.BooleanField(default=True, verbose_name=_('Active'))

    class Meta:
        """Model metadata for Shift."""

        verbose_name = _('Shift')
        verbose_name_plural = _('Shifts')

    def __str__(self):
        """Return string representation."""
        return self.name


class ShiftAssignment(models.Model):
    """Links a user to a shift for a date range."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shift_assignments',
        verbose_name=_('User'),
    )

    shift = models.ForeignKey(
        Shift,
        on_delete=models.CASCADE,
        related_name='assignments',
        verbose_name=_('Shift'),
    )

    start_date = models.DateField(verbose_name=_('Start Date'))

    end_date = models.DateField(null=True, blank=True, verbose_name=_('End Date'))

    class Meta:
        """Model metadata for ShiftAssignment."""

        verbose_name = _('Shift Assignment')
        verbose_name_plural = _('Shift Assignments')

    def __str__(self):
        """Return string representation."""
        return f'{self.user.username} — {self.shift.name}'
