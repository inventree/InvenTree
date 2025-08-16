"""Plugins for testing label machines."""

import structlog

from machine.machine_type import BaseDriver
from plugin import InvenTreePlugin
from plugin.machine import BaseMachineType
from plugin.machine.machine_types import LabelPrinterBaseDriver
from plugin.mixins import MachineDriverMixin, SettingsMixin

logger = structlog.get_logger('inventree')


class TestingLabelPrinterDriver(LabelPrinterBaseDriver):
    """Test driver for label printing."""

    SLUG = 'test-label-printer-api'
    NAME = 'Test label printer'
    DESCRIPTION = 'This is a test label printer driver for testing.'

    MACHINE_SETTINGS = {
        'TEST_SETTING': {
            'name': 'Test setting',
            'description': 'This is a test setting',
        }
    }

    def restart_machine(self, machine: BaseMachineType):
        """Override restart_machine."""
        machine.set_status_text('Restarting...')

    def print_label(self, machine, label, item, **kwargs) -> None:
        """Override print_label."""
        # Simply output some warning messages,
        # which we can check for in the unit test
        logger.warn('Printing Label: TestingLabelPrinterDriver')
        logger.warn(f'machine: {machine.pk}')
        logger.warn(f'label: {label.pk}')
        logger.warn(f'item: {item.pk}')

        for k, v in kwargs['printing_options'].items():
            logger.warn(f'options: {k}: {v}')


class TestingLabelPrinterDriverError1(LabelPrinterBaseDriver):
    """Test driver for label printing."""

    SLUG = 'test-label-printer-error'
    NAME = 'Test label printer error'
    DESCRIPTION = 'This is a test label printer driver for testing.'

    def print_label(self, *args, **kwargs) -> None:
        """Override print_label."""


class TestingLabelPrinterDriverError2(LabelPrinterBaseDriver):
    """Test driver for label printing."""

    SLUG = 'test-label-printer-error'
    NAME = 'Test label printer error'
    DESCRIPTION = 'This is a test label printer driver for testing.'

    def print_label(self, *args, **kwargs) -> None:
        """Override print_label."""


class TestingLabelPrinterDriverNotImplemented(LabelPrinterBaseDriver):
    """Test driver for label printing."""

    SLUG = 'test-label-printer-not-implemented'
    NAME = 'Test label printer error not implemented'
    DESCRIPTION = 'This is a test label printer driver for testing.'


class LabelPrinterMachineTest(MachineDriverMixin, SettingsMixin, InvenTreePlugin):
    """A test plugin for label printer machines.

    This plugin registers multiple driver types for unit testing.
    """

    NAME = 'LabelPrinterMachineTest'
    SLUG = 'label-printer-test-plugin'
    TITLE = 'Test plugin for label printer machines'

    VERSION = '0.1'

    def get_machine_drivers(self) -> list[BaseDriver]:
        """Return a list of drivers registered by this plugin."""
        return [
            TestingLabelPrinterDriver,
            TestingLabelPrinterDriverError1,
            TestingLabelPrinterDriverError2,
            TestingLabelPrinterDriverNotImplemented,
        ]
