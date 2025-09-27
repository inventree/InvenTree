"""Machine app tests."""

from typing import cast

from django.apps import apps
from django.test import TestCase
from django.urls import reverse

from InvenTree.unit_test import AdminTestCase, InvenTreeAPITestCase
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
        plg_registry.reload_plugins()
        registry.initialize(main=True)

        super().setUp()

    def test_machine_lifecycle(self):
        """Test the machine lifecycle."""
        # Check initial conditions of the machine registry
        self.assertEqual(len(registry.get_machine_types()), 1)
        self.assertEqual(len(registry.get_driver_types()), 0)
        self.assertEqual(len(registry.get_machines()), 0)

        # Enable sample plugin
        plg_registry.set_plugin_state('sample-printer-machine-plugin', True)

        # Check state now
        self.assertEqual(len(registry.get_machine_types()), 1)
        self.assertEqual(len(registry.get_driver_types()), 1)
        self.assertEqual(len(registry.get_machines()), 0)

        # Enable test plugin
        plg_registry.set_plugin_state('label-printer-test-plugin', True)

        # Check state now
        self.assertEqual(len(registry.get_machine_types()), 1)
        self.assertEqual(len(registry.get_driver_types()), 3)
        self.assertEqual(len(registry.get_machines()), 0)

        # Check for expected machine registry errors
        self.assertEqual(len(registry.errors), 2)
        self.assertIn(
            "Cannot re-register driver 'test-label-printer-error'",
            str(registry.errors[0]),
        )
        self.assertIn(
            'did not override the required attributes', str(registry.errors[1])
        )

        # Check for expected machine types
        for slug in [
            'sample-printer-driver',
            'test-label-printer-api',
            'test-label-printer-error',
        ]:
            instance = registry.get_driver_instance(slug)
            self.assertIsNotNone(instance, f"Driver '{slug}' should be registered")

        # Next, un-register some plugins
        plg_registry.set_plugin_state('label-printer-test-plugin', False)

        self.assertEqual(len(registry.get_driver_types()), 1)
        self.assertEqual(len(registry.errors), 0)

        driver = registry.get_driver_types()[0]
        self.assertEqual(driver.SLUG, 'sample-printer-driver')

        # Create some new label printing machines
        machines = [
            MachineConfig.objects.create(
                name=f'Test Machine {i}',
                machine_type='label-printer',
                driver=driver.SLUG,
                active=i < 3,
            )
            for i in range(1, 4)
        ]

        self.assertEqual(MachineConfig.objects.count(), 3)

        # test that the registry is initialized correctly
        self.assertEqual(len(registry.machines), 3)
        self.assertEqual(len(registry.driver_instances), 1)

        # test get_machines
        self.assertEqual(len(registry.get_machines(initialized=None)), 3)
        self.assertEqual(len(registry.get_machines(active=True)), 2)
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
        machine = machines[0]
        self.assertEqual(registry.get_machine(machine.pk), machine.machine)

        # Test machine restart hook
        registry.restart_machine(machine.machine)

        # Assert properties have been set and correctly initialized with default values
        self.assertDictEqual(
            machine.machine.properties_dict,
            {
                'Model': {
                    'key': 'Model',
                    'value': 'Sample Printer 3000',
                    'type': 'str',
                    'group': '',
                    'max_progress': None,
                },
                'Battery': {
                    'key': 'Battery',
                    'value': 42,
                    'type': 'progress',
                    'group': '',
                    'max_progress': 100,
                },
            },
        )

        # Test remove machine
        self.assertEqual(len(registry.get_machines()), 2)
        registry.remove_machine(machine)
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

    def test_call_function(self):
        """Test arbitrary function calls against a machine."""
        from machine.registry import call_machine_function

        machine = self.create_machine()

        with self.assertRaises(AttributeError):
            call_machine_function(machine.pk, 'fake_function', custom_arg=123)

        result = call_machine_function(machine.pk, 'custom_func', x=3, y=4)

        self.assertEqual(result, 12)

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
        assert template

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
