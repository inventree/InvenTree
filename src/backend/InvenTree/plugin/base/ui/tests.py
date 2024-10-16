"""Unit tests for base mixins for plugins."""

from django.urls import reverse

from common.models import InvenTreeSetting
from InvenTree.unit_test import InvenTreeAPITestCase
from plugin.registry import registry


class UserInterfaceMixinTests(InvenTreeAPITestCase):
    """Test the UserInterfaceMixin plugin mixin class."""

    roles = 'all'

    fixtures = ['part', 'category', 'location', 'stock']

    @classmethod
    def setUpTestData(cls):
        """Set up the test case."""
        super().setUpTestData()

        # Ensure that the 'sampleui' plugin is installed and active
        registry.set_plugin_state('sampleui', True)

        # Ensure that UI plugins are enabled
        InvenTreeSetting.set_setting('ENABLE_PLUGINS_INTERFACE', True, change_user=None)

    def test_installed(self):
        """Test that the sample UI plugin is installed and active."""
        plugin = registry.get_plugin('sampleui')
        self.assertTrue(plugin.is_active())

        plugins = registry.with_mixin('ui')
        self.assertGreater(len(plugins), 0)

    def test_panels(self):
        """Test that the sample UI plugin provides custom panels."""
        from part.models import Part

        plugin = registry.get_plugin('sampleui')

        _part = Part.objects.first()

        # Ensure that the part is active
        _part.active = True
        _part.save()

        url = reverse('api-plugin-panel-list')

        query_data = {'target_model': 'part', 'target_id': _part.pk}

        # Enable *all* plugin settings
        plugin.set_setting('ENABLE_PART_PANELS', True)
        plugin.set_setting('ENABLE_PURCHASE_ORDER_PANELS', True)
        plugin.set_setting('ENABLE_BROKEN_PANELS', True)
        plugin.set_setting('ENABLE_DYNAMIC_PANEL', True)

        # Request custom panel information for a part instance
        response = self.get(url, data=query_data)

        # There should be 4 active panels for the part by default
        self.assertEqual(4, len(response.data))

        _part.active = False
        _part.save()

        response = self.get(url, data=query_data)

        # As the part is not active, only 3 panels left
        self.assertEqual(3, len(response.data))

        # Disable the "ENABLE_PART_PANELS" setting, and try again
        plugin.set_setting('ENABLE_PART_PANELS', False)

        response = self.get(url, data=query_data)

        # There should still be 3 panels
        self.assertEqual(3, len(response.data))

        # Check for the correct panel names
        self.assertEqual(response.data[0]['name'], 'sample_panel')
        self.assertIn('content', response.data[0])
        self.assertNotIn('source', response.data[0])

        self.assertEqual(response.data[1]['name'], 'broken_panel')
        self.assertEqual(response.data[1]['source'], '/this/does/not/exist.js')
        self.assertNotIn('content', response.data[1])

        self.assertEqual(response.data[2]['name'], 'dynamic_panel')
        self.assertEqual(
            response.data[2]['source'], '/static/plugins/sampleui/sample_panel.js'
        )
        self.assertNotIn('content', response.data[2])

        # Next, disable the global setting for UI integration
        InvenTreeSetting.set_setting(
            'ENABLE_PLUGINS_INTERFACE', False, change_user=None
        )

        response = self.get(url, data=query_data)

        # There should be no panels available
        self.assertEqual(0, len(response.data))

        # Set the setting back to True for subsequent tests
        InvenTreeSetting.set_setting('ENABLE_PLUGINS_INTERFACE', True, change_user=None)

    def test_ui_features(self):
        """Test that the sample UI plugin provides custom features."""
        template_editor_url = reverse(
            'api-plugin-ui-feature-list', kwargs={'feature': 'template_editor'}
        )
        template_preview_url = reverse(
            'api-plugin-ui-feature-list', kwargs={'feature': 'template_preview'}
        )

        query_data_label = {'template_type': 'labeltemplate', 'template_model': 'part'}
        query_data_report = {
            'template_type': 'reporttemplate',
            'template_model': 'part',
        }

        # Request custom template editor information
        response = self.get(template_editor_url, data=query_data_label)
        self.assertEqual(1, len(response.data))

        response = self.get(template_editor_url, data=query_data_report)
        self.assertEqual(0, len(response.data))

        response = self.get(template_preview_url, data=query_data_report)
        self.assertEqual(1, len(response.data))

        # Check for the correct feature details here
        self.assertEqual(response.data[0]['feature_type'], 'template_preview')
        self.assertDictEqual(
            response.data[0]['options'],
            {
                'key': 'sample-template-preview',
                'title': 'Sample Template Preview',
                'icon': 'category',
            },
        )
        self.assertEqual(
            response.data[0]['source'],
            '/static/plugin/sample_template.js:getTemplatePreview',
        )

        # Next, disable the global setting for UI integration
        InvenTreeSetting.set_setting(
            'ENABLE_PLUGINS_INTERFACE', False, change_user=None
        )

        response = self.get(template_editor_url, data=query_data_label)

        # There should be no features available
        self.assertEqual(0, len(response.data))

        # Set the setting back to True for subsequent tests
        InvenTreeSetting.set_setting('ENABLE_PLUGINS_INTERFACE', True, change_user=None)
