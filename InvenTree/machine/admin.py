from django import forms
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from machine import models
from machine.registry import registry


class MachineAdminForm(forms.ModelForm):
    def get_machine_type_choices():
        return [(machine_type.SLUG, machine_type.NAME) for machine_type in registry.machine_types.values()]

    def get_driver_choices():
        return [(driver.SLUG, driver.NAME) for driver in registry.drivers.values()]

    # TODO: add conditional choices like shown here
    # Ref: https://www.reddit.com/r/django/comments/18cj55/conditional_choices_for_model_field_based_on/
    # Ref: https://gist.github.com/blackrobot/4956070
    driver_key = forms.ChoiceField(label=_("Driver"), choices=get_driver_choices)
    machine_type_key = forms.ChoiceField(label=_("Machine Type"), choices=get_machine_type_choices)


class MachineSettingInline(admin.TabularInline):
    """Inline admin class for MachineSetting."""

    model = models.MachineSetting

    read_only_fields = [
        'key',
    ]

    def has_add_permission(self, request, obj):
        """The machine settings should not be meddled with manually."""
        return False


@admin.register(models.Machine)
class MachineAdmin(admin.ModelAdmin):
    """Custom admin with restricted id fields."""

    form = MachineAdminForm
    list_filter = ["active"]
    list_display = ["name", "machine_type_key", "driver_key", "active", "is_driver_available", "no_errors"]
    readonly_fields = ["is_driver_available", "get_admin_errors"]
    inlines = [MachineSettingInline]
