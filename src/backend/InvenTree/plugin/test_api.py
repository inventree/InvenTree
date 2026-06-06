"""Tests for general API tests for the plugin app."""

from django.test import override_settings
from django.urls import reverse

from rest_framework.exceptions import NotFound

from InvenTree.unit_test import InvenTreeAPITestCase, PluginMixin
from plugin.api import check_plugin
from plugin.models import PluginConfig, PluginSetting


class PluginDetailAPITest(PluginMixin, InvenTreeAPITestCase):
    """Tests the plugin API endpoints."""

    roles = ['admin.add', 'admin.view', 'admin.change', 'admin.delete']

    def setUp(self):
        """Setup for all tests."""
        self.MSG_NO_PKG = 'Either packagename or URL must be provided'

        self.PKG_NAME = 'inventree-brother-plugin'
        self.PKG_URL = 'git+https://github.com/inventree/inventree-brother-plugin'
        super().setUp()

    def test_plugin_uninstall(self):
        """Test plugin uninstall command."""
        # invalid package name
        url = reverse('api-plugin-uninstall', kwargs={'plugin': 'samplexx'})

        # Requires superuser permissions
        self.patch(url, expected_code=403)

        self.user.is_superuser = True
        self.user.save()

        # Invalid slug (404 error)
        self.patch(url, expected_code=404)

        url = reverse('api-plugin-uninstall', kwargs={'plugin': 'sample'})

        data = self.patch(url, expected_code=400).data

        plugs = {
            'sample': 'Plugin cannot be uninstalled as it is a sample plugin',
            'bom-exporter': 'Plugin cannot be uninstalled as it is currently active',
            'inventree-slack-notification': 'Plugin cannot be uninstalled as it is a built-in plugin',
        }

        for slug, msg in plugs.items():
            url = reverse('api-plugin-uninstall', kwargs={'plugin': slug})
            data = self.patch(url, expected_code=400).data
            self.assertIn(msg, str(data))

        with self.settings(PLUGINS_INSTALL_DISABLED=True):
            url = reverse('api-plugin-uninstall', kwargs={'plugin': 'bom-exporter'})
            data = self.patch(url, expected_code=400).data
            self.assertIn(
                'Plugin uninstalling is disabled', str(data['non_field_errors'])
            )

    def test_plugin_install(self):
        """Test the plugin install command."""
        url = reverse('api-plugin-install')

        # Requires superuser permissions
        self.user.is_superuser = False
        self.user.save()

        self.post(
            url,
            {'confirm': True, 'packagename': self.PKG_NAME},
            expected_code=403,
            max_query_time=30,
        )

        # Provide superuser permissions
        self.user.is_superuser = True
        self.user.save()

        # invalid package name
        data = self.post(
            url,
            {
                'confirm': True,
                'packagename': 'invalid_package_name-asdads-asfd-asdf-asdf-asdf',
            },
            expected_code=400,
            max_query_time=60,
        ).data

        self.assertIn(
            'ERROR: Could not find a version that satisfies the requirement', str(data)
        )
        self.assertIn('ERROR: No matching distribution found for', str(data))

        # valid - Pypi
        data = self.post(
            url,
            {'confirm': True, 'packagename': self.PKG_NAME},
            expected_code=201,
            max_query_time=30,
            max_query_count=450,
        ).data

        self.assertEqual(data['success'], 'Installed plugin successfully')

        # valid - github url
        data = self.post(
            url,
            {'confirm': True, 'url': self.PKG_URL},
            expected_code=201,
            max_query_count=450,
            max_query_time=60,
        ).data

        self.assertEqual(data['success'], 'Installed plugin successfully')

        # valid - github url and package name
        data = self.post(
            url,
            {'confirm': True, 'url': self.PKG_URL, 'packagename': self.PKG_NAME},
            expected_code=201,
            max_query_count=450,
            max_query_time=30,
        ).data
        self.assertEqual(data['success'], 'Installed plugin successfully')

        # valid (kindoff) - Pypi and onsense uri
        data = self.post(
            url,
            {'confirm': True, 'packagename': self.PKG_NAME, 'url': 'lol://example.com'},
            expected_code=201,
            max_query_time=30,
            max_query_count=450,
        ).data

        # invalid tries
        # no input
        data = self.post(url, {}, expected_code=400).data
        self.assertIn('This field is required.', str(data['confirm']))

        # no package info
        data = self.post(url, {'confirm': True}, expected_code=400).data

        self.assertEqual(data['url'][0].title().upper(), self.MSG_NO_PKG.upper())
        self.assertEqual(
            data['packagename'][0].title().upper(), self.MSG_NO_PKG.upper()
        )

        # not confirmed
        data = self.post(url, {'packagename': self.PKG_NAME}, expected_code=400).data
        self.assertIn('This field is required.', str(data['confirm']))

        data = self.post(
            url, {'packagename': self.PKG_NAME, 'confirm': False}, expected_code=400
        ).data

        self.assertEqual(
            data['confirm'][0].title().upper(), 'Installation not confirmed'.upper()
        )

        # Plugin installation disabled
        with self.settings(PLUGINS_INSTALL_DISABLED=True):
            response = self.post(
                url,
                {'packagename': 'inventree-order-history', 'confirm': True},
                expected_code=400,
            )
            self.assertIn(
                'Plugin installation is disabled',
                str(response.data['non_field_errors']),
            )

        # plugin - normal user should not be able to install plugins
        self.user.is_staff = False
        self.user.save()
        self.post(
            url,
            {'confirm': True, 'packagename': self.PKG_NAME},
            expected_code=400,
            max_query_time=30,
            max_query_count=450,
        )

    def test_plugin_deactivate_mandatory(self):
        """Test deactivating a mandatory plugin."""
        self.user.is_superuser = True
        self.user.save()

        # Get a mandatory plugin
        plg = PluginConfig.objects.filter(key='bom-exporter').first()
        assert plg is not None

        url = reverse('api-plugin-detail-activate', kwargs={'plugin': plg.key})

        # Try to deactivate the mandatory plugin
        response = self.client.patch(url, {'active': False}, follow=True)
        self.assertEqual(response.status_code, 400)
        self.assertIn('Mandatory plugin cannot be deactivated', str(response.data))

    def test_plugin_activate(self):
        """Test the plugin activation API endpoint."""
        test_plg = PluginConfig.objects.get(key='samplelocate')
        self.assertIsNotNone(test_plg, 'Test plugin not found')
        self.assertFalse(test_plg.is_active())
        self.assertFalse(test_plg.is_builtin())
        self.assertFalse(test_plg.is_mandatory())

        url = reverse('api-plugin-detail-activate', kwargs={'plugin': test_plg.key})

        # Should not work - not a superuser
        response = self.client.post(url, {}, follow=True)
        self.assertEqual(response.status_code, 403)

        # Make user superuser
        self.user.is_superuser = True
        self.user.save()

        # Deactivate plugin
        test_plg.active = False
        test_plg.save()

        # Activate plugin with detail url
        test_plg.refresh_from_db()
        self.assertFalse(test_plg.is_active())

        response = self.client.patch(url, {}, follow=True)
        self.assertEqual(response.status_code, 200)

        test_plg.refresh_from_db()
        self.assertTrue(test_plg.is_active())

        # Deactivate plugin
        test_plg.active = False
        test_plg.save()

        # Activate plugin
        test_plg.refresh_from_db()
        self.assertFalse(test_plg.active)
        response = self.client.patch(url, {}, follow=True)
        self.assertEqual(response.status_code, 200)

        test_plg.refresh_from_db()
        self.assertTrue(test_plg.is_active())

    def test_plugin_config_delete(self):
        """Test deleting a config."""
        test_plg = self.plugin_confs.first()
        assert test_plg is not None

        self.user.is_superuser = True
        self.user.save()

        url = reverse('api-plugin-detail', kwargs={'plugin': test_plg.key})
        response = self.delete(url, {}, expected_code=400)
        self.assertIn(
            'Plugin cannot be deleted as it is currently active',
            str(response.data['detail']),
        )

    @override_settings(
        SITE_URL='http://testserver', CSRF_TRUSTED_ORIGINS=['http://testserver']
    )
    def test_admin_action(self):
        """Test the PluginConfig action commands."""
        url = reverse('admin:plugin_pluginconfig_changelist')

        test_plg = self.plugin_confs.first()
        assert test_plg is not None

        # deactivate plugin
        response = self.client.post(
            url,
            {
                'action': 'plugin_deactivate',
                'index': 0,
                '_selected_action': [test_plg.pk],
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Select Plugin Configuration to change')

        # deactivate plugin - deactivate again -> nothing will happen but the nothing 'changed' function is triggered
        response = self.client.post(
            url,
            {
                'action': 'plugin_deactivate',
                'index': 0,
                '_selected_action': [test_plg.pk],
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Select Plugin Configuration to change')

        # activate plugin
        response = self.client.post(
            url,
            {
                'action': 'plugin_activate',
                'index': 0,
                '_selected_action': [test_plg.pk],
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Select Plugin Configuration to change')

        # save to deactivate a plugin
        response = self.client.post(
            reverse('admin:plugin_pluginconfig_change', args=(test_plg.pk,)),
            {'_save': 'Save'},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, '(not active) | Change Plugin Configuration | Django site admin'
        )

    def test_model(self):
        """Test the PluginConfig model."""
        # check mixin registry
        plg = self.plugin_confs.first()
        assert plg is not None

        mixin_dict = plg.mixins()
        self.assertIn('base', mixin_dict)
        self.assertEqual(
            mixin_dict, {**mixin_dict, 'base': {'key': 'base', 'human_name': 'base'}}
        )

        # check reload on save
        with self.assertWarns(Warning) as cm:
            plg_inactive = self.plugin_confs.filter(active=False).first()
            assert plg_inactive is not None

            plg_inactive.active = True
            plg_inactive.save()

        self.assertEqual(
            cm.warning.args[0],
            f'A plugin registry reload was triggered for plugin {plg_inactive.key}',
        )

        # Set active state back to False
        with self.assertWarns(Warning) as cm:
            plg_inactive.active = False
            plg_inactive.save()

        self.assertEqual(
            cm.warning.args[0],
            f'A plugin registry reload was triggered for plugin {plg_inactive.key}',
        )

    def test_check_plugin(self):
        """Test check_plugin function."""
        # No argument
        with self.assertRaises(NotFound) as exc:
            check_plugin(plugin_slug=None, plugin_pk=None)
        self.assertEqual(str(exc.exception.detail), 'Plugin not specified')

        # Wrong with slug
        with self.assertRaises(NotFound) as exc:
            check_plugin(plugin_slug='123abc', plugin_pk=None)
        self.assertEqual(str(exc.exception.detail), "Plugin '123abc' not installed")

        # Wrong with pk
        with self.assertRaises(NotFound) as exc:
            check_plugin(plugin_slug=None, plugin_pk=123)
        self.assertEqual(str(exc.exception.detail), "Plugin '123' not installed")

    def test_plugin_settings(self):
        """Test plugin settings access via the API."""
        # Ensure we have superuser permissions
        self.user.is_superuser = True
        self.user.save()

        # Activate the 'sample' plugin via the API
        cfg = PluginConfig.objects.filter(key='sample').first()
        self.assertIsNotNone(cfg)

        url = reverse('api-plugin-detail-activate', kwargs={'plugin': cfg.key})
        self.client.patch(url, {}, expected_code=200)

        # Valid plugin settings endpoints
        valid_settings = ['SELECT_PART', 'API_KEY', 'NUMERICAL_SETTING']

        for key in valid_settings:
            response = self.get(
                reverse(
                    'api-plugin-setting-detail', kwargs={'plugin': 'sample', 'key': key}
                )
            )

            self.assertEqual(response.data['key'], key)

        # Test that an invalid setting key raises a 404 error
        response = self.get(
            reverse(
                'api-plugin-setting-detail',
                kwargs={'plugin': 'sample', 'key': 'INVALID_SETTING'},
            ),
            expected_code=404,
        )

        # Test that a protected setting returns hidden value
        response = self.get(
            reverse(
                'api-plugin-setting-detail',
                kwargs={'plugin': 'sample', 'key': 'PROTECTED_SETTING'},
            ),
            expected_code=200,
        )

        self.assertEqual(response.data['value'], '***')

        # Test that we can update a setting value
        response = self.patch(
            reverse(
                'api-plugin-setting-detail',
                kwargs={'plugin': 'sample', 'key': 'NUMERICAL_SETTING'},
            ),
            {'value': 456},
            expected_code=200,
        )

        self.assertEqual(response.data['value'], 456)

        # Retrieve the value again
        response = self.get(
            reverse(
                'api-plugin-setting-detail',
                kwargs={'plugin': 'sample', 'key': 'NUMERICAL_SETTING'},
            ),
            expected_code=200,
        )

        self.assertEqual(response.data['value'], 456)

    def test_plugin_user_settings(self):
        """Test the PluginUserSetting API endpoints."""
        # Fetch user settings for invalid plugin
        response = self.get(
            reverse(
                'api-plugin-user-setting-list', kwargs={'plugin': 'invalid-plugin'}
            ),
            expected_code=404,
        )

        # Fetch all user settings for the 'email' plugin
        url = reverse(
            'api-plugin-user-setting-list',
            kwargs={'plugin': 'inventree-email-notification'},
        )

        response = self.get(url, expected_code=200)

        settings_keys = [item['key'] for item in response.data]
        self.assertIn('NOTIFY_BY_EMAIL', settings_keys)

        # Fetch user settings for an invalid key
        self.get(
            reverse(
                'api-plugin-user-setting-detail',
                kwargs={'plugin': 'inventree-email-notification', 'key': 'INVALID_KEY'},
            ),
            expected_code=404,
        )

        # Fetch user setting detail for a valid key
        response = self.get(
            reverse(
                'api-plugin-user-setting-detail',
                kwargs={
                    'plugin': 'inventree-email-notification',
                    'key': 'NOTIFY_BY_EMAIL',
                },
            ),
            expected_code=200,
        )

        # User ID must match the current user
        self.assertEqual(response.data['user'], self.user.pk)

        # Check for expected values
        for k in [
            'pk',
            'key',
            'value',
            'name',
            'description',
            'type',
            'model_name',
            'user',
        ]:
            self.assertIn(k, response.data)

    def test_plugin_metadata(self):
        """Test metadata endpoint for plugin."""
        self.user.is_superuser = True
        self.user.save()

        cfg = PluginConfig.objects.filter(key='sample').first()
        self.assertIsNotNone(cfg)

        self.get(f'/api/plugins/{cfg.key}/metadata/', expected_code=200, follow=True)

    def test_settings(self):
        """Test settings endpoint for plugin."""
        from plugin.registry import registry

        registry.set_plugin_state('sample', True)
        url = reverse('api-plugin-settings', kwargs={'plugin': 'sample'})
        self.get(url, expected_code=200)

    def test_registry(self):
        """Test registry endpoint for plugin."""
        url = reverse('api-plugin-registry-status')
        self.get(url, expected_code=403)

        self.user.is_superuser = True
        self.user.save()

        self.get(url, expected_code=200)

        self.user.is_superuser = False
        self.user.save()

    def test_plugin_filter_by_mixin(self):
        """Test filtering plugins by mixin."""
        from plugin import PluginMixinEnum
        from plugin.registry import registry

        # Ensure we have some plugins loaded
        registry.reload_plugins(full_reload=True, collect=True)

        url = reverse('api-plugin-list')

        # Filter by 'mixin' parameter
        mixin_results = {
            PluginMixinEnum.BARCODE: 5,
            PluginMixinEnum.EXPORTER: 4,
            PluginMixinEnum.ICON_PACK: 1,
            PluginMixinEnum.MAIL: 1,
            PluginMixinEnum.NOTIFICATION: 3,
            PluginMixinEnum.USER_INTERFACE: 1,
        }

        for mixin, expected_count in mixin_results.items():
            data = self.get(url, {'mixin': mixin}).data

            self.assertEqual(len(data), expected_count)

            if expected_count > 0:
                for item in data:
                    self.assertIn(mixin, item['mixins'])

    def test_plugin_filters(self):
        """Unit testing for plugin API filters."""
        from plugin.models import PluginConfig
        from plugin.registry import registry

        PluginConfig.objects.all().delete()
        registry.reload_plugins(full_reload=True, collect=True)

        N = PluginConfig.objects.count()
        self.assertGreater(N, 0)

        url = reverse('api-plugin-list')

        data = self.get(url).data

        self.assertGreater(len(data), 0)
        self.assertEqual(len(data), N)

        # Filter by 'builtin' plugins
        data = self.get(url, {'builtin': 'true'}).data

        Y_BUILTIN = len(data)

        for item in data:
            self.assertTrue(item['is_builtin'])

        data = self.get(url, {'builtin': 'false'}).data

        N_BUILTIN = len(data)

        for item in data:
            self.assertFalse(item['is_builtin'])

        self.assertGreater(Y_BUILTIN, 0)
        self.assertGreater(N_BUILTIN, 0)

        self.assertEqual(N_BUILTIN + Y_BUILTIN, N)

        # Filter by 'active' status
        Y_ACTIVE = len(self.get(url, {'active': 'true'}).data)
        N_ACTIVE = len(self.get(url, {'active': 'false'}).data)

        self.assertGreater(Y_ACTIVE, 0)
        self.assertGreater(N_ACTIVE, 0)

        self.assertEqual(Y_ACTIVE + N_ACTIVE, N)

        # Filter by 'sample' status
        Y_SAMPLE = len(self.get(url, {'sample': 'true'}).data)
        N_SAMPLE = len(self.get(url, {'sample': 'false'}).data)

        self.assertGreater(Y_SAMPLE, 0)
        self.assertGreater(N_SAMPLE, 0)

        self.assertEqual(Y_SAMPLE + N_SAMPLE, N)

        # Filter by 'mandatory' status`
        Y_MANDATORY = len(self.get(url, {'mandatory': 'true'}).data)
        N_MANDATORY = len(self.get(url, {'mandatory': 'false'}).data)

        self.assertGreater(Y_MANDATORY, 0)
        self.assertGreater(N_MANDATORY, 0)

        self.assertEqual(Y_MANDATORY + N_MANDATORY, N)

        # Add in a new mandatory plugin
        with self.settings(PLUGINS_MANDATORY=['samplelocate']):
            registry.reload_plugins(full_reload=True, collect=True)

            Y_MANDATORY_2 = len(self.get(url, {'mandatory': 'true'}).data)
            N_MANDATORY_2 = len(self.get(url, {'mandatory': 'false'}).data)

            self.assertEqual(Y_MANDATORY_2, Y_MANDATORY + 1)
            self.assertEqual(N_MANDATORY_2, N_MANDATORY - 1)


class PluginFullAPITest(PluginMixin, InvenTreeAPITestCase):
    """Tests the plugin API endpoints."""

    superuser = True

    @override_settings(PLUGIN_TESTING_SETUP=True)
    def test_full_process(self):
        """Test the full plugin install/uninstall process via API."""
        install_slug = 'inventree-brother-plugin'
        slug = 'brother'

        # Install a plugin
        data = self.post(
            reverse('api-plugin-install'),
            {'confirm': True, 'packagename': install_slug},
            expected_code=201,
            max_query_time=30,
            max_query_count=450,
        ).data

        self.assertEqual(data['success'], 'Installed plugin successfully')

        # Activate the plugin
        data = self.patch(
            reverse('api-plugin-detail-activate', kwargs={'plugin': slug}),
            data={'active': True},
            max_query_count=450,
        ).data

        self.assertEqual(data['active'], True)

        # Check if the plugin is installed
        test_plg = PluginConfig.objects.get(key=slug)
        self.assertIsNotNone(test_plg, 'Test plugin not found')
        self.assertTrue(test_plg.is_active())

        # De-activate and uninstall the plugin
        data = self.patch(
            reverse('api-plugin-detail-activate', kwargs={'plugin': slug}),
            data={'active': False},
            max_query_count=380,
        ).data
        self.assertEqual(data['active'], False)
        response = self.patch(
            reverse('api-plugin-uninstall', kwargs={'plugin': slug}),
            data={'delete_config': True},
            max_query_count=350,
        )
        self.assertEqual(response.status_code, 200)

        from django.conf import settings

        if not settings.DOCKER:
            # This test fails if running inside docker container
            # TODO: Work out why...

            # Successful uninstallation
            with self.assertRaises(PluginConfig.DoesNotExist):
                PluginConfig.objects.get(key=slug)

    @override_settings(PLUGIN_TESTING_SETUP=True)
    def test_registry(self):
        """Test install with a custom registry."""
        plrg_name = 'inventree-dummy-app-plugin'

        # install - python repository url and package name
        data = self.post(
            reverse('api-plugin-install'),
            {
                'confirm': True,
                'url': 'https://git.invenhost.com/api/packages/invenhost-c1/pypi/simple/',
                'packagename': plrg_name,
            },
            expected_code=201,
            max_query_count=450,
            max_query_time=30,
        ).data
        self.assertEqual(data['success'], 'Installed plugin successfully')

        # # and uninstall it again to clean up
        # response = self.patch(
        #     reverse('api-plugin-uninstall', kwargs={'plugin': plrg_name}),
        #     data={'delete_config': True},
        #     max_query_count=350,
        # )
        # self.assertEqual(response.status_code, 200)


class PluginLockedSettingsTest(PluginMixin, InvenTreeAPITestCase):
    """Tests for locked plugin settings (overridden via configuration).

    When a plugin setting is specified in PLUGIN_SETTING_OVERRIDES:
    - The API reports read_only=True for that setting
    - The stored value always reflects the override, even after a PATCH attempt
    - Other settings on the same plugin remain editable (read_only=False)
    """

    superuser = True

    PLUGIN_SLUG = 'sample'

    # Two settings from the sample plugin used across these tests
    LOCKED_KEY = 'API_KEY'
    LOCKED_VALUE = 'locked-api-key-value'

    LOCKED_NUMERIC_KEY = 'NUMERICAL_SETTING'
    LOCKED_NUMERIC_VALUE = 42

    UNLOCKED_KEY = 'CHOICE_SETTING'

    def setUp(self):
        """Activate the sample plugin and confirm it is ready."""
        super().setUp()

        from plugin.registry import registry

        registry.set_plugin_state(self.PLUGIN_SLUG, True)

        self.cfg = PluginConfig.objects.filter(key=self.PLUGIN_SLUG).first()
        self.assertIsNotNone(self.cfg)

    def _setting_url(self, key):
        return reverse(
            'api-plugin-setting-detail', kwargs={'plugin': self.PLUGIN_SLUG, 'key': key}
        )

    # ------------------------------------------------------------------
    # Helper that supplies the override context for all locked-setting tests
    # ------------------------------------------------------------------
    def _overrides(self):
        return {
            self.PLUGIN_SLUG: {
                self.LOCKED_KEY: self.LOCKED_VALUE,
                self.LOCKED_NUMERIC_KEY: self.LOCKED_NUMERIC_VALUE,
            }
        }

    def test_locked_setting_read_only_flag(self):
        """Locked settings must be reported as read_only=True via the API."""
        with self.settings(PLUGIN_SETTING_OVERRIDES=self._overrides()):
            response = self.get(self._setting_url(self.LOCKED_KEY), expected_code=200)
            self.assertTrue(response.data['read_only'])

    def test_unlocked_setting_not_read_only(self):
        """Settings that are NOT overridden must be reported as read_only=False."""
        with self.settings(PLUGIN_SETTING_OVERRIDES=self._overrides()):
            response = self.get(self._setting_url(self.UNLOCKED_KEY), expected_code=200)
            self.assertFalse(response.data['read_only'])

    def test_locked_setting_returns_override_value(self):
        """GET on a locked setting must return the configured override value."""
        with self.settings(PLUGIN_SETTING_OVERRIDES=self._overrides()):
            response = self.get(self._setting_url(self.LOCKED_KEY), expected_code=200)
            self.assertEqual(response.data['value'], self.LOCKED_VALUE)

    def test_locked_setting_model_get(self):
        """PluginSetting.get_setting() must return the override value directly."""
        with self.settings(PLUGIN_SETTING_OVERRIDES=self._overrides()):
            value = PluginSetting.get_setting(self.LOCKED_KEY, plugin=self.cfg)
            self.assertEqual(value, self.LOCKED_VALUE)

            numeric = PluginSetting.get_setting(
                self.LOCKED_NUMERIC_KEY, plugin=self.cfg
            )
            self.assertEqual(numeric, self.LOCKED_NUMERIC_VALUE)

    def test_locked_setting_patch_ignored(self):
        """PATCH to a locked setting must not change the value; override is re-applied."""
        with self.settings(PLUGIN_SETTING_OVERRIDES=self._overrides()):
            response = self.patch(
                self._setting_url(self.LOCKED_KEY),
                {'value': 'attacker-supplied-value'},
                expected_code=200,
            )
            # The response value must reflect the override, not the submitted value
            self.assertEqual(response.data['value'], self.LOCKED_VALUE)

            # Confirm persistence: a subsequent GET also returns the locked value
            response = self.get(self._setting_url(self.LOCKED_KEY), expected_code=200)
            self.assertEqual(response.data['value'], self.LOCKED_VALUE)

    def test_locked_numeric_setting_patch_ignored(self):
        """PATCH to a locked numeric setting must not change the value."""
        with self.settings(PLUGIN_SETTING_OVERRIDES=self._overrides()):
            response = self.patch(
                self._setting_url(self.LOCKED_NUMERIC_KEY),
                {'value': 999},
                expected_code=200,
            )
            self.assertEqual(int(response.data['value']), self.LOCKED_NUMERIC_VALUE)

    def test_unlocked_setting_can_be_changed(self):
        """Settings not in the override dict must still be freely editable."""
        with self.settings(PLUGIN_SETTING_OVERRIDES=self._overrides()):
            # Set an initial known value
            self.patch(
                self._setting_url(self.UNLOCKED_KEY), {'value': 'A'}, expected_code=200
            )
            response = self.get(self._setting_url(self.UNLOCKED_KEY), expected_code=200)
            self.assertEqual(response.data['value'], 'A')

            # Change it again to confirm mutability
            self.patch(
                self._setting_url(self.UNLOCKED_KEY), {'value': 'B'}, expected_code=200
            )
            response = self.get(self._setting_url(self.UNLOCKED_KEY), expected_code=200)
            self.assertEqual(response.data['value'], 'B')

    def test_locked_setting_model_save_enforced(self):
        """Saving a PluginSetting instance directly must enforce the override value."""
        with self.settings(PLUGIN_SETTING_OVERRIDES=self._overrides()):
            # Retrieve (or create) the DB object and try to write a different value
            obj = PluginSetting.get_setting_object(self.LOCKED_KEY, plugin=self.cfg)
            self.assertIsNotNone(obj)

            obj.value = 'should-be-overwritten'
            obj.save()

            # Re-fetch from DB to confirm the override was enforced
            obj.refresh_from_db()
            self.assertEqual(obj.value, self.LOCKED_VALUE)

    def test_no_overrides_settings_are_editable(self):
        """Without any PLUGIN_SETTING_OVERRIDES, all settings default to read_only=False."""
        with self.settings(PLUGIN_SETTING_OVERRIDES={}):
            for key in [self.LOCKED_KEY, self.LOCKED_NUMERIC_KEY, self.UNLOCKED_KEY]:
                response = self.get(self._setting_url(key), expected_code=200)
                self.assertFalse(
                    response.data['read_only'], msg=f'{key} should not be read_only'
                )
