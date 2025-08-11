"""Sample plugin for registering custom machines."""

from django.db import models

import structlog

from plugin import InvenTreePlugin
from plugin.machine import BaseMachineType
from plugin.machine.machine_types import LabelPrinterBaseDriver, LabelPrinterMachine
from plugin.mixins import SettingsMixin
from report.models import LabelTemplate

logger = structlog.get_logger('inventree')


class SamplePrinterMachine(SettingsMixin, InvenTreePlugin):
    """A very simple example of a 'printer' machine plugin.

    This plugin class simply prints a message to the logger.
    """

    NAME = 'SamplePrinterMachine'
    SLUG = 'sampleprinter'
    TITLE = 'Sample dummy plugin for printing labels'

    VERSION = '0.1'


class SamplePrinterDriver(LabelPrinterBaseDriver):
    """Sample printer driver."""

    SLUG = 'sample-printer'
    NAME = 'Sample Label Printer Driver'
    DESCRIPTION = 'Sample label printing driver for InvenTree'

    MACHINE_SETTINGS = {
        'CONNECTION': {
            'name': 'Connection String',
            'description': 'Custom string for connecting to the printer',
            'default': '123-xx123:8000',
        }
    }

    def init_machine(self, machine: BaseMachineType) -> None:
        """Machine initialization hook."""

    def print_label(
        self,
        machine: LabelPrinterMachine,
        label: LabelTemplate,
        item: models.Model,
        **kwargs,
    ) -> None:
        """Send the label to the printer."""
