"""Admin classes."""

from django.contrib import admin
from django.http.request import HttpRequest

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


class ReadOnlyScheduleAdmin(ScheduleAdmin):
    """Read-only admin interface for django-q Schedule objects."""

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
