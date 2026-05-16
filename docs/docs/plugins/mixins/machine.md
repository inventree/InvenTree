---
title: Machine Mixin
---

## MachineDriverMixin

The `MachineDriverMixin` class is used to implement custom machine drivers (or machine types) in InvenTree.

InvenTree supports integration with [external machines](../machines/overview.md), through the use of plugin-supplied device drivers.

### get_machine_drivers

To register custom machine driver(s), the `get_machine_drivers` method must be implemented. This method should return a list of machine driver classes that the plugin supports.

::: plugin.base.integration.MachineMixin.MachineDriverMixin.get_machine_drivers
    options:
      show_bases: False
      show_root_heading: False
      show_root_toc_entry: False
      summary: False
      members: []
      extra:
        show_source: True

The default implementation returns an empty list, meaning no custom machine drivers are registered.

### get_machine_types

To register custom machine type(s), the `get_machine_types` method must be implemented. This method should return a list of machine type classes that the plugin supports.

::: plugin.base.integration.MachineMixin.MachineDriverMixin.get_machine_types
    options:
      show_bases: False
      show_root_heading: False
      show_root_toc_entry: False
      summary: False
      members: []
      extra:
        show_source: True

The default implementation returns an empty list, meaning no custom machine types are registered.

## Sample Plugin

A sample plugin is provided which implements a simple [label printing](../machines/label_printer.md) machine driver:

::: plugin.samples.machines.sample_printer.SamplePrinterMachine
    options:
        show_bases: False
        show_root_heading: False
        show_root_toc_entry: False
        show_source: True
        members: []
