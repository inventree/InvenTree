"""Tests for the various validators in the settings."""

from unittest import mock

from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings

import common.setting.system
from common.setting.system import SYSTEM_SETTINGS, collect_system_settings


class SettingsTests(TestCase):
    """Tests settings behaviour."""

    def test_collection(self):
        """Test collection of system settings."""
        # old keys are still there
        for key in ['STOCKTAKE_ENABLE', 'STOCK_STALE_DAYS', 'PRICING_DECIMAL_PLACES']:
            self.assertIn(key, SYSTEM_SETTINGS)

        # Re-run causes no issues
        count = len(SYSTEM_SETTINGS)
        collect_system_settings()
        self.assertEqual(len(SYSTEM_SETTINGS), count)

        # Duplicates cause an error
        with mock.patch('common.setting.system._settings_collected', False):
            with self.assertRaises(ValueError):
                collect_system_settings()

    def test_get_global_setting_unexpected_kwargs(self):
        """Unexpected keyword arguments are dropped, rather than forwarded."""
        from common.models import InvenTreeSetting
        from common.settings import get_global_setting

        with (
            mock.patch.object(
                InvenTreeSetting, 'get_setting', return_value=True
            ) as get_setting,
            mock.patch('common.settings.logger') as logger,
        ):
            get_global_setting(
                'BARCODE_STORE_RESULTS', backup=False, default='', create=False
            )

        get_setting.assert_called_once_with('BARCODE_STORE_RESULTS', create=False)
        logger.warning.assert_called_once()

    @override_settings(
        CACHES={
            'default': {
                'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
                'LOCATION': 'settings-cache-test',
            }
        }
    )
    def test_get_global_setting_cache_hit(self):
        """Unexpected keyword arguments must not cause global cache misses.

        Previously, any extra kwarg became part of the cache key. As the global
        cache is always populated under the canonical key, such lookups never hit
        the cache, and required a database query on every call.
        """
        from django.core.cache import cache

        from common.settings import get_global_setting, set_global_setting

        cache.clear()

        set_global_setting('BARCODE_STORE_RESULTS', True)

        # Prime the global cache
        self.assertTrue(get_global_setting('BARCODE_STORE_RESULTS', cache=True))

        with self.assertNumQueries(0):
            self.assertTrue(
                get_global_setting(
                    'BARCODE_STORE_RESULTS', backup=False, create=False, cache=True
                )
            )

        cache.clear()

    def test_update_instance_name_no_multi(self):
        """Test valid cases for update_instance_name."""
        self.assertIsNone(common.setting.system.update_instance_name('abc'))

    def test_update_instance_url_no_multi(self):
        """Test update_instance_url."""
        self.assertIsNone(common.setting.system.update_instance_url('abc.com'))

    @override_settings(SITE_URL=None)
    def test_base_url_validator(self):
        """Test valid and invalid base URL values."""
        validator = common.setting.system.BaseURLValidator()

        for value in ['', 'http://localhost', 'https://inventree.example']:
            self.assertIsNone(validator(value))

        for value in ['inventree', 'ftp://inventree']:
            with self.assertRaises(ValidationError):
                validator(value)

    @override_settings(SITE_URL='https://inventree.example')
    def test_base_url_validator_locked_by_configuration(self):
        """Test that a configured site URL cannot be changed."""
        validator = common.setting.system.BaseURLValidator()

        self.assertIsNone(validator('https://inventree.example'))

        with self.assertRaisesMessage(
            ValidationError, 'Site URL is locked by configuration'
        ):
            validator('https://other.example')
