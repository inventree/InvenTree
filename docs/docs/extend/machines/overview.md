---
title: Machines
---

## Machines

InvenTree has a builtin machine registry. There are different machine types available where each type can have different drivers. Drivers and even custom machine types can be provided by plugins.

### Registry

The machine registry is the main component which gets initialized on server start and manages all configured machines.

#### Initialization process

The machine registry initialization process can be divided into three stages:

- **Stage 1: Discover machine types:** by looking for classes that inherit the BaseMachineType class
- **Stage 2: Discover drivers:** by looking for classes that inherit the BaseDriver class (and are not referenced as base driver for any discovered machine type)
- **Stage 3: Machine loading:**
    1. For each MachineConfig in database instantiate the MachineType class (drivers get instantiated here as needed and passed to the machine class. But only one instance of the driver class is maintained along the registry)
    2. The driver.init_driver function is called for each used driver
    3. The machine.initialize function is called for each machine, which calls the driver.init_machine function for each machine, then the machine.initialized state is set to true

### Machine types

Each machine type can provide a different type of connection functionality between inventree and a physical machine. These machine types are already built into InvenTree.

#### Built-in types

| Name | Description  |
| --- | --- |
| [Label printer](./label_printer.md) | Directly print labels for various items. |

#### Example machine type

If you want to create your own machine type, please also take a look at the already existing machine types in `machines/machine_types/*.py`. The following example creates a machine type called `abc`.

```py
from django.utils.translation import ugettext_lazy as _
from plugin.machine import BaseDriver, BaseMachineType, MachineStatus

class ABCBaseDriver(BaseDriver):
    """Base xyz driver."""

    machine_type = 'abc'

    def my_custom_required_method(self):
        """This function must be overridden."""
        raise NotImplementedError('The `my_custom_required_method` function must be overridden!')

    def my_custom_method(self):
        """This function can be overridden."""
        raise NotImplementedError('The `my_custom_method` function can be overridden!')

    required_overrides = [my_custom_required_method]

class ABCMachine(BaseMachineType):
    SLUG = 'abc'
    NAME = _('ABC')
    DESCRIPTION = _('This is an awesome machine type for ABC.')

    base_driver = ABCBaseDriver

    class ABCStatus(MachineStatus):
        CONNECTED = 100, _('Connected'), 'success'
        STANDBY = 101, _('Standby'), 'success'
        PRINTING = 110, _('Printing'), 'primary'

    MACHINE_STATUS = ABCStatus
    default_machine_status = ABCStatus.DISCONNECTED
```

#### Machine Type API

The machine type class gets instantiated for each machine on server startup and the reference is stored in the machine registry. (Therefore `machine.NAME` is the machine type name and `machine.name` links to the machine instances user defined name)

::: machine.BaseMachineType
    options:
        heading_level: 5
        show_bases: false
        members:
          - machine_config
          - name
          - active
          - initialize
          - update
          - restart
          - handle_error
          - get_setting
          - set_setting
          - check_setting
          - set_status
          - set_status_text

### Drivers

Drivers provide the connection layer between physical machines and inventree. There can be multiple drivers defined for the same machine type. Drivers are provided by plugins that are enabled and extend the corresponding base driver for the particular machine type. Each machine type already provides a base driver that needs to be inherited.

#### Example driver

A basic driver only needs to specify the basic attributes like `SLUG`, `NAME`, `DESCRIPTION`. The others are given by the used base driver, so take a look at [Machine types](#machine-types). The following example will create an driver called `abc` for the `xyz` machine type. The class will be discovered if it is provided by an **installed & activated** plugin just like this:

```py
from plugin import InvenTreePlugin
from plugin.machine.machine_types import ABCBaseDriver

class MyXyzAbcDriverPlugin(InvenTreePlugin):
    NAME = "XyzAbcDriver"
    SLUG = "xyz-driver"
    TITLE = "Xyz Abc Driver"
    # ...

class XYZDriver(ABCBaseDriver):
    SLUG = 'my-xyz-driver'
    NAME = 'My XYZ driver'
    DESCRIPTION = 'This is an awesome XYZ driver for a ABC machine'
```

#### Driver API

::: machine.BaseDriver
    options:
        heading_level: 5
        show_bases: false
        members:
          - init_driver
          - init_machine
          - update_machine
          - restart_machine
          - get_machines
          - handle_error

### Settings

Each machine can have different settings configured. There are machine settings that are specific to that machine type and driver settings that are specific to the driver, but both can be specified individually for each machine. Define them by adding a `MACHINE_SETTINGS` dictionary attribute to either the driver or the machine type. The format follows the same pattern as the `SETTINGS` for normal plugins documented on the [`SettingsMixin`](../plugins/settings.md)

```py
class MyXYZDriver(ABCBaseDriver):
    MACHINE_SETTINGS = {
        'SERVER': {
            'name': _('Server'),
            'description': _('IP/Hostname to connect to the cups server'),
            'default': 'localhost',
            'required': True,
        }
    }
```

Settings can even marked as `'required': True` which prevents the machine from starting if the setting is not defined.

### Machine status

Machine status can be used to report the machine status to the users. They can be set by the driver for each machine, but get lost on a server restart.

#### Codes

Each machine type has a set of status codes defined that can be set for each machine by the driver. There also needs to be a default status code defined.

```py
from plugin.machine import MachineStatus, BaseMachineType

class XYZStatus(MachineStatus):
    CONNECTED = 100, _('Connected'), 'success'
    STANDBY = 101, _('Standby'), 'success'
    DISCONNECTED = 400, _('Disconnected'), 'danger'

class XYZMachineType(BaseMachineType):
    # ...

    MACHINE_STATUS = XYZStatus
    default_machine_status = XYZStatus.DISCONNECTED
```

And to set a status code for a machine by the driver.

```py
class MyXYZDriver(ABCBaseDriver):
    # ...
    def init_machine(self, machine):
        # ... do some init stuff here
        machine.set_status(XYZMachineType.MACHINE_STATUS.CONNECTED)
```

**`MachineStatus` API**

::: machine.machine_type.MachineStatus
    options:
        heading_level: 5
        show_bases: false

#### Free text

There can also be a free text status code defined.

```py
class MyXYZDriver(ABCBaseDriver):
    # ...
    def init_machine(self, machine):
        # ... do some init stuff here
        machine.set_status_text("Paper missing")
```
