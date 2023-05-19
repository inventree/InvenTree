from typing import TYPE_CHECKING, Dict

# Import only for typechecking, otherwise this throws cyclic import errors
if TYPE_CHECKING:
    from common.models import SettingsKeyType
    from machine.models import Machine
else:  # pragma: no cover
    class Machine:
        pass

    class SettingsKeyType:
        pass


class BaseDriver:
    """Base class for machine drivers

    Attributes:
        SLUG: Slug string for identifying a machine
        NAME: User friendly name for displaying
        DESCRIPTION: Description of what this driver does (default: "")
    """

    SLUG: str
    NAME: str
    DESCRIPTION: str

    MACHINE_SETTINGS: Dict[str, SettingsKeyType]

    @classmethod
    def validate(cls):
        def attribute_missing(key):
            return not hasattr(cls, key) or getattr(cls, key) == ""

        def override_missing(base_implementation):
            return base_implementation == getattr(cls, base_implementation.__name__, None)

        missing_attributes = list(filter(attribute_missing, ["SLUG", "NAME", "DESCRIPTION"]))
        missing_overrides = list(filter(override_missing, getattr(cls, "requires_override", [])))

        errors = []

        if len(missing_attributes) > 0:
            errors.append(f"did not provide the following attributes: {', '.join(missing_attributes)}")
        if len(missing_overrides) > 0:
            errors.append(f"did not override the required attributes: {', '.join(map(lambda attr: attr.__name__, missing_overrides))}")

        if len(errors) > 0:
            raise NotImplementedError(f"The driver '{cls}' " + " and ".join(errors))

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
    DESCRIPTION: str

    base_driver: BaseDriver

    @classmethod
    def validate(cls):
        def attribute_missing(key):
            return not hasattr(cls, key) or getattr(cls, key) == ""

        missing_attributes = list(filter(attribute_missing, ["SLUG", "NAME", "DESCRIPTION", "base_driver"]))

        if len(missing_attributes) > 0:
            raise NotImplementedError(f"The machine type '{cls}' did not provide the following attributes: {', '.join(missing_attributes)}")
