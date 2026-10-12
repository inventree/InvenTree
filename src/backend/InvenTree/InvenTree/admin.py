"""Admin classes."""

from django.contrib import admin
from django.utils import timezone

from allauth.usersessions.admin import UserSessionAdmin
from allauth.usersessions.models import UserSession
from django_q.admin import ScheduleAdmin
from django_q.models import Schedule
from djmoney.contrib.exchange.admin import RateAdmin
from djmoney.contrib.exchange.models import Rate

from common.admin_shared import NoAddAdminMixin, NoEditAdminMixin, ReadOnlyAdminMixin


class CustomRateAdmin(NoAddAdminMixin, RateAdmin):
    """Admin interface for the Rate class."""


admin.site.unregister(Rate)
admin.site.register(Rate, CustomRateAdmin)


def run_schedule_now(modeladmin, request, queryset):
    """Immediately queue the selected scheduled tasks for execution."""
    queryset.update(next_run=timezone.now())
    count = queryset.count()
    modeladmin.message_user(request, f'{count} task(s) queued for immediate execution.')


run_schedule_now.short_description = 'Run selected tasks now'


class ReadOnlyScheduleAdmin(ReadOnlyAdminMixin, ScheduleAdmin):
    """Read-only admin interface for django-q Schedule objects."""

    actions = [run_schedule_now]


admin.site.unregister(Schedule)
admin.site.register(Schedule, ReadOnlyScheduleAdmin)


class InvenTreeUserSessionAdmin(NoEditAdminMixin, UserSessionAdmin):
    """Admin interface for UserSession - view and delete only, no add or edit."""


admin.site.unregister(UserSession)
admin.site.register(UserSession, InvenTreeUserSessionAdmin)
