"""Machine app tests."""

from typing import cast
from unittest.mock import MagicMock, Mock

from django.apps import apps
from django.test import TestCase
from django.urls import reverse

from InvenTree.unit_test import AdminTestCase, InvenTreeAPITestCase
from machine.machine_type import BaseDriver, BaseMachineType, MachineStatus
from machine.models import MachineConfig
from machine.registry import registry
from part.models import Part
from plugin.models import PluginConfig
from plugin.registry import registry as plg_registry
from report.models import LabelTemplate


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
        registry.set_shared_state('errors', [])

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
        registry.initialize(main=True)

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
        self.assertEqual(len(registry.get_machines(initialized=None)), 3)
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
        CALL_COUNT = range(1, 5)  # Due to interplay between plugin and machine registry
        self.assertIn(self.driver_mocks['init_driver'].call_count, CALL_COUNT)
        self.assertIn(self.driver_mocks['init_machine'].call_count, CALL_COUNT)

        # Test machine restart hook
        registry.restart_machine(self.machine1.machine)

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


class TestLabelPrinterMachineType(InvenTreeAPITestCase):
    """Test the label printer machine type."""

    fixtures = ['category', 'part', 'location', 'stock']

    def test_registration(self):
        """Test that the machine is correctly registered from the plugin."""
        PLG_KEY = 'label-printer-test-plugin'
        DRIVER_KEY = 'test-label-printer-api'

        # Test that the machine is only available when the plugin is enabled
        for enabled in [False, True, False, True, False]:
            plg_registry.set_plugin_state(PLG_KEY, enabled)
            machine = registry.get_driver_instance(DRIVER_KEY)
            if enabled:
                self.assertIsNotNone(machine)
            else:
                self.assertIsNone(machine)

    def create_machine(self):
        """Create a new label printing machine."""
        registry.initialize(main=True)

        PLG_KEY = 'label-printer-test-plugin'
        DRIVER_KEY = 'test-label-printer-api'

        # Ensure that the driver is initialized
        plg_registry.set_plugin_state(PLG_KEY, True)

        driver = registry.get_driver_instance(DRIVER_KEY)
        self.assertIsNotNone(driver)

        machine_config = MachineConfig.objects.create(
            name='Test Label Printer',
            machine_type='label-printer',
            driver=DRIVER_KEY,
            active=True,
        )

        machine = registry.get_machine(machine_config.pk)
        self.assertIsNotNone(machine)
        self.assertIsNotNone(machine.base_driver)
        self.assertIsNotNone(machine.driver)

        return machine

    def test_print_label(self):
        """Test the print label method."""
        plugin_ref = 'inventreelabelmachine'

        machine = self.create_machine()

        # setup the label app
        apps.get_app_config('report').create_default_labels()  # type: ignore
        plg_registry.reload_plugins()

        config = cast(PluginConfig, plg_registry.get_plugin(plugin_ref).plugin_config())  # type: ignore
        config.active = True
        config.save()

        parts = Part.objects.all()[:2]
        template = LabelTemplate.objects.filter(enabled=True, model_type='part').first()

        url = reverse('api-label-print')

        with self.assertLogs('inventree', level='WARNING') as cm:
            self.post(
                url,
                {
                    'plugin': config.key,
                    'items': [a.pk for a in parts],
                    'template': template.pk,
                    'machine': str(machine.pk),
                    'driver_options': {'copies': '3', 'fake_option': 99},
                },
                expected_code=201,
            )

        # 4 entries for each printed label
        self.assertEqual(len(cm.output), 10)

        # Check for expected messages
        messages = [
            'Printing Label: TestingLabelPrinterDriver',
            f'machine: {machine.pk}',
            f'label: {template.pk}',
            f'item: {parts[0].pk}',
            f'item: {parts[1].pk}',
            'options: copies: 3',
        ]

        for message in messages:
            result = False
            for item in cm.records:
                if message in str(item):
                    result = True
                    break

            self.assertTrue(result, f'Message not found: {message}')

        # test with non existing machine
        response = self.post(
            url,
            {
                'plugin': config.key,
                'machine': 'dummy-uuid-which-does-not-exist',
                'driver_options': {'copies': '1', 'test_option': '2'},
                'items': [a.pk for a in parts],
                'template': template.pk,
            },
            expected_code=400,
        )

        self.assertIn('is not a valid choice', str(response.data['machine']))


class AdminTest(AdminTestCase):
    """Tests for the admin interface integration."""

    def test_admin(self):
        """Test the admin URL."""
        self.helper(model=MachineConfig)
