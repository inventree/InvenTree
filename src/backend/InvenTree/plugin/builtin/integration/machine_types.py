"""Base plugin which defines the built-in machine types."""

from django.utils.translation import gettext_lazy as _

from plugin import InvenTreePlugin
from plugin.machine import BaseDriver, BaseMachineType
from plugin.machine.machine_types import LabelPrinterMachine
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
        return [LabelPrinterMachine]

    def get_machine_drivers(self) -> list[BaseDriver]:
        """Return all built-in machine drivers."""
        return []
