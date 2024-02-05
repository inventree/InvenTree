"""Machine API tests."""

from django.urls import reverse

from InvenTree.unit_test import InvenTreeAPITestCase
from machine import registry
from machine.machine_types import BaseLabelPrintingDriver


class MachineAPITest(InvenTreeAPITestCase):
    """Class for unit testing machine API endpoints."""

    @classmethod
    def setUpTestData(cls):
        """Create a test driver."""
        super().setUpTestData()

        class TestingLabelPrinterDriver(BaseLabelPrintingDriver):
            """Test driver for label printing."""

            SLUG = 'test-label-printer'
            NAME = 'Test label printer'
            DESCRIPTION = 'This is a test label printer driver for testing.'

            def print_label(self, *args, **kwargs) -> None:
                """Override print_label."""
                pass

        id(TestingLabelPrinterDriver)  # just to be sure that this class really exists
        registry.initialize()

    def test_machine_type_list(self):
        """Test machine types list API endpoint."""
        response = self.get(reverse('api-machine-types'))
        self.assertEqual(len(response.data), 1)
        self.assertDictContainsSubset(
            {
                'slug': 'label-printer',
                'name': 'Label Printer',
                'description': 'Directly print labels for various items.',
                'provider_plugin': None,
                'is_builtin': True,
            },
            response.data[0],
        )
        self.assertTrue(
            response.data[0]['provider_file'].endswith(
                'machine/machine_types/LabelPrintingMachineType.py'
            )
        )

    def test_machine_driver_list(self):
        """Test machine driver list API endpoint."""
        response = self.get(reverse('api-machine-drivers'))
        self.assertEqual(len(response.data), 1)
        self.assertDictContainsSubset(
            {
                'slug': 'test-label-printer',
                'name': 'Test label printer',
                'description': 'This is a test label printer driver for testing.',
                'provider_plugin': None,
                'is_builtin': True,
                'machine_type': 'label-printer',
                'errors': [],
            },
            response.data[0],
        )
