from django.utils.translation import gettext_lazy as _

from machine.machine_type import BaseDriver, BaseMachineType, MachineStatus


class BaseLabelPrintingDriver(BaseDriver):
    """Base label printing driver."""

    machine_type = "label_printer"

    def print_label(self):
        """This function must be overridden."""
        raise NotImplementedError("The `print_label` function must be overridden!")

    def print_labels(self):
        """This function must be overridden."""
        raise NotImplementedError("The `print_labels` function must be overridden!")

    requires_override = [print_label]


class LabelPrintingMachineType(BaseMachineType):
    SLUG = "label_printer"
    NAME = _("Label Printer")
    DESCRIPTION = _("Device used to print labels")

    base_driver = BaseLabelPrintingDriver

    class MACHINE_STATUS(MachineStatus):
        CONNECTED = 100, _("Connected"), "success"
        PRINTING = 101, _("Printing"), "primary"
        PAPER_MISSING = 301, _("Paper missing"), "warning"
        DISCONNECTED = 400, _("Disconnected"), "danger"

    default_machine_status = MACHINE_STATUS.DISCONNECTED
