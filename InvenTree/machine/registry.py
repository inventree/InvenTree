import logging
from typing import Dict, List

import InvenTree.helpers
from machine.driver import BaseDriver, BaseMachineType

logger = logging.getLogger('inventree')


class MachinesRegistry:
    def __init__(self) -> None:
        """Initialize machine registry

        Set up all needed references for internal and external states.
        """

        # Import only for typechecking
        from typing import TYPE_CHECKING
        if TYPE_CHECKING:
            from machine.models import Machine

        self.machine_types: Dict[str, BaseMachineType] = {}
        self.drivers: Dict[str, BaseDriver] = {}
        self.driver_instances: Dict[str, BaseDriver] = {}
        self.machines: Dict[str, Machine] = {}

        self.base_drivers: List[BaseDriver] = []

    def initialize(self):
        print("INITIALIZE")  # TODO: remove debug statement
        self.discover_machine_types()
        self.discover_drivers()
        self.load_machines()

    def discover_machine_types(self):
        logger.debug("Collecting machine types")

        machine_types: Dict[str, BaseMachineType] = {}
        base_drivers: List[BaseDriver] = []

        discovered_machine_types: List[BaseMachineType] = InvenTree.helpers.inheritors(BaseMachineType)
        for machine_type in discovered_machine_types:
            machine_types[machine_type.SLUG] = machine_type
            base_drivers.append(machine_type.base_driver)

        self.machine_types = machine_types
        self.base_drivers = base_drivers

        logger.debug(f"Found {len(self.machine_types.keys())} machine types")

    def discover_drivers(self):
        logger.debug("Collecting machine drivers")

        drivers: Dict[str, BaseDriver] = {}

        discovered_drivers: List[BaseDriver] = InvenTree.helpers.inheritors(BaseDriver)
        for driver in discovered_drivers:
            # skip discovered drivers that define a base driver for a machine type
            if driver in self.base_drivers:
                continue

            drivers[driver.SLUG] = driver

        self.drivers = drivers

        logger.debug(f"Found {len(self.drivers.keys())} machine drivers")

    def get_driver_instance(self, slug: str):
        if slug not in self.driver_instances:
            driver = self.drivers.get(slug, None)
            if driver is None:
                return None

            self.driver_instances[slug] = driver()

        return self.driver_instances.get(slug, None)

    def load_machines(self):
        # Imports need to be in this level to prevent early db model imports
        from machine.models import Machine

        for machine in Machine.objects.all():
            self.machines[machine.name] = machine

        # initialize machines after all machine instances were created
        for machine in self.machines.values():
            machine.initialize()

    def get_machines(self, machine_type):
        # TODO: implement function
        pass


registry: MachinesRegistry = MachinesRegistry()
