"""Tests for PUI backend stuff."""

import json
import os
from pathlib import Path
from unittest import mock

from InvenTree.config import get_frontend_settings
from InvenTree.unit_test import InvenTreeTestCase

from .templatetags import spa_helper


class TemplateTagTest(InvenTreeTestCase):
    """Tests for the template tag code."""

    def assertSettings(self, settings_data):
        """Helper to test if needed args are in the settings."""
        self.assertTrue('debug' in settings_data)
        self.assertTrue('server_list' in settings_data)
        self.assertTrue('show_server_selector' in settings_data)
        self.assertTrue('environment' in settings_data)

    def test_spa_bundle(self):
        """Test the 'spa_bundle' template tag"""
        resp = spa_helper.spa_bundle()
        self.assertTrue(
            resp.startswith('<link rel="stylesheet" href="/static/web/assets/index')
        )
        shipped_js = resp.split('<script type="module" src="')[1:]
        self.assertTrue(len(shipped_js) > 0)
        self.assertTrue(len(shipped_js) == 3)

        manifest_file = Path(__file__).parent.joinpath("static/web/manifest.json")
        # Try with removed manifest file
        manifest_file.rename(manifest_file.with_suffix('.json.bak'))  # Rename
        resp = resp = spa_helper.spa_bundle()
        self.assertIsNone(resp)
        manifest_file.with_suffix('.json.bak').rename(
            manifest_file.with_suffix('.json')
        )  # Name back

    def test_spa_settings(self):
        """Test the 'spa_settings' template tag"""
        resp = spa_helper.spa_settings()
        self.assertTrue(resp.startswith('<script>window.INVENTREE_SETTINGS='))
        settings_data_string = resp.replace(
            '<script>window.INVENTREE_SETTINGS=', ''
        ).replace('</script>', '')
        settings_data = json.loads(settings_data_string)
        self.assertSettings(settings_data)

    def test_get_frontend_settings(self):
        """Test frontend settings retrieval."""
        # Normal run for priming
        rsp = get_frontend_settings()
        self.assertSettings(rsp)

        # No base_url
        envs = {'INVENTREE_PUI_URL_BASE': ''}
        with mock.patch.dict(os.environ, envs):
            rsp = get_frontend_settings()
            self.assertSettings(rsp)

        # No debug, no serverlist -> selector
        rsp = get_frontend_settings(False)
        self.assertSettings(rsp)
        self.assertTrue(rsp['show_server_selector'])

        # No debug, serverlist -> no selector
        envs = {'INVENTREE_PUI_SETTINGS': json.dumps({'server_list': ['aa', 'bb']})}
        with mock.patch.dict(os.environ, envs):
            rsp = get_frontend_settings(False)
            self.assertFalse('show_server_selector' in rsp)
            self.assertEqual(rsp['server_list'], ['aa', 'bb'])
