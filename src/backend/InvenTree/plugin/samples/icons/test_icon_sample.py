"""Unit tests for icon pack sample plugins."""

from django.urls import reverse

from InvenTree.unit_test import InvenTreeAPITestCase
from plugin import InvenTreePlugin, registry
from plugin.helpers import MixinNotImplementedError
from plugin.mixins import IconPackMixin


class SampleIconPackPluginTests(InvenTreeAPITestCase):
    """Tests for SampleIconPackPlugin."""

    def test_get_icons_api(self):
        """Check get icons api."""
        # Activate plugin
        config = registry.get_plugin('sampleicons').plugin_config()
        config.active = True
        config.save()

        response = self.get(reverse('api-icon-list'), expected_code=200)
        self.assertEqual(len(response.data), 2)

        for icon_pack in response.data:
            if icon_pack['prefix'] == 'my':
                break
        else:
            self.fail('My icon pack not found')

        self.assertEqual(icon_pack['prefix'], 'my')
        self.assertEqual(icon_pack['name'], 'My Custom Icons')
        for font_format in ['woff2', 'woff', 'truetype']:
            self.assertIn(font_format, icon_pack['fonts'])

        self.assertEqual(len(icon_pack['icons']), 1)
        self.assertEqual(icon_pack['icons']['my-icon']['name'], 'My Icon')
        self.assertEqual(icon_pack['icons']['my-icon']['category'], '')
        self.assertEqual(icon_pack['icons']['my-icon']['tags'], ['my', 'icon'])
        self.assertEqual(
            icon_pack['icons']['my-icon']['variants'],
            {'filled': 'f0a5', 'cool': 'f073'},
        )

    def test_mixin(self):
        """Test that MixinNotImplementedError is raised."""

        class Wrong(IconPackMixin, InvenTreePlugin):
            pass

        with self.assertRaises(MixinNotImplementedError):
            plugin = Wrong()
            plugin.icon_packs()
