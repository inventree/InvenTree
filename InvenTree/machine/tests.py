"""Machine app tests."""

from typing import cast
from unittest.mock import MagicMock, Mock

from django.apps import apps
from django.test import TestCase
from django.urls import reverse

from rest_framework import serializers

from InvenTree.unit_test import InvenTreeAPITestCase
from label.models import PartLabel
from machine.machine_type import BaseDriver, BaseMachineType, MachineStatus
from machine.machine_types.label_printer import LabelPrinterBaseDriver
from machine.models import MachineConfig
from machine.registry import registry
from part.models import Part
from plugin.models import PluginConfig
from plugin.registry import registry as plg_registry


class TestMachineRegistryMixin(TestCase):
    """Machine registry test mixin to setup the registry between tests correctly."""

    placeholder_uuid = '00000000-0000-0000-0000-000000000000'

    def tearDown(self) -> None:
        """Clean up after testing."""
        registry.machine_types = {}
        registry.drivers = {}
        registry.driver_instances = {}
        registry.machines = {}
        registry.base_drivers = []
        registry.errors = []

        return super().tearDown()


class TestDriverMachineInterface(TestMachineRegistryMixin, TestCase):
    """Test the machine registry."""

    def setUp(self):
        """Setup some testing drivers/machines."""

        class TestingMachineBaseDriver(BaseDriver):
            """Test base driver for testing machines."""

            machine_type = 'testing-type'

        class TestingMachineType(BaseMachineType):
            """Test machine type for testing."""

            SLUG = 'testing-type'
            NAME = 'Testing machine type'
            DESCRIPTION = 'This is a test machine type for testing.'

            base_driver = TestingMachineBaseDriver

            class TestingMachineTypeStatus(MachineStatus):
                """Test machine status."""

                UNKNOWN = 100, 'Unknown', 'secondary'

            MACHINE_STATUS = TestingMachineTypeStatus
            default_machine_status = MACHINE_STATUS.UNKNOWN

        class TestingDriver(TestingMachineBaseDriver):
            """Test driver for testing machines."""

            SLUG = 'test-driver'
            NAME = 'Test Driver'
            DESCRIPTION = 'This is a test driver for testing.'

            MACHINE_SETTINGS = {
                'TEST_SETTING': {'name': 'Test Setting', 'description': 'Test setting'}
            }

        # mock driver implementation
        self.driver_mocks = {
            k: Mock()
            for k in [
                'init_driver',
                'init_machine',
                'update_machine',
                'restart_machine',
            ]
        }

        for key, value in self.driver_mocks.items():
            setattr(TestingDriver, key, value)

        self.machine1 = MachineConfig.objects.create(
            name='Test Machine 1',
            machine_type='testing-type',
            driver='test-driver',
            active=True,
        )
        self.machine2 = MachineConfig.objects.create(
            name='Test Machine 2',
            machine_type='testing-type',
            driver='test-driver',
            active=True,
        )
        self.machine3 = MachineConfig.objects.create(
            name='Test Machine 3',
            machine_type='testing-type',
            driver='test-driver',
            active=False,
        )
        self.machines = [self.machine1, self.machine2, self.machine3]

        # init registry
        registry.initialize()

        # mock machine implementation
        self.machine_mocks = {
            m: {k: MagicMock() for k in ['update', 'restart']} for m in self.machines
        }
        for machine_config, mock_dict in self.machine_mocks.items():
            for key, mock in mock_dict.items():
                mock.side_effect = getattr(machine_config.machine, key)
                setattr(machine_config.machine, key, mock)

        super().setUp()

    def test_machine_lifecycle(self):
        """Test the machine lifecycle."""
        # test that the registry is initialized correctly
        self.assertEqual(len(registry.machines), 3)
        self.assertEqual(len(registry.driver_instances), 1)

        # test get_machines
        self.assertEqual(len(registry.get_machines()), 2)
        self.assertEqual(len(registry.get_machines(active=False, initialized=False)), 1)
        self.assertEqual(len(registry.get_machines(name='Test Machine 1')), 1)
        self.assertEqual(
            len(registry.get_machines(name='Test Machine 1', active=False)), 0
        )
        self.assertEqual(
            len(registry.get_machines(name='Test Machine 1', active=True)), 1
        )

        # test get_machines with an unknown filter
        with self.assertRaisesMessage(
            ValueError,
            "'unknown_filter' is not a valid filter field for registry.get_machines.",
        ):
            registry.get_machines(unknown_filter='test')

        # test get_machine
        self.assertEqual(registry.get_machine(self.machine1.pk), self.machine1.machine)

        # test get_drivers
        self.assertEqual(len(registry.get_drivers('testing-type')), 1)
        self.assertEqual(registry.get_drivers('testing-type')[0].SLUG, 'test-driver')

        # test that init hooks where called correctly
        self.driver_mocks['init_driver'].assert_called_once()
        self.assertEqual(self.driver_mocks['init_machine'].call_count, 2)

        # Test machine restart hook
        registry.restart_machine(self.machine1.machine)
        self.driver_mocks['restart_machine'].assert_called_once_with(
            self.machine1.machine
        )
        self.assertEqual(self.machine_mocks[self.machine1]['restart'].call_count, 1)

        # Test machine update hook
        self.machine1.name = 'Test Machine 1 - Updated'
        self.machine1.save()
        self.driver_mocks['update_machine'].assert_called_once()
        self.assertEqual(self.machine_mocks[self.machine1]['update'].call_count, 1)
        old_machine_state, machine = self.driver_mocks['update_machine'].call_args.args
        self.assertEqual(old_machine_state['name'], 'Test Machine 1')
        self.assertEqual(machine.name, 'Test Machine 1 - Updated')
        self.assertEqual(self.machine1.machine, machine)
        self.machine_mocks[self.machine1]['update'].reset_mock()

        # get ref to machine 1
        machine1: BaseMachineType = self.machine1.machine  # type: ignore
        self.assertIsNotNone(machine1)

        # Test machine setting update hook
        self.assertEqual(machine1.get_setting('TEST_SETTING', 'D'), '')
        machine1.set_setting('TEST_SETTING', 'D', 'test-value')
        self.assertEqual(self.machine_mocks[self.machine1]['update'].call_count, 2)
        old_machine_state, machine = self.driver_mocks['update_machine'].call_args.args
        self.assertEqual(old_machine_state['settings']['D', 'TEST_SETTING'], '')
        self.assertEqual(machine1.get_setting('TEST_SETTING', 'D'), 'test-value')
        self.assertEqual(self.machine1.machine, machine)

        # Test remove machine
        self.assertEqual(len(registry.get_machines()), 2)
        registry.remove_machine(machine1)
        self.assertEqual(len(registry.get_machines()), 1)


