from django.utils.translation import gettext_lazy as _

from machine.machine_type import BaseDriver, BaseMachineType, MachineStatus


class BaseLabelPrintingDriver(BaseDriver):
    """Base label printing driver."""

    machine_type = 'label_printer'

    def print_label(self):
        """This function must be overridden."""
        raise NotImplementedError('The `print_label` function must be overridden!')

    def print_labels(self):
        """This function must be overridden."""
        raise NotImplementedError('The `print_labels` function must be overridden!')

    requires_override = [print_label]


class LabelPrintingMachineType(BaseMachineType):
    SLUG = 'label_printer'
    NAME = _('Label Printer')
    DESCRIPTION = _('Directly print labels for various items.')

    base_driver = BaseLabelPrintingDriver

    class LabelPrinterStatus(MachineStatus):
        CONNECTED = 100, _('Connected'), 'success'
        STANDBY = 101, _('Standby'), 'success'
        PRINTING = 110, _('Printing'), 'primary'
        LABEL_SPOOL_EMPTY = 301, _('Label spool empty'), 'warning'
        DISCONNECTED = 400, _('Disconnected'), 'danger'

    MACHINE_STATUS = LabelPrinterStatus

    default_machine_status = LabelPrinterStatus.DISCONNECTED
