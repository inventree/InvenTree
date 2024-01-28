import logging
from typing import Dict, List, Set, Type, Union
from uuid import UUID

from machine.machine_type import BaseDriver, BaseMachineType

logger = logging.getLogger('inventree')


class MachineRegistry:
    def __init__(self) -> None:
        """Initialize machine registry

        Set up all needed references for internal and external states.
        """
        self.machine_types: Dict[str, Type[BaseMachineType]] = {}
        self.drivers: Dict[str, Type[BaseDriver]] = {}
        self.driver_instances: Dict[str, BaseDriver] = {}
        self.machines: Dict[str, BaseMachineType] = {}

        self.base_drivers: List[Type[BaseDriver]] = []
        self.errors: list[Union[str, Exception]] = []

    def handle_error(self, error: Union[Exception, str]):
        """Helper function for capturing errors with the machine registry."""
        self.errors.append(error)

    def initialize(self):
        self.discover_machine_types()
        self.discover_drivers()
        self.load_machines()

    def discover_machine_types(self):
        import InvenTree.helpers

        logger.debug('Collecting machine types')

        machine_types: Dict[str, Type[BaseMachineType]] = {}
        base_drivers: List[Type[BaseDriver]] = []

        discovered_machine_types: Set[Type[BaseMachineType]] = (
            InvenTree.helpers.inheritors(BaseMachineType)
        )
        for machine_type in discovered_machine_types:
            try:
                machine_type.validate()
            except NotImplementedError as error:
                self.handle_error(error)
                continue

            if machine_type.SLUG in machine_types:
                self.handle_error(
                    ValueError(f"Cannot re-register machine type '{machine_type.SLUG}'")
                )
                continue

            machine_types[machine_type.SLUG] = machine_type
            base_drivers.append(machine_type.base_driver)

        self.machine_types = machine_types
        self.base_drivers = base_drivers

        logger.debug(f'Found {len(self.machine_types.keys())} machine types')

    def discover_drivers(self):
        import InvenTree.helpers

        logger.debug('Collecting machine drivers')

        drivers: Dict[str, Type[BaseDriver]] = {}

        discovered_drivers: Set[Type[BaseDriver]] = InvenTree.helpers.inheritors(
            BaseDriver
        )
        for driver in discovered_drivers:
            # skip discovered drivers that define a base driver for a machine type
            if driver in self.base_drivers:
                continue

            try:
                driver.validate()
            except NotImplementedError as error:
                self.handle_error(error)
                continue

            if driver.SLUG in drivers:
                self.handle_error(
                    ValueError(f"Cannot re-register driver '{driver.SLUG}'")
                )
                continue

            drivers[driver.SLUG] = driver

        self.drivers = drivers

        logger.debug(f'Found {len(self.drivers.keys())} machine drivers')

    def get_driver_instance(self, slug: str):
        if slug not in self.driver_instances:
            driver = self.drivers.get(slug, None)
            if driver is None:
                return None

            self.driver_instances[slug] = driver()

        return self.driver_instances.get(slug, None)

    def load_machines(self):
        # Imports need to be in this level to prevent early db model imports
        from machine.models import MachineConfig

        for machine_config in MachineConfig.objects.all():
            self.add_machine(machine_config, initialize=False)

        # initialize drivers
        for driver in self.driver_instances.values():
            driver.init_driver()

        # initialize machines after all machine instances were created
        for machine in self.machines.values():
            if machine.active:
                machine.initialize()

    def add_machine(self, machine_config, initialize=True):
        machine_type = self.machine_types.get(machine_config.machine_type, None)
        if machine_type is None:
            self.handle_error(f"Machine type '{machine_config.machine_type}' not found")
            return

        machine: BaseMachineType = machine_type(machine_config)
        self.machines[str(machine.pk)] = machine

        if initialize and machine.active:
            machine.initialize()

    def update_machine(self, old_machine_state, machine_config):
        if machine := machine_config.machine:
            machine.update(old_machine_state)

    def restart_machine(self, machine):
        machine.restart()

    def remove_machine(self, machine: BaseMachineType):
        self.machines.pop(str(machine.pk), None)

    def get_machines(self, **kwargs):
        """Get loaded machines from registry. (By default only initialized machines)

        Kwargs:
            name: Machine name
            machine_type: Machine type definition (class)
            driver: Machine driver (class)
            initialized: (bool, default: True)
            active: (bool)
            base_driver: base driver (class)
        """
        allowed_fields = [
            'name',
            'machine_type',
            'driver',
            'initialized',
            'active',
            'base_driver',
        ]

        kwargs = {'initialized': True, **kwargs}

        def filter_machine(machine: BaseMachineType):
            for key, value in kwargs.items():
                if key not in allowed_fields:
                    continue

                # check if current driver is subclass from base_driver
                if key == 'base_driver':
                    if machine.driver and not issubclass(
                        machine.driver.__class__, value
                    ):
                        return False

                # check if current machine is subclass from machine_type
                elif key == 'machine_type':
                    if issubclass(machine.__class__, value):
                        return False

                # check attributes of machine
                elif value != getattr(machine, key, None):
                    return False

            return True

        return list(filter(filter_machine, self.machines.values()))

    def get_machine(self, pk: Union[str, UUID]):
        """Get machine from registry by pk."""
        return self.machines.get(str(pk), None)


registry: MachineRegistry = MachineRegistry()
