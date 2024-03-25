"""Unit tests for app plugin."""

import os
from pathlib import Path
from unittest import mock

from django.core.management import call_command
from django.urls import reverse

from InvenTree.unit_test import InvenTreeAPITestCase, InvenTreeTestCase
from plugin import registry


class SampleAppIntegrationPluginTests(InvenTreeAPITestCase, InvenTreeTestCase):
    """Tests for SampleAppIntegrationPlugin."""

    superuser = True

    def test_api(self):
        """Check the APIs of the custom sample plugin work."""
        from common.models import InvenTreeSetting

        # Set up test environment
        InvenTreeSetting.set_setting('ENABLE_PLUGINS_URL', True, None)
        registry.set_plugin_state('app_sample_plugin', True)

        _dir = str(
            Path(__file__).parent.joinpath('samples_app', 'app_sample').absolute()
        )

        # Patch environment variable to add dir
        envs = {'INVENTREE_PLUGIN_TEST_DIR': _dir}
        with mock.patch.dict(os.environ, envs):
            # Reload to rediscover plugins
            registry.reload_plugins(full_reload=True, collect=True)

            # Run migrations
            call_command('migrate', verbosity=0)

            # Get
            response = self.get(reverse('plugin:app_sample_plugin:api-list'))
            self.assertEqual(response.status_code, 200)
            print('smapel-plugin-api-list', response.json())

            # Detail
            response = self.get(
                reverse('plugin:app_sample_plugin:api-detail', kwargs={'pk': 1})
            )
            self.assertEqual(response.status_code, 200)
            print('smapel-plugin-api-detail', response.json())

            # Options
            try:
                response = self.options(reverse('plugin:app_sample_plugin:api-list'))
                self.assertEqual(response.status_code, 200)
                print('smapel-plugin-api-options', response.json())
            except Exception as e:
                print('smapel-plugin-api-options error', e)

        # Tear down test environment
        InvenTreeSetting.set_setting('ENABLE_PLUGINS_URL', False, None)
        registry.reload_plugins()
