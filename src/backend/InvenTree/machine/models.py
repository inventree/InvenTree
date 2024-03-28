"""Models for the machine app."""

import uuid
from typing import Literal

from django.contrib import admin
from django.db import models
from django.utils.html import escape, format_html_join
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

import common.models
from machine import registry


class MachineConfig(models.Model):
    """A Machine objects represents a physical machine."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(
        unique=True,
        max_length=255,
        verbose_name=_('Name'),
        help_text=_('Name of machine'),
    )

    machine_type = models.CharField(
        max_length=255, verbose_name=_('Machine Type'), help_text=_('Type of machine')
    )

    driver = models.CharField(
        max_length=255,
        verbose_name=_('Driver'),
        help_text=_('Driver used for the machine'),
    )

    active = models.BooleanField(
        default=True, verbose_name=_('Active'), help_text=_('Machines can be disabled')
    )

    def __str__(self) -> str:
        """String representation of a machine."""
        return f'{self.name}'

    def save(self, *args, **kwargs) -> None:
        """Custom save function to capture creates/updates to notify the registry."""
        created = self._state.adding

        old_machine = None
        if (
            not created
            and self.pk
            and (old_machine := MachineConfig.objects.get(pk=self.pk))
        ):
            old_machine = old_machine.to_dict()

        super().save(*args, **kwargs)

        if created:
            # machine was created, add it to the machine registry
            registry.add_machine(self, initialize=True)
        elif old_machine:
            # machine was updated, invoke update hook
            # elif acts just as a type gate, old_machine should be defined always
            # if machine is not created now which is already handled above
            registry.update_machine(old_machine, self)

    def delete(self, *args, **kwargs):
        """Remove machine from registry first."""
        if self.machine:
            registry.remove_machine(self.machine)

        return super().delete(*args, **kwargs)

    def to_dict(self):
        """Serialize a machine config to a dict including setting."""
        machine = {f.name: f.value_to_string(self) for f in self._meta.fields}
        machine['settings'] = {
            (setting.config_type, setting.key): setting.value
            for setting in MachineSetting.objects.filter(machine_config=self)
        }
        return machine

    @property
    def machine(self):
        """Machine instance getter."""
        return registry.get_machine(self.pk)

    @property
    def errors(self):
        """Machine errors getter."""
        return getattr(self.machine, 'errors', [])

    @admin.display(boolean=True, description=_('Driver available'))
    def is_driver_available(self) -> bool:
        """Status if driver for machine is available."""
        return self.machine is not None and self.machine.driver is not None

    @admin.display(boolean=True, description=_('No errors'))
    def no_errors(self) -> bool:
        """Status if machine has errors."""
        return len(self.errors) == 0

    @admin.display(boolean=True, description=_('Initialized'))
    def initialized(self) -> bool:
        """Status if machine is initialized."""
        return getattr(self.machine, 'initialized', False)

    @admin.display(description=_('Errors'))
    def get_admin_errors(self):
        """Get machine errors for django admin interface."""
        return format_html_join(
            mark_safe('<br>'), '{}', ((str(error),) for error in self.errors)
        ) or mark_safe(f"<i>{_('No errors')}</i>")

    @admin.display(description=_('Machine status'))
    def get_machine_status(self):
        """Get machine status for django admin interface."""
        if self.machine is None:
            return None

        out = mark_safe(self.machine.status.render(self.machine.status))

        if self.machine.status_text:
            out += escape(f' ({self.machine.status_text})')

        return out


class MachineSetting(common.models.BaseInvenTreeSetting):
    """This models represents settings for individual machines."""

    typ = 'machine_config'
    extra_unique_fields = ['machine_config', 'config_type']

    class Meta:
        """Meta for MachineSetting."""

        unique_together = [('machine_config', 'config_type', 'key')]

    class ConfigType(models.TextChoices):
        """Machine setting config type enum."""

        MACHINE = 'M', _('Machine')
        DRIVER = 'D', _('Driver')

    machine_config = models.ForeignKey(
        MachineConfig,
        related_name='settings',
        verbose_name=_('Machine Config'),
        on_delete=models.CASCADE,
    )

    config_type = models.CharField(
        verbose_name=_('Config type'), max_length=1, choices=ConfigType.choices
    )

    def save(self, *args, **kwargs) -> None:
        """Custom save method to notify the registry on changes."""
        old_machine = self.machine_config.to_dict()

        super().save(*args, **kwargs)

        registry.update_machine(old_machine, self.machine_config)

    @classmethod
    def get_config_type(cls, config_type_str: Literal['M', 'D']):
        """Helper method to get the correct enum value for easier usage with literal strings."""
        if config_type_str == 'M':
            return cls.ConfigType.MACHINE
        elif config_type_str == 'D':
            return cls.ConfigType.DRIVER

    @classmethod
    def get_setting_definition(cls, key, **kwargs):
        """In the BaseInvenTreeSetting class, we have a class attribute named 'SETTINGS'.

        which is a dict object that fully defines all the setting parameters.

        Here, unlike the BaseInvenTreeSetting, we do not know the definitions of all settings
        'ahead of time' (as they are defined externally in the machine driver).

        Settings can be provided by the caller, as kwargs['settings'].

        If not provided, we'll look at the machine registry to see what settings this machine driver requires
        """
        if 'settings' not in kwargs:
            machine_config: MachineConfig = kwargs.pop('machine_config', None)
            if machine_config and machine_config.machine:
                config_type = kwargs.get('config_type', None)
                if config_type == cls.ConfigType.DRIVER:
                    kwargs['settings'] = machine_config.machine.driver_settings
                elif config_type == cls.ConfigType.MACHINE:
                    kwargs['settings'] = machine_config.machine.machine_settings

        return super().get_setting_definition(key, **kwargs)
