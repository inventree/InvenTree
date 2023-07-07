from django import forms
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from machine import models
from machine.registry import registry

# Note: Most of this code here is only for developing as there is no UI for machines *yet*.


class MachineConfigAdminForm(forms.ModelForm):
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
        'config_type'
    ]

    def get_extra(self, request, obj, **kwargs):
        if getattr(obj, 'machine', None) is not None:
            # TODO: improve this mechanism
            machine_settings = getattr(obj.machine, "MACHINE_SETTINGS", {})
            driver_settings = getattr(obj.machine.driver, "MACHINE_SETTINGS", {})
            count = len(machine_settings.keys()) + len(driver_settings.keys())
            if obj.settings.count() != count:
                return count
        return 0

    def has_add_permission(self, request, obj):
        """The machine settings should not be meddled with manually."""
        return True  # TODO: change back


@admin.register(models.MachineConfig)
class MachineConfigAdmin(admin.ModelAdmin):
    """Custom admin with restricted id fields."""

    form = MachineConfigAdminForm
    list_filter = ["active"]
    list_display = ["name", "machine_type_key", "driver_key", "active", "is_driver_available", "no_errors", "get_machine_status"]
    readonly_fields = ["is_driver_available", "get_admin_errors", "get_machine_status"]
    inlines = [MachineSettingInline]

    def get_readonly_fields(self, request, obj):
        # if update, don't allow changes on machine_type and driver
        if obj is not None:
            return ["machine_type_key", "driver_key", *self.readonly_fields]

        return self.readonly_fields

    def get_inline_formsets(self, request, formsets, inline_instances, obj):
        formsets = super().get_inline_formsets(request, formsets, inline_instances, obj)

        if getattr(obj, 'machine', None) is not None:
            machine_settings = getattr(obj.machine, "MACHINE_SETTINGS", {})
            driver_settings = getattr(obj.machine.driver, "MACHINE_SETTINGS", {})
            settings = [(s, models.MachineSetting.ConfigType.MACHINE) for s in machine_settings] + [(s, models.MachineSetting.ConfigType.DRIVER) for s in driver_settings]
            for form, (setting, typ) in zip(formsets[0].forms, settings):
                if form.fields["key"].initial is None:
                    form.fields["key"].initial = setting
                if form.fields["config_type"].initial is None:
                    form.fields["config_type"].initial = typ

        return formsets
