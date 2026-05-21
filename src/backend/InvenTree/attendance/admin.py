"""Admin registration for attendance models."""

from django.contrib import admin

from attendance.models import ClockEntry, Shift, ShiftAssignment


@admin.register(ClockEntry)
class ClockEntryAdmin(admin.ModelAdmin):
    """Admin view for ClockEntry."""

    list_display = ('user', 'clock_in', 'clock_out', 'location')
    search_fields = ('user__username', 'user__first_name', 'location')
    autocomplete_fields = ('user',)
    date_hierarchy = 'clock_in'


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    """Admin view for Shift."""

    list_display = ('name', 'start_time', 'end_time', 'active')


@admin.register(ShiftAssignment)
class ShiftAssignmentAdmin(admin.ModelAdmin):
    """Admin view for ShiftAssignment."""

    list_display = ('user', 'shift', 'start_date', 'end_date')
    autocomplete_fields = ('user',)
