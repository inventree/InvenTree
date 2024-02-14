## Label printer

Label printer machines can directly print labels for various items in InvenTree. They replace standard [`LabelPrintingMixin`](../plugins/label.md) plugins that are used to connect to physical printers. Using machines rather than a standard `LabelPrintingMixin` plugin has the advantage that machines can be created multiple times using different settings but the same driver. That way multiple label printers of the same brand can be connected.

### Writing your own printing driver

Take a look at the most basic required code for a driver in this [example](./overview.md#example-driver). Next either implement the [`print_label`](#machine.machine_types.LabelPrinterBaseDriver.print_label) or [`print_labels`](#machine.machine_types.LabelPrinterBaseDriver.print_labels) function.

### Label printer status

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
