from typing import TYPE_CHECKING, Any, Dict, List, Literal, Tuple, Type, Union

from generic.states import StatusCode
from InvenTree.helpers_mixin import ClassProviderMixin, ClassValidationMixin

# Import only for typechecking, otherwise this throws cyclic import errors
if TYPE_CHECKING:
    from common.models import SettingsKeyType
    from machine.models import MachineConfig
else:  # pragma: no cover

    class MachineConfig:
        pass

    class SettingsKeyType:
        pass


class MachineStatus(StatusCode):
    """Base class for representing a set of machine status codes.

    Use enum syntax to define the status codes, e.g.
    ```python
    CONNECTED = 200, _("Connected"), 'success'
    ```

    The values of the status can be accessed with `MachineStatus.CONNECTED.value`.

    Additionally there are helpers to access all additional attributes `text`, `label`, `color`.

    Status code ranges:
        1XX - Everything fine
        2XX - Warnings (e.g. ink is about to become empty)
        3XX - Something wrong with the machine (e.g. no labels are remaining on the spool)
        4XX - Something wrong with the driver (e.g. cannot connect to the machine)
        5XX - Unknown issues
    """

    pass


class BaseDriver(ClassValidationMixin, ClassProviderMixin):
    """Base class for machine drivers

    Attributes:
        SLUG: Slug string for identifying a machine
        NAME: User friendly name for displaying
        DESCRIPTION: Description of what this driver does

        MACHINE_SETTINGS: Driver specific settings dict (optional)
    """

    SLUG: str
    NAME: str
    DESCRIPTION: str

    MACHINE_SETTINGS: Dict[str, SettingsKeyType]

    machine_type: str

    required_attributes = ['SLUG', 'NAME', 'DESCRIPTION', 'machine_type']

    def init_driver(self):
        """This method gets called after all machines are created and can be used to initialize the driver.

        After the driver is initialized, the self.init_machine function is
        called for each machine associated with that driver.
        """
        pass

    def init_machine(self, machine: 'BaseMachineType'):
        """This method gets called for each active machine using that driver while initialization.

        If this function raises an Exception, it gets added to the machine.errors
        list and the machine does not initialize successfully.

        Arguments:
            machine: Machine instance
        """
        pass

    def update_machine(
        self, old_machine_state: Dict[str, Any], machine: 'BaseMachineType'
    ):
        """This method gets called for each update of a machine

        Note:
            machine.restart_required can be set to True here if the machine needs a manual restart to apply the changes

        Arguments:
            old_machine_state: Dict holding the old machine state before update
            machine: Machine instance with the new state
        """
        pass

    def restart_machine(self, machine: 'BaseMachineType'):
        """This method gets called on manual machine restart e.g. by using the restart machine action in the Admin Center.

        Note:
            machine.restart_required gets set to False again

        Arguments:
            machine: Machine instance
        """
        pass

    def get_machines(self, **kwargs):
        """Return all machines using this driver. (By default only initialized machines)"""
        from machine import registry

        return registry.get_machines(driver=self, **kwargs)


