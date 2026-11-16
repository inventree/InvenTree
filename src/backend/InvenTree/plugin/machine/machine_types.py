"""just re-export the machine types from the plugin InvenTree app."""

from machine.machine_types.label_printer import (
    LabelPrinterBaseDriver,
    LabelPrinterMachine,
)

__all__ = ['LabelPrinterBaseDriver', 'LabelPrinterMachine']
