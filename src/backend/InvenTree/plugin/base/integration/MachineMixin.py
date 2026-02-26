"""Plugin mixin for registering machine drivers."""

import structlog

from machine.machine_type import BaseDriver, BaseMachineType
from plugin import PluginMixinEnum

logger = structlog.get_logger('inventree')


class MachineDriverMixin:
    """Mixin class for registering machine driver types.

    This mixin class can be used to register custom machine types or drivers.

    get_machine_types:
        - Register a custom class of machine
        - Returns a list of BaseMachineType objects

    get_machine_drivers:
        - Register custom machine drivers for existing machine types
        - Returns a list of BaseDriver objects
    """

    class MixinMeta:
        """Meta class for MachineDriverMixin."""

        MIXIN_NAME = 'MachineDriver'

    def __init__(self):
        """Initialize the mixin and register it."""
        super().__init__()
        self.add_mixin(PluginMixinEnum.MACHINE, True, __class__)

    def get_machine_types(self) -> list[BaseMachineType]:
        """Register custom machine types."""
        return []

    def get_machine_drivers(self) -> list[BaseDriver]:
        """Register custom machine drivers."""
        return []
