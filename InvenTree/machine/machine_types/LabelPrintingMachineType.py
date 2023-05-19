from django.utils.translation import gettext_lazy as _

from machine.machine_type import BaseDriver, BaseMachineType


class BaseLabelPrintingDriver(BaseDriver):
    """Base label printing driver."""

    def print_label():
        """This function must be overriden."""
        raise NotImplementedError("The `print_label` function must be overriden!")

    def print_labels():
        """This function must be overriden."""
        raise NotImplementedError("The `print_labels` function must be overriden!")

    requires_override = [print_label]


class LabelPrintingMachineType(BaseMachineType):
    SLUG = "label_printer"
    NAME = _("Label Printer")
    DESCRIPTION = _("Device used to print labels")

    base_driver = BaseLabelPrintingDriver
