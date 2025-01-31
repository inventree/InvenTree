"""Base machine type/base driver."""

from typing import TYPE_CHECKING, Any, Literal, Union

from generic.states import StatusCode
from InvenTree.helpers_mixin import (
    ClassProviderMixin,
    ClassValidationMixin,
    get_shared_class_instance_state_mixin,
)

# Import only for typechecking, otherwise this throws cyclic import errors
if TYPE_CHECKING:
    from common.models import SettingsKeyType
    from machine.models import MachineConfig
else:  # pragma: no cover

    class MachineConfig:
        """Only used if not typechecking currently."""

    class SettingsKeyType:
        """Only used if not typechecking currently."""


class MachineStatus(StatusCode):
    """Base class for representing a set of machine status codes.

    Use enum syntax to define the status codes, e.g.
    ```python
    CONNECTED = 200, _("Connected"), 'success'
    ```

    The values of the status can be accessed with `MachineStatus.CONNECTED.value`.

    Additionally there are helpers to access all additional attributes `text`, `label`, `color`.

    Available colors:
        primary, secondary, warning, danger, success, warning, info

    Status code ranges:
        ```
        1XX - Everything fine
        2XX - Warnings (e.g. ink is about to become empty)
        3XX - Something wrong with the machine (e.g. no labels are remaining on the spool)
        4XX - Something wrong with the driver (e.g. cannot connect to the machine)
        5XX - Unknown issues
        ```
    """


class BaseDriver(
    ClassValidationMixin,
    ClassProviderMixin,
    get_shared_class_instance_state_mixin(lambda x: f'machine:driver:{x.SLUG}'),
):
    """Base class for all machine drivers.

    Attributes:
        SLUG: Slug string for identifying the driver in format /[a-z-]+/ (required)
        NAME: User friendly name for displaying (required)
        DESCRIPTION: Description of what this driver does (required)

        MACHINE_SETTINGS: Driver specific settings dict
    """

    SLUG: str
    NAME: str
    DESCRIPTION: str

    MACHINE_SETTINGS: dict[str, SettingsKeyType]

    machine_type: str

    required_attributes = ['SLUG', 'NAME', 'DESCRIPTION', 'machine_type']

    def __init__(self) -> None:
        """Base driver __init__ method."""
        super().__init__()

    def init_driver(self):
        """This method gets called after all machines are created and can be used to initialize the driver.

        After the driver is initialized, the self.init_machine function is
        called for each machine associated with that driver.
        """

    def init_machine(self, machine: 'BaseMachineType'):
        """This method gets called for each active machine using that driver while initialization.

        If this function raises an Exception, it gets added to the machine.errors
        list and the machine does not initialize successfully.

        Arguments:
            machine: Machine instance
        """

    def update_machine(
        self, old_machine_state: dict[str, Any], machine: 'BaseMachineType'
    ):
        """This method gets called for each update of a machine.

        Note:
            machine.restart_required can be set to True here if the machine needs a manual restart to apply the changes

        Arguments:
            old_machine_state: Dict holding the old machine state before update
            machine: Machine instance with the new state
        """

    def restart_machine(self, machine: 'BaseMachineType'):
        """This method gets called on manual machine restart e.g. by using the restart machine action in the Admin Center.

        Note:
            `machine.restart_required` gets set to False again before this function is called

        Arguments:
            machine: Machine instance
        """

    def get_machines(self, **kwargs):
        """Return all machines using this driver (By default only initialized machines).

        Keyword Arguments:
            name (str): Machine name
            machine_type (BaseMachineType): Machine type definition (class)
            initialized (bool | None): use None to get all machines (default: True)
            active (bool): machine needs to be active
            base_driver (BaseDriver): base driver (class)
        """
        from machine import registry

        kwargs.pop('driver', None)

        return registry.get_machines(driver=self, **kwargs)

    def handle_error(self, error: Union[Exception, str]):
        """Handle driver error.

        Arguments:
            error: Exception or string
        """
        self.set_shared_state('errors', [*self.errors, error])

    # --- state getters/setters
    @property
    def errors(self) -> list[Union[str, Exception]]:
        """List of driver errors."""
        return self.get_shared_state('errors', [])


