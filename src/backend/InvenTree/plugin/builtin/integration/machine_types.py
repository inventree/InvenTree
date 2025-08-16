"""Base plugin which defines the built-in machine types."""

from django.utils.translation import gettext_lazy as _

from machine.machine_type import BaseDriver, BaseMachineType
from plugin import InvenTreePlugin
from plugin.mixins import MachineDriverMixin


class InvenTreeMachineTypes(MachineDriverMixin, InvenTreePlugin):
    """Plugin which provides built-in machine type definitions."""

    NAME = 'InvenTreeMachines'
    SLUG = 'inventree-machines'
    TITLE = _('InvenTree Machines')
    DESCRIPTION = _('Built-in machine types for InvenTree')
    AUTHOR = _('InvenTree contributors')
    VERSION = '1.0.0'

    def get_machine_types(self) -> list[BaseMachineType]:
        """Return all built-in machine types."""
        from machine.machine_types.label_printer import LabelPrinterMachine

        return [LabelPrinterMachine]

    def get_machine_drivers(self) -> list[BaseDriver]:
        """Return all built-in machine drivers."""
        return []
