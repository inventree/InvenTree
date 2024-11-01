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

    def test_ui_dashboard_items(self):
        """Test that the sample UI plugin provides custom dashboard items."""
        # Ensure the user has superuser status
        self.user.is_superuser = True
        self.user.save()

        url = reverse('api-plugin-ui-feature-list', kwargs={'feature': 'dashboard'})

        response = self.get(url)
        self.assertEqual(len(response.data), 4)

        for item in response.data:
            self.assertEqual(item['plugin_name'], 'sampleui')

        self.assertEqual(response.data[0]['key'], 'broken-dashboard-item')
        self.assertEqual(response.data[0]['title'], 'Broken Dashboard Item')
        self.assertEqual(response.data[0]['source'], '/this/does/not/exist.js')

        self.assertEqual(response.data[1]['key'], 'sample-dashboard-item')
        self.assertEqual(response.data[1]['title'], 'Sample Dashboard Item')
        self.assertEqual(
            response.data[1]['source'],
            '/static/plugins/sampleui/sample_dashboard_item.js',
        )

        self.assertEqual(response.data[2]['key'], 'dynamic-dashboard-item')
        self.assertEqual(response.data[2]['title'], 'Context Dashboard Item')
        self.assertEqual(
            response.data[2]['source'],
            '/static/plugins/sampleui/sample_dashboard_item.js:renderContextItem',
        )

        self.assertEqual(response.data[3]['key'], 'admin-dashboard-item')
        self.assertEqual(response.data[3]['title'], 'Admin Dashboard Item')
        self.assertEqual(
            response.data[3]['source'],
            '/static/plugins/sampleui/admin_dashboard_item.js',
        )

        # Additional options and context data should be passed through to the client
        self.assertDictEqual(response.data[3]['options'], {'width': 4, 'height': 2})

        self.assertDictEqual(
            response.data[3]['context'], {'secret-key': 'this-is-a-secret'}
        )

        # Remove superuser status - the 'admin-dashboard-item' should disappear
        self.user.is_superuser = False
        self.user.save()

        response = self.get(url)
        self.assertEqual(len(response.data), 3)

    def test_ui_panels(self):
        """Test that the sample UI plugin provides custom panels."""
        from part.models import Part

        plugin = registry.get_plugin('sampleui')

        _part = Part.objects.first()

        # Ensure that the part is active
        _part.active = True
        _part.save()

        url = reverse('api-plugin-ui-feature-list', kwargs={'feature': 'panel'})

        query_data = {'target_model': 'part', 'target_id': _part.pk}

        # Enable *all* plugin settings
        plugin.set_setting('ENABLE_PART_PANELS', True)
        plugin.set_setting('ENABLE_PURCHASE_ORDER_PANELS', True)
        plugin.set_setting('ENABLE_BROKEN_PANELS', True)
        plugin.set_setting('ENABLE_DYNAMIC_PANEL', True)

        # Request custom panel information for a part instance
        response = self.get(url, data=query_data)

        # There should be 4 active panels for the part by default
        self.assertEqual(3, len(response.data))

        _part.active = False
        _part.save()

        response = self.get(url, data=query_data)

        # As the part is not active, only 3 panels left
        self.assertEqual(3, len(response.data))

        # Disable the "ENABLE_PART_PANELS" setting, and try again
        plugin.set_setting('ENABLE_PART_PANELS', False)

        response = self.get(url, data=query_data)

        # There should still be 2 panels
        self.assertEqual(2, len(response.data))

        for panel in response.data:
            self.assertEqual(panel['plugin_name'], 'sampleui')
            self.assertEqual(panel['feature_type'], 'panel')

        self.assertEqual(response.data[0]['key'], 'broken-panel')
        self.assertEqual(response.data[0]['title'], 'Broken Panel')
        self.assertEqual(response.data[0]['source'], '/this/does/not/exist.js')

        self.assertEqual(response.data[1]['key'], 'dynamic-panel')
        self.assertEqual(response.data[1]['title'], 'Dynamic Panel')
        self.assertEqual(
            response.data[1]['source'], '/static/plugins/sampleui/sample_panel.js'
        )

        ctx = response.data[1]['context']

        for k in ['version', 'plugin_version', 'random', 'time']:
            self.assertIn(k, ctx)

        # Next, disable the global setting for UI integration
        InvenTreeSetting.set_setting(
            'ENABLE_PLUGINS_INTERFACE', False, change_user=None
        )

        response = self.get(url, data=query_data)

        # There should be no panels available
        self.assertEqual(0, len(response.data))

        # Set the setting back to True for subsequent tests
        InvenTreeSetting.set_setting('ENABLE_PLUGINS_INTERFACE', True, change_user=None)

    def test_ui_template_editors(self):
        """Test that the sample UI plugin provides template editor features."""
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

        # Request custom label template editor information
        response = self.get(template_editor_url, data=query_data_label)
        self.assertEqual(1, len(response.data))

        data = response.data[0]

        for k, v in {
            'plugin_name': 'sampleui',
            'key': 'sample-template-editor',
            'title': 'Sample Template Editor',
            'source': '/static/plugins/sampleui/sample_template.js:getTemplateEditor',
        }.items():
            self.assertEqual(data[k], v)

        # Request custom report template editor information
        response = self.get(template_editor_url, data=query_data_report)
        self.assertEqual(0, len(response.data))

        # Request custom report template preview information
        response = self.get(template_preview_url, data=query_data_report)
        self.assertEqual(1, len(response.data))

        data = response.data[0]

        for k, v in {
            'plugin_name': 'sampleui',
            'feature_type': 'template_preview',
            'key': 'sample-template-preview',
            'title': 'Sample Template Preview',
            'context': None,
            'source': '/static/plugins/sampleui/sample_preview.js:getTemplatePreview',
        }.items():
            self.assertEqual(data[k], v)

        # Next, disable the global setting for UI integration
        InvenTreeSetting.set_setting(
            'ENABLE_PLUGINS_INTERFACE', False, change_user=None
        )

        response = self.get(template_editor_url, data=query_data_label)

        # There should be no features available
        self.assertEqual(0, len(response.data))

        # Set the setting back to True for subsequent tests
        InvenTreeSetting.set_setting('ENABLE_PLUGINS_INTERFACE', True, change_user=None)
