"""Tests for PUI backend stuff."""
import json

from InvenTree.unit_test import InvenTreeTestCase

from .templatetags import spa_helper


class TemplateTagTest(InvenTreeTestCase):
    """Tests for the template tag code."""

    def test_spa_bundle(self):
        """Test the 'spa_bundle' template tag"""
        resp = spa_helper.spa_bundle()
        self.assertTrue(resp.startswith('<link rel="stylesheet" href="/static/web/assets/index'))
        shipped_js = resp.split('<script type="module" src="')[1:]
        self.assertTrue(len(shipped_js) > 0)
        self.assertTrue(len(shipped_js) == 3)

    def test_spa_settings(self):
        """Test the 'spa_settings' template tag"""
        resp = spa_helper.spa_settings()
        self.assertTrue(resp.startswith('<script>window.INVENTREE_SETTINGS='))
        settings_data_string = resp.replace('<script>window.INVENTREE_SETTINGS=', '').replace('</script>', '')
        settings_data = json.loads(settings_data_string)
        self.assertTrue('debug' in settings_data)
        self.assertTrue('server_list' in settings_data)
        self.assertTrue('show_server_selector' in settings_data)
        self.assertTrue('environment' in settings_data)
