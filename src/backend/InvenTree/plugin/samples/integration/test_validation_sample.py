"""Unit tests for the SampleValidatorPlugin class."""

from django.core.exceptions import ValidationError
from django.urls import reverse

import build.models
import part.models
from InvenTree.unit_test import InvenTreeAPITestCase, InvenTreeTestCase
from plugin.registry import registry


class SampleValidatorPluginTest(InvenTreeAPITestCase, InvenTreeTestCase):
    """Tests for the SampleValidatonPlugin class."""

    fixtures = ['part', 'category', 'location', 'build']

    def setUp(self):
        """Set up the test environment."""
        cat = part.models.PartCategory.objects.first()
        self.part = part.models.Part.objects.create(
            name='TestPart', category=cat, description='A test part', component=True
        )
        self.assembly = part.models.Part.objects.create(
            name='TestAssembly',
            category=cat,
            description='A test assembly',
            component=False,
            assembly=True,
        )
        self.bom_item = part.models.BomItem.objects.create(
            part=self.assembly, sub_part=self.part, quantity=1
        )
        super().setUp()

    def get_plugin(self):
        """Return the SampleValidatorPlugin instance."""
        return registry.get_plugin('validator', active=True)

    def enable_plugin(self, en: bool):
        """Enable or disable the SampleValidatorPlugin."""
        registry.set_plugin_state('validator', en)

    def test_validate_model_instance(self):
        """Test the validate_model_instance function."""
        # First, ensure that the plugin is disabled
        self.enable_plugin(False)

        plg = self.get_plugin()
        self.assertIsNone(plg)

        # Set the BomItem quantity to a non-integer value
        # This should pass, as the plugin is currently disabled
        self.bom_item.quantity = 3.14159
        self.bom_item.save()

        # Next, check that we can make a part instance description shorter
        prt = part.models.Part.objects.first()
        prt.description = prt.description[:-1]
        prt.save()

        # Now, enable the plugin
        self.enable_plugin(True)

        plg = self.get_plugin()
        self.assertIsNotNone(plg)

        plg.set_setting('BOM_ITEM_INTEGER', True)

        self.bom_item.quantity = 3.14159
        with self.assertRaises(ValidationError):
            self.bom_item.save()

        # Now, disable the plugin setting
        plg.set_setting('BOM_ITEM_INTEGER', False)

        self.bom_item.quantity = 3.14159
        self.bom_item.save()

        # Test that we *cannot* set a part description to a shorter value
        prt.description = prt.description[:-1]
        with self.assertRaises(ValidationError):
            prt.save()

        self.enable_plugin(False)

    def test_validate_part_name(self):
        """Test the validate_part_name function."""
        self.enable_plugin(True)
        plg = self.get_plugin()
        self.assertIsNotNone(plg)

        # Set the part description short
        self.part.description = 'x'

        with self.assertRaises(ValidationError):
            self.part.save()

        self.enable_plugin(False)
        self.part.save()

    def test_validate_ipn(self):
        """Test the validate_ipn function."""
        self.enable_plugin(True)
        plg = self.get_plugin()
        self.assertIsNotNone(plg)

        self.part.IPN = 'LMNOP'
        plg.set_setting('IPN_MUST_CONTAIN_Q', False)
        self.part.save()

        plg.set_setting('IPN_MUST_CONTAIN_Q', True)

        with self.assertRaises(ValidationError):
            self.part.save()

        self.part.IPN = 'LMNOPQ'

        self.part.save()

    def test_validate_generate_batch_code(self):
        """Test the generate_batch_code function."""
        self.enable_plugin(True)
        plg = self.get_plugin()
        self.assertIsNotNone(plg)

        code = plg.generate_batch_code()
        self.assertIsInstance(code, str)
        self.assertTrue(code.startswith('SAMPLE-BATCH'))

    def test_api_batch(self):
        """Test the batch code validation API."""
        self.enable_plugin(True)
        url = reverse('api-generate-batch-code')

        response = self.post(url)
        self.assertIn('batch_code', response.data)
        self.assertTrue(response.data['batch_code'].startswith('SAMPLE-BATCH'))

        # Use part code
        part_itm = part.models.Part.objects.first()
        response = self.post(url, {'part': part_itm.pk})
        self.assertIn('batch_code', response.data)
        self.assertTrue(
            response.data['batch_code'].startswith(part_itm.name + '-SAMPLE-BATCH')
        )

        # Use build_order
        build_itm = build.models.Build.objects.first()
        response = self.post(url, {'build_order': build_itm.pk})
        self.assertIn('batch_code', response.data)
        self.assertTrue(
            response.data['batch_code'].startswith(
                build_itm.reference + '-SAMPLE-BATCH'
            )
        )
