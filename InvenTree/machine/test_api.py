"""Machine API tests."""

import re
from typing import cast

from django.urls import reverse

from InvenTree.unit_test import InvenTreeAPITestCase
from machine import registry
from machine.machine_type import BaseDriver, BaseMachineType
from machine.machine_types import LabelPrinterBaseDriver
from machine.models import MachineConfig
from machine.tests import TestMachineRegistryMixin
from stock.models import StockLocation


class MachineAPITest(TestMachineRegistryMixin, InvenTreeAPITestCase):
    """Class for unit testing machine API endpoints."""

    roles = ['admin.add', 'admin.view', 'admin.change', 'admin.delete']

    placeholder_uuid = '00000000-0000-0000-0000-000000000000'

    def setUp(self):
        """Setup some testing drivers/machines."""

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

            def print_label(self, *args, **kwargs) -> None:
                """Override print_label."""

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

        registry.initialize()

        super().setUp()

    def test_machine_type_list(self):
        """Test machine types list API endpoint."""
        response = self.get(reverse('api-machine-types'))
        machine_type = [t for t in response.data if t['slug'] == 'label-printer']
        self.assertEqual(len(machine_type), 1)
        machine_type = machine_type[0]
        self.assertDictContainsSubset(
            {
                'slug': 'label-printer',
                'name': 'Label Printer',
                'description': 'Directly print labels for various items.',
                'provider_plugin': None,
                'is_builtin': True,
            },
            machine_type,
        )
        self.assertTrue(
            machine_type['provider_file'].endswith(
                'machine/machine_types/label_printer.py'
            )
        )

    def test_machine_driver_list(self):
        """Test machine driver list API endpoint."""
        response = self.get(reverse('api-machine-drivers'))
        driver = [a for a in response.data if a['slug'] == 'test-label-printer-api']
        self.assertEqual(len(driver), 1)
        driver = driver[0]
        self.assertDictContainsSubset(
            {
                'slug': 'test-label-printer-api',
                'name': 'Test label printer',
                'description': 'This is a test label printer driver for testing.',
                'provider_plugin': None,
                'is_builtin': True,
                'machine_type': 'label-printer',
                'driver_errors': [],
            },
            driver,
        )
        self.assertEqual(driver['provider_file'], __file__)

        # Test driver with errors
        driver_instance = cast(
            BaseDriver, registry.get_driver_instance('test-label-printer-api')
        )
        self.assertIsNotNone(driver_instance)
        driver_instance.handle_error('Test error')

        response = self.get(reverse('api-machine-drivers'))
        driver = [a for a in response.data if a['slug'] == 'test-label-printer-api']
        self.assertEqual(len(driver), 1)
        driver = driver[0]
        self.assertEqual(driver['driver_errors'], ['Test error'])

    def test_machine_status(self):
        """Test machine status API endpoint."""
        response = self.get(reverse('api-machine-registry-status'))
        errors_msgs = [e['message'] for e in response.data['registry_errors']]

        required_patterns = [
            r'\'<class \'.*\.TestingLabelPrinterDriverNotImplemented\'>\' did not override the required attributes: one of print_label or print_labels',
            "Cannot re-register driver 'test-label-printer-error'",
        ]

        for pattern in required_patterns:
            for error in errors_msgs:
                if re.match(pattern, error):
                    break
            else:
                errors_str = '\n'.join([f'- {e}' for e in errors_msgs])
                self.fail(
                    f"""Error message matching pattern '{pattern}' not found in machine registry errors:\n{errors_str}"""
                )

    def test_machine_list(self):
        """Test machine list API endpoint."""
        response = self.get(reverse('api-machine-list'))
        self.assertEqual(len(response.data), 0)

        MachineConfig.objects.create(
            machine_type='label-printer',
            driver='test-label-printer-api',
            name='Test Machine',
            active=True,
        )

        response = self.get(reverse('api-machine-list'))
        self.assertEqual(len(response.data), 1)
        self.assertDictContainsSubset(
            {
                'name': 'Test Machine',
                'machine_type': 'label-printer',
                'driver': 'test-label-printer-api',
                'initialized': True,
                'active': True,
                'status': 101,
                'status_model': 'LabelPrinterStatus',
                'status_text': '',
                'is_driver_available': True,
            },
            response.data[0],
        )

    def test_machine_detail(self):
        """Test machine detail API endpoint."""
        self.assertFalse(len(MachineConfig.objects.all()), 0)
        self.get(
            reverse('api-machine-detail', kwargs={'pk': self.placeholder_uuid}),
            expected_code=404,
        )

        machine_data = {
            'machine_type': 'label-printer',
            'driver': 'test-label-printer-api',
            'name': 'Test Machine',
            'active': True,
        }

        # Create a machine
        response = self.post(reverse('api-machine-list'), machine_data)
        self.assertDictContainsSubset(machine_data, response.data)
        pk = response.data['pk']

        # Retrieve the machine
        response = self.get(reverse('api-machine-detail', kwargs={'pk': pk}))
        self.assertDictContainsSubset(machine_data, response.data)

        # Update the machine
        response = self.patch(
            reverse('api-machine-detail', kwargs={'pk': pk}),
            {'name': 'Updated Machine'},
        )
        self.assertDictContainsSubset({'name': 'Updated Machine'}, response.data)
        self.assertEqual(MachineConfig.objects.get(pk=pk).name, 'Updated Machine')

        # Delete the machine
        response = self.delete(
            reverse('api-machine-detail', kwargs={'pk': pk}), expected_code=204
        )
        self.assertFalse(len(MachineConfig.objects.all()), 0)

        # Create machine where the driver does not exist
        machine_data['driver'] = 'non-existent-driver'
        machine_data['name'] = 'Machine with non-existent driver'
        response = self.post(reverse('api-machine-list'), machine_data)
        self.assertIn(
            "Driver 'non-existent-driver' not found", response.data['machine_errors']
        )
        self.assertFalse(response.data['initialized'])
        self.assertFalse(response.data['is_driver_available'])

    def test_machine_detail_settings(self):
        """Test machine detail settings API endpoint."""
        machine_setting_url = reverse(
            'api-machine-settings-detail',
            kwargs={'pk': self.placeholder_uuid, 'config_type': 'M', 'key': 'LOCATION'},
        )

        # Test machine settings for non-existent machine
        self.get(machine_setting_url, expected_code=404)

        # Create a machine
        machine = MachineConfig.objects.create(
            machine_type='label-printer',
            driver='test-label-printer-api',
            name='Test Machine with settings',
            active=True,
        )

        machine_setting_url = reverse(
            'api-machine-settings-detail',
            kwargs={'pk': machine.pk, 'config_type': 'M', 'key': 'LOCATION'},
        )
        driver_setting_url = reverse(
            'api-machine-settings-detail',
            kwargs={'pk': machine.pk, 'config_type': 'D', 'key': 'TEST_SETTING'},
        )

        # Get settings
        response = self.get(machine_setting_url)
        self.assertEqual(response.data['value'], '')

        response = self.get(driver_setting_url)
        self.assertEqual(response.data['value'], '')

        # Update machine setting
        location = StockLocation.objects.create(name='Test Location')
        response = self.patch(machine_setting_url, {'value': str(location.pk)})
        self.assertEqual(response.data['value'], str(location.pk))

        response = self.get(machine_setting_url)
        self.assertEqual(response.data['value'], str(location.pk))

        # Update driver setting
        response = self.patch(driver_setting_url, {'value': 'test value'})
        self.assertEqual(response.data['value'], 'test value')

        response = self.get(driver_setting_url)
        self.assertEqual(response.data['value'], 'test value')

        # Get list of all settings for a machine
        settings_url = reverse('api-machine-settings', kwargs={'pk': machine.pk})
        response = self.get(settings_url)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(
            [('M', 'LOCATION'), ('D', 'TEST_SETTING')],
            [(s['config_type'], s['key']) for s in response.data],
        )

    def test_machine_restart(self):
        """Test machine restart API endpoint."""
        machine = MachineConfig.objects.create(
            machine_type='label-printer',
            driver='test-label-printer-api',
            name='Test Machine',
            active=True,
        )

        # verify machine status before restart
        response = self.get(reverse('api-machine-detail', kwargs={'pk': machine.pk}))
        self.assertEqual(response.data['status_text'], '')

        # restart the machine
        response = self.post(
            reverse('api-machine-restart', kwargs={'pk': machine.pk}), expected_code=200
        )

        # verify machine status after restart
        response = self.get(reverse('api-machine-detail', kwargs={'pk': machine.pk}))
        self.assertEqual(response.data['status_text'], 'Restarting...')
