from typing import TYPE_CHECKING, Dict

# Import only for typechecking, otherwise this throws cyclic import errors
if TYPE_CHECKING:
    from common.models import SettingsKeyType
    from machine.models import MachineConfig
else:  # pragma: no cover
    class MachineConfig:
        pass

    class SettingsKeyType:
        pass


# TODO: move to better destination
class ClassValidationMixin:
    """Mixin to validate class attributes and overrides.

    Class attributes:
        required_attributes: List of class attributes that need to be defined
        required_overrides: List of functions that need override
    """

    required_attributes = []
    required_overrides = []

    @classmethod
    def validate(cls):
        def attribute_missing(key):
            return not hasattr(cls, key) or getattr(cls, key) == ""

        def override_missing(base_implementation):
            return base_implementation == getattr(cls, base_implementation.__name__, None)

        missing_attributes = list(filter(attribute_missing, cls.required_attributes))
        missing_overrides = list(filter(override_missing, cls.required_overrides))

        errors = []

        if len(missing_attributes) > 0:
            errors.append(f"did not provide the following attributes: {', '.join(missing_attributes)}")
        if len(missing_overrides) > 0:
            errors.append(f"did not override the required attributes: {', '.join(map(lambda attr: attr.__name__, missing_overrides))}")

        if len(errors) > 0:
            raise NotImplementedError(f"'{cls}' " + " and ".join(errors))


class BaseDriver(ClassValidationMixin):
    """Base class for machine drivers

    Attributes:
        SLUG: Slug string for identifying a machine
        NAME: User friendly name for displaying
        DESCRIPTION: Description of what this driver does

        MACHINE_SETTINGS: Settings dict (optional)
    """

    SLUG: str
    NAME: str
    DESCRIPTION: str

    MACHINE_SETTINGS: Dict[str, SettingsKeyType]

    def init_machine(self, machine: "BaseMachineType"):
        """This method get called for each active machine using that driver while initialization

        Arguments:
            machine: Machine instance
        """
        pass

    def get_machines(self, **kwargs):
        """Return all machines using this driver. (By default only active machines)"""
        from machine import registry

        return registry.get_machines(driver=self, **kwargs)


class BaseMachineType(ClassValidationMixin):
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

    # used by the ClassValidationMixin
    required_attributes = ["SLUG", "NAME", "DESCRIPTION", "base_driver"]

    def __init__(self, machine_config: MachineConfig) -> None:
        from machine import registry

        self.errors = []
        self.initialized = False

        self.machine_config = machine_config
        self.driver = registry.get_driver_instance(self.machine_config.driver_key)

        if not self.driver:
            self.errors.append(f"Driver '{self.machine_config.driver_key}' not found")
        if self.driver and not isinstance(self.driver, self.base_driver):
            self.errors.append(f"'{self.driver.NAME}' is incompatible with machine type '{self.NAME}'")

        if len(self.errors) > 0:
            return

        # TODO: add further init stuff here

    @property
    def pk(self):
        return self.machine_config.pk

    @property
    def name(self):
        return self.machine_config.name

    @property
    def active(self):
        return self.machine_config.active

    def initialize(self):
        """Machine initialization function, gets called after all machines are loaded"""
        if self.driver is None:
            return

        try:
            self.driver.init_machine(self)
            self.initialized = True
        except Exception as e:
            self.errors.append(e)

    def get_setting(self, key, cache=False):
        """Return the 'value' of the setting associated with this machine.

        Arguments:
            key: The 'name' of the setting value to be retrieved
            cache: Whether to use RAM cached value (default = False)
        """
        from machine.models import MachineSetting

        return MachineSetting.get_setting(key, machine_config=self.machine_config, cache=cache)

    def set_setting(self, key, value):
        """Set plugin setting value by key.

        Arguments:
            key: The 'name' of the setting to set
            value: The 'value' of the setting
        """
        from machine.models import MachineSetting

        MachineSetting.set_setting(key, value, None, machine_config=self.machine_config)
