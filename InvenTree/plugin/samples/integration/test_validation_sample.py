"""Unit tests for the SampleValidatorPlugin class."""

from django.core.exceptions import ValidationError

import part.models
from InvenTree.unit_test import InvenTreeTestCase
from plugin.registry import registry


class SampleValidatorPluginTest(InvenTreeTestCase):
    """Tests for the SampleValidatonPlugin class."""

    fixtures = ['category', 'location']

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
