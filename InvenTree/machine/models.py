from typing import Any

from django.contrib import admin
from django.db import models
from django.utils.html import format_html_join
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

import common.models
from machine.registry import registry


class Machine(models.Model):
    """A Machine objects represents a physical machine."""

    name = models.CharField(
        unique=True,
        max_length=255,
        verbose_name=_("Name"),
        help_text=_("Name of machine")
    )

    machine_type_key = models.CharField(
        max_length=255,
        verbose_name=_("Machine Type"),
        help_text=_("Type of machine"),
    )

    driver_key = models.CharField(
        max_length=255,
        verbose_name=_("Driver"),
        help_text=_("Driver used for the machine")
    )

    active = models.BooleanField(
        default=True,
        verbose_name=_("Active"),
        help_text=_("Machines can be disabled")
    )

    def __str__(self) -> str:
        """String representation of a machine."""
        return f"{self.name}"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Override to set original state of the machine instance."""
        super().__init__(*args, **kwargs)

        self.errors = []
        self.initialized = False

        self.driver = registry.get_driver_instance(self.driver_key)
        self.machine_type = registry.machine_types.get(self.machine_type_key, None)

        if not self.driver:
            self.errors.append(f"Driver '{self.driver_key}' not found")
        if not self.machine_type:
            self.errors.append(f"Machine type '{self.machine_type_key}' not found")
        if self.machine_type and self.driver and not isinstance(self.driver, self.machine_type.base_driver):
            self.errors.append(f"'{self.driver.NAME}' is incompatible with machine type '{self.machine_type.NAME}'")

        if len(self.errors) > 0:
            return

        # TODO: add other init stuff here

    @admin.display(boolean=True, description=_("Driver available"))
    def is_driver_available(self) -> bool:
        """Status if driver for machine is available"""
        return self.driver is not None

    @admin.display(boolean=True, description=_("Machine has no errors"))
    def no_errors(self) -> bool:
        """Status if machine has errors"""
        return len(self.errors) == 0

    @admin.display(description=_("Errors"))
    def get_admin_errors(self):
        return format_html_join(mark_safe("<br>"), "{}", ((str(error),) for error in self.errors)) or mark_safe(f"<i>{_('No errors')}</i>")

    def initialize(self):
        """Machine initialization function, gets called after all machines are loaded"""
        if self.driver is None:
            return

        self.driver.init_machine(self)

        self.initialized = True

    def get_setting(self, key, cache=False):
        """Return the 'value' of the setting associated with this machine.

        Arguments:
            key: The 'name' of the setting value to be retrieved
            cache: Whether to use RAM cached value (default = False)
        """
        from machine.models import MachineSetting

        return MachineSetting.get_setting(key, machine=self, cache=cache)

    def set_setting(self, key, value):
        """Set plugin setting value by key.

        Arguments:
            key: The 'name' of the setting to set
            value: The 'value' of the setting
        """
        from machine.models import MachineSetting

        MachineSetting.set_setting(key, value, None, machine=self)


class MachineSetting(common.models.BaseInvenTreeSetting):
    """This models represents settings for individual machines."""

    typ = "machine"
    extra_unique_fields = ["machine"]

    class Meta:
        """Meta for MachineSetting."""
        unique_together = [
            ("machine", "key")
        ]

    machine = models.ForeignKey(
        Machine,
        related_name="settings",
        verbose_name=_("Machine"),
        on_delete=models.CASCADE
    )

    @classmethod
    def get_setting_definition(cls, key, **kwargs):
        """In the BaseInvenTreeSetting class, we have a class attribute named 'SETTINGS', which
        is a dict object that fully defines all the setting parameters.

        Here, unlike the BaseInvenTreeSetting, we do not know the definitions of all settings
        'ahead of time' (as they are defined externally in the machine).

        Settings can be provided by the caller, as kwargs['settings'].

        If not provided, we'll look at the machine registry to see what settings this machine requires
        """
        if 'settings' not in kwargs:
            machine: Machine = kwargs.pop('machine', None)
            if machine:
                kwargs['settings'] = getattr(machine.driver, "MACHINE_SETTINGS", {})

        return super().get_setting_definition(key, **kwargs)
