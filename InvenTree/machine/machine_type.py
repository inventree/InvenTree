from typing import Dict


class BaseDriver:
    """Base class for machine drivers

    Attributes:
        SLUG: Slug string for identifying a machine
        NAME: User friendly name for displaying
        DESCRIPTION: Description of what this driver does (default: "")
    """

    SLUG: str
    NAME: str
    DESCRIPTION: str = ""

    # Import only for typechecking
    from typing import TYPE_CHECKING
    if TYPE_CHECKING:
        from machine.models import Machine
    else:  # pragma: no cover
        class Machine:
            pass

    # TODO: add better typing
    MACHINE_SETTINGS: Dict[str, dict]

    def init_machine(self, machine: Machine):
        """This method get called for each active machine using that driver while initialization

        Arguments:
            machine: Machine instance
        """
        pass

    def get_machines(self):
        """Return all machines using this driver."""
        from machine import registry

        return registry.get_machines(driver=self)


class BaseMachineType:
    """Base class for machine types

    Attributes:
        SLUG: Slug string for identifying a machine type
        NAME: User friendly name for displaying
        DESCRIPTION: Description of what this machine type can do (default: "")

        base_driver: Reference to the base driver for this machine type
    """

    SLUG: str
    NAME: str
    DESCRIPTION: str = ""

    base_driver: BaseDriver