class BaseMachineType(
    ClassValidationMixin,
    ClassProviderMixin,
    get_shared_class_instance_state_mixin(lambda x: f'machine:machine:{x.pk}'),
):
    """Base class for machine types.

    Attributes:
        SLUG: Slug string for identifying the machine type in format /[a-z-]+/ (required)
        NAME: User friendly name for displaying (required)
        DESCRIPTION: Description of what this machine type can do (required)

        base_driver: Reference to the base driver for this machine type

        MACHINE_SETTINGS: Machine type specific settings dict (optional)

        MACHINE_STATUS: Set of status codes this machine type can have
        default_machine_status: Default machine status with which this machine gets initialized
    """

    SLUG: str
    NAME: str
    DESCRIPTION: str

    base_driver: type[BaseDriver]

    MACHINE_SETTINGS: dict[str, SettingsKeyType]

    MACHINE_STATUS: type[MachineStatus]
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
        """Base machine type __init__ function."""
        from machine import registry
        from machine.models import MachineSetting

        self.pk = machine_config.pk
        self.driver = registry.get_driver_instance(machine_config.driver)

        if not self.driver:
            self.handle_error(f"Driver '{machine_config.driver}' not found")
        if self.driver and not isinstance(self.driver, self.base_driver):
            self.handle_error(
                f"'{self.driver.NAME}' is incompatible with machine type '{self.NAME}'"
            )

        self.machine_settings: dict[str, SettingsKeyType] = getattr(
            self, 'MACHINE_SETTINGS', {}
        )
        self.driver_settings: dict[str, SettingsKeyType] = getattr(
            self.driver, 'MACHINE_SETTINGS', {}
        )

        self.setting_types: list[
            tuple[dict[str, SettingsKeyType], MachineSetting.ConfigType]
        ] = [
            (self.machine_settings, MachineSetting.ConfigType.MACHINE),
            (self.driver_settings, MachineSetting.ConfigType.DRIVER),
        ]

    def __str__(self):
        """String representation of a machine."""
        return f'{self.name}'

    def __repr__(self):
        """Python representation of a machine."""
        return f'<{self.__class__.__name__}: {self.name}>'

    # --- properties
    @property
    def machine_config(self):
        """Machine_config property which is a reference to the database entry."""
        # always fetch the machine_config if needed to ensure we get the newest reference
        from .models import MachineConfig

        return MachineConfig.objects.get(pk=self.pk)

    @property
    def name(self):
        """The machines name."""
        return self.machine_config.name

    @property
    def active(self):
        """The machines active status."""
        return self.machine_config.active

    # --- hook functions
    def initialize(self):
        """Machine initialization function, gets called after all machines are loaded."""
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
            self.handle_error(f'Missing {" and ".join(error_parts)}')
            return

        try:
            self.driver.init_machine(self)
            self.initialized = True
        except Exception as e:
            self.handle_error(e)

    def update(self, old_state: dict[str, Any]):
        """Machine update function, gets called if the machine itself changes or their settings.

        Arguments:
            old_state: Dict holding the old machine state before update
        """
        if self.driver is None:
            return

        try:
            self.driver.update_machine(old_state, self)

            # check if the active state has changed and initialize the machine if necessary
            if old_state['active'] != self.active:
                if self.initialized is False and self.active is True:
                    self.initialize()
                elif self.initialized is True and self.active is False:
                    self.initialized = False
        except Exception as e:
            self.handle_error(e)

    def restart(self):
        """Machine restart function, can be used to manually restart the machine from the admin ui.

        This will first reset the machines state (errors, status, status_text) and then call the drivers restart function.
        """
        if self.driver is None:
            return

        try:
            # reset the machine state
            self.restart_required = False
            self.reset_errors()
            self.set_status(self.default_machine_status)
            self.set_status_text('')

            # call the driver restart function
            self.driver.restart_machine(self)
        except Exception as e:
            self.handle_error(e)

    # --- helper functions
    def handle_error(self, error: Union[Exception, str]):
        """Helper function for capturing errors with the machine.

        Arguments:
            error: Exception or string
        """
        self.set_shared_state('errors', [*self.errors, error])

    def reset_errors(self):
        """Helper function for resetting the error list for a machine."""
        self.set_shared_state('errors', [])

    def get_setting(
        self, key: str, config_type_str: Literal['M', 'D'], cache: bool = False
    ):
        """Return the 'value' of the setting associated with this machine.

        Arguments:
            key: The 'name' of the setting value to be retrieved
            config_type_str: Either "M" (machine scoped settings) or "D" (driver scoped settings)
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

    def set_setting(self, key: str, config_type_str: Literal['M', 'D'], value: Any):
        """Set plugin setting value by key.

        Arguments:
            key: The 'name' of the setting to set
            config_type_str: Either "M" (machine scoped settings) or "D" (driver scoped settings)
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
            missing_settings: dict[ConfigType, list[str]] of all settings that are missing (empty if is_valid is 'True')
        """
        from machine.models import MachineSetting

        missing_settings: dict[MachineSetting.ConfigType, list[str]] = {}
        for settings, config_type in self.setting_types:
            _nbr, missing = MachineSetting.check_all_settings(
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

        Arguments:
            status: The new MachineStatus code to set
        """
        self.set_shared_state('status', status.value)

    def set_status_text(self, status_text: str):
        """Set the machine status text. It can be any arbitrary text.

        Arguments:
            status_text: The new status text to set
        """
        self.set_shared_state('status_text', status_text)

    # --- state getters/setters
    @property
    def initialized(self) -> bool:
        """Initialized state of the machine."""
        return self.get_shared_state('initialized', False)

    @initialized.setter
    def initialized(self, value: bool):
        self.set_shared_state('initialized', value)

    @property
    def restart_required(self) -> bool:
        """Restart required state of the machine."""
        return self.get_shared_state('restart_required', False)

    @restart_required.setter
    def restart_required(self, value: bool):
        self.set_shared_state('restart_required', value)

    @property
    def errors(self) -> list[Union[str, Exception]]:
        """List of machine errors."""
        return self.get_shared_state('errors', [])

    @property
    def status(self) -> MachineStatus:
        """Machine status code."""
        status_code = self.get_shared_state('status', self.default_machine_status.value)
        return self.MACHINE_STATUS(status_code)

    @property
    def status_text(self) -> str:
        """Machine status text."""
        return self.get_shared_state('status_text', '')
