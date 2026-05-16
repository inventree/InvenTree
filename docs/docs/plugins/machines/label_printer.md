---
title: Label Printer Machines
---

## Label Printer

Label printer machines can directly print labels for various items in InvenTree. They replace standard [`LabelPrintingMixin`](../mixins/label.md) plugins that are used to connect to physical printers. Using machines rather than a standard `LabelPrintingMixin` plugin has the advantage that machines can be created multiple times using different settings but the same driver. That way multiple label printers of the same brand can be connected.

### Writing A Custom Driver

To implement a custom label printer driver, you need to write a plugin which implements the [MachineDriverMixin](../mixins/machine.md) and returns a list of label printer drivers in the `get_machine_drivers` method.

Take a look at the most basic required code for a driver in this [example](./overview.md#example-driver). Next either implement the [`print_label`](#machine.machine_types.LabelPrinterBaseDriver.print_label) or [`print_labels`](#machine.machine_types.LabelPrinterBaseDriver.print_labels) function.

### Label Printer Status

There are a couple of predefined status codes for label printers. By default the `UNKNOWN` status code is set for each machine, but they can be changed at any time by the driver. For more info about status code see [Machine status codes](./overview.md#machine-status).

::: machine.machine_types.label_printer.LabelPrinterStatus
    options:
        heading_level: 4
        show_bases: false
        show_docstring_description: false

### LabelPrintingDriver API

::: machine.machine_types.LabelPrinterBaseDriver
    options:
        heading_level: 4
        show_bases: false
        members:
          - print_label
          - print_labels
          - get_printers
          - PrintingOptionsSerializer
          - get_printing_options_serializer
          - machine_plugin
          - render_to_pdf
          - render_to_pdf_data
          - render_to_html
          - render_to_png