class TestLabelPrinterMachineType(TestMachineRegistryMixin, InvenTreeAPITestCase):
    """Test the label printer machine type."""

    fixtures = ['category', 'part', 'location', 'stock']

    def setUp(self):
        """Setup the label printer machine type."""
        super().setUp()

        class TestingLabelPrinterDriver(LabelPrinterBaseDriver):
            """Label printer driver for testing."""

            SLUG = 'testing-label-printer'
            NAME = 'Testing Label Printer'
            DESCRIPTION = 'This is a test label printer driver for testing.'

            class PrintingOptionsSerializer(
                LabelPrinterBaseDriver.PrintingOptionsSerializer
            ):
                """Test printing options serializer."""

                test_option = serializers.IntegerField()

            def print_label(self, *args, **kwargs):
                """Mock print label method so that there are no errors."""

        self.machine = MachineConfig.objects.create(
            name='Test Label Printer',
            machine_type='label-printer',
            driver='testing-label-printer',
            active=True,
        )

        registry.initialize()
        driver_instance = cast(
            TestingLabelPrinterDriver,
            registry.get_driver_instance('testing-label-printer'),
        )

        self.print_label = Mock()
        driver_instance.print_label = self.print_label

        self.print_labels = Mock(side_effect=driver_instance.print_labels)
        driver_instance.print_labels = self.print_labels

    def test_print_label(self):
        """Test the print label method."""
        plugin_ref = 'inventreelabelmachine'

        # setup the label app
        apps.get_app_config('label').create_labels()  # type: ignore
        plg_registry.reload_plugins()
        config = cast(PluginConfig, plg_registry.get_plugin(plugin_ref).plugin_config())  # type: ignore
        config.active = True
        config.save()

        parts = Part.objects.all()[:2]
        label = cast(PartLabel, PartLabel.objects.first())

        url = reverse('api-part-label-print', kwargs={'pk': label.pk})
        url += f'/?plugin={plugin_ref}&part[]={parts[0].pk}&part[]={parts[1].pk}'

        self.post(
            url,
            {
                'machine': str(self.machine.pk),
                'driver_options': {'copies': '1', 'test_option': '2'},
            },
            expected_code=200,
        )

        # test the print labels method call
        self.print_labels.assert_called_once()
        self.assertEqual(self.print_labels.call_args.args[0], self.machine.machine)
        self.assertEqual(self.print_labels.call_args.args[1], label)
        self.assertQuerySetEqual(
            self.print_labels.call_args.args[2], parts, transform=lambda x: x
        )
        self.assertIn('printing_options', self.print_labels.call_args.kwargs)
        self.assertEqual(
            self.print_labels.call_args.kwargs['printing_options'],
            {'copies': 1, 'test_option': 2},
        )

        # test the single print label method calls
        self.assertEqual(self.print_label.call_count, 2)
        self.assertEqual(self.print_label.call_args.args[0], self.machine.machine)
        self.assertEqual(self.print_label.call_args.args[1], label)
        self.assertEqual(self.print_label.call_args.args[2], parts[1])
        self.assertIn('printing_options', self.print_labels.call_args.kwargs)
        self.assertEqual(
            self.print_labels.call_args.kwargs['printing_options'],
            {'copies': 1, 'test_option': 2},
        )

        # test with non existing machine
        self.post(
            url,
            {
                'machine': self.placeholder_uuid,
                'driver_options': {'copies': '1', 'test_option': '2'},
            },
            expected_code=400,
        )
