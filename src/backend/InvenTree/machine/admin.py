"""Django admin interface for the machine app."""

from django.contrib import admin
from django.http.request import HttpRequest

from machine import models


class MachineSettingInline(admin.TabularInline):
    """Inline admin class for MachineSetting."""

    model = models.MachineSetting

    read_only_fields = ['key', 'config_type']

    def has_add_permission(self, request, obj):
        """The machine settings should not be meddled with manually."""
        return False


@admin.register(models.MachineConfig)
class MachineConfigAdmin(admin.ModelAdmin):
    """Custom admin with restricted id fields."""

    list_filter = ['active']
    list_display = [
        'name',
        'machine_type',
        'driver',
        'initialized',
        'active',
        'no_errors',
        'get_machine_status',
    ]
    readonly_fields = [
        'initialized',
        'is_driver_available',
        'get_admin_errors',
        'get_machine_status',
    ]
    inlines = [MachineSettingInline]

    def get_readonly_fields(self, request, obj):
        """If update, don't allow changes on machine_type and driver."""
        if obj is not None:
            return ['machine_type', 'driver', *self.readonly_fields]

        return self.readonly_fields
