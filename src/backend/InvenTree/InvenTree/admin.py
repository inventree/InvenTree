"""Admin classes."""

from django.contrib import admin
from django.http.request import HttpRequest
from django.utils import timezone

from allauth.usersessions.admin import UserSessionAdmin
from allauth.usersessions.models import UserSession
from django_q.admin import ScheduleAdmin
from django_q.models import Schedule
from djmoney.contrib.exchange.admin import RateAdmin
from djmoney.contrib.exchange.models import Rate


class CustomRateAdmin(RateAdmin):
    """Admin interface for the Rate class."""

    def has_add_permission(self, request: HttpRequest) -> bool:
        """Disable the 'add' permission for Rate objects."""
        return False


admin.site.unregister(Rate)
admin.site.register(Rate, CustomRateAdmin)


def run_schedule_now(modeladmin, request, queryset):
    """Immediately queue the selected scheduled tasks for execution."""
    queryset.update(next_run=timezone.now())
    count = queryset.count()
    modeladmin.message_user(request, f'{count} task(s) queued for immediate execution.')


run_schedule_now.short_description = 'Run selected tasks now'


class ReadOnlyScheduleAdmin(ScheduleAdmin):
    """Read-only admin interface for django-q Schedule objects."""

    actions = [run_schedule_now]

    def has_add_permission(self, request: HttpRequest) -> bool:
        """Prevent adding new Schedule objects."""
        return False

    def has_change_permission(self, request: HttpRequest, obj=None) -> bool:
        """Prevent changing existing Schedule objects."""
        return False

    def has_delete_permission(self, request: HttpRequest, obj=None) -> bool:
        """Prevent deleting Schedule objects."""
        return False


admin.site.unregister(Schedule)
admin.site.register(Schedule, ReadOnlyScheduleAdmin)


class InvenTreeUserSessionAdmin(UserSessionAdmin):
    """Admin interface for UserSession - view and delete only, no add or edit."""

    def has_add_permission(self, request: HttpRequest) -> bool:
        """Prevent creating sessions via admin."""
        return False

    def has_change_permission(self, request: HttpRequest, obj=None) -> bool:
        """Prevent editing sessions via admin."""
        return False


admin.site.unregister(UserSession)
admin.site.register(UserSession, InvenTreeUserSessionAdmin)