class BaseMachineType(ClassValidationMixin, ClassProviderMixin):
    """Base class for machine types

    Attributes:
        SLUG: Slug string for identifying a machine type
        NAME: User friendly name for displaying
        DESCRIPTION: Description of what this machine type can do (default: "")

        base_driver: Reference to the base driver for this machine type

        MACHINE_SETTINGS: Machine type specific settings dict (optional)

        MACHINE_STATUS: Set of status codes this machine type can have
        default_machine_status: Default machine status with which this machine gets initialized
    """

    SLUG: str
    NAME: str
    DESCRIPTION: str

    base_driver: Type[BaseDriver]

    MACHINE_SETTINGS: Dict[str, SettingsKeyType]

    MACHINE_STATUS: Type[MachineStatus]
    default_machine_status: MachineStatus

    # used by the ClassValidationMixin
    required_attributes = [
        'SLUG',
        'NAME',
        'DESCRIPTION',
        'base_driver',
        'MACHINE_STATUS',
        'default_machine_status',
    ]

    def __init__(self, machine_config: MachineConfig) -> None:
        from machine import registry
        from machine.models import MachineSetting

        self.errors = []
        self.initialized = False

        self.status = self.default_machine_status
        self.status_text = ''

        self.pk = machine_config.pk
        self.driver = registry.get_driver_instance(machine_config.driver)

        if not self.driver:
            self.handle_error(f"Driver '{machine_config.driver}' not found")
        if self.driver and not isinstance(self.driver, self.base_driver):
            self.handle_error(
                f"'{self.driver.NAME}' is incompatible with machine type '{self.NAME}'"
            )

        self.machine_settings: Dict[str, SettingsKeyType] = getattr(
            self, 'MACHINE_SETTINGS', {}
        )
        self.driver_settings: Dict[str, SettingsKeyType] = getattr(
            self.driver, 'MACHINE_SETTINGS', {}
        )

        self.setting_types: List[
            Tuple[Dict[str, SettingsKeyType], MachineSetting.ConfigType]
        ] = [
            (self.machine_settings, MachineSetting.ConfigType.MACHINE),
            (self.driver_settings, MachineSetting.ConfigType.DRIVER),
        ]

        self.restart_required = False

    def __str__(self):
        return f'{self.name}'

    # --- properties
    @property
    def machine_config(self):
        # always fetch the machine_config if needed to ensure we get the newest reference
        from .models import MachineConfig

        return MachineConfig.objects.get(pk=self.pk)

    @property
    def name(self):
        return self.machine_config.name

    @property
    def active(self):
        return self.machine_config.active

    # --- hook functions
    def initialize(self):
        """Machine initialization function, gets called after all machines are loaded"""
        if self.driver is None:
            return

        # check if all required settings are defined before continue with init process
        settings_valid, missing_settings = self.check_settings()
        if not settings_valid:
            error_parts = []
            for config_type, missing in missing_settings.items():
                if len(missing) > 0:
                    error_parts.append(
                        f'{config_type.name} settings: ' + ', '.join(missing)
                    )
            self.handle_error(f"Missing {' and '.join(error_parts)}")
            return

        try:
            self.driver.init_machine(self)
            self.initialized = True
        except Exception as e:
            self.handle_error(e)

    def update(self, old_state: dict[str, Any]):
        """Machine update function, gets called if the machine itself changes or their settings."""
        if self.driver is None:
            return

        try:
            self.driver.update_machine(old_state, self)
        except Exception as e:
            self.handle_error(e)

    def restart(self):
        """Machine restart function, can be used to manually restart the machine from the admin ui."""
        if self.driver is None:
            return

        try:
            self.restart_required = False
            self.driver.restart_machine(self)
        except Exception as e:
            self.handle_error(e)

    # --- helper functions
    def handle_error(self, error: Union[Exception, str]):
        """Helper function for capturing errors with the machine."""
        self.errors.append(error)

    def get_setting(self, key: str, config_type_str: Literal['M', 'D'], cache=False):
        """Return the 'value' of the setting associated with this machine.

        Arguments:
            key: The 'name' of the setting value to be retrieved
            config_type: Either "M" (machine scoped settings) or "D" (driver scoped settings)
            cache: Whether to use RAM cached value (default = False)
        """
        from machine.models import MachineSetting

        config_type = MachineSetting.get_config_type(config_type_str)
        return MachineSetting.get_setting(
            key,
            machine_config=self.machine_config,
            config_type=config_type,
            cache=cache,
        )

    def set_setting(self, key: str, config_type_str: Literal['M', 'D'], value):
        """Set plugin setting value by key.

        Arguments:
            key: The 'name' of the setting to set
            config_type: Either "M" (machine scoped settings) or "D" (driver scoped settings)
            value: The 'value' of the setting
        """
        from machine.models import MachineSetting

        config_type = MachineSetting.get_config_type(config_type_str)
        MachineSetting.set_setting(
            key,
            value,
            None,
            machine_config=self.machine_config,
            config_type=config_type,
        )

    def check_settings(self):
        """Check if all required settings for this machine are defined.

        Returns:
            is_valid: Are all required settings defined
            missing_settings: Dict[ConfigType, List[str]] of all settings that are missing (empty if is_valid is 'True')
        """
        from machine.models import MachineSetting

        missing_settings: Dict[MachineSetting.ConfigType, List[str]] = {}
        for settings, config_type in self.setting_types:
            is_valid, missing = MachineSetting.check_all_settings(
                settings_definition=settings,
                machine_config=self.machine_config,
                config_type=config_type,
            )
            missing_settings[config_type] = missing

        return all(
            len(missing) == 0 for missing in missing_settings.values()
        ), missing_settings

    def set_status(self, status: MachineStatus):
        """Set the machine status code. There are predefined ones for each MachineType.

        Import the MachineType to access it's `MACHINE_STATUS` enum.
        """
        self.status = status

    def set_status_text(self, status_text: str):
        """Set the machine status text. It can be any arbitrary text."""
        self.status_text = status_text
