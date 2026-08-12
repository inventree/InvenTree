"""Tests for the builtin currency exchange plugin."""

from unittest import mock

from django.core.exceptions import ValidationError
from django.test import TestCase

from plugin.builtin.integration import iranian_currency_exchange as iran_exchange


class IranianCurrencyExchangeTests(TestCase):
    """Test Iranian rial currency exchange behavior."""

    def setUp(self):
        """Create a currency exchange plugin instance."""
        self.plugin = iran_exchange.IranianCurrencyExchange()

    def plugin_settings(
        self, *, api_enabled=False, manual_rate=0, api_key='test-key', api_unit='IRT'
    ):
        """Return deterministic plugin settings for a test."""
        values = {
            'API_ENABLED': api_enabled,
            'USD_IRR_RATE': manual_rate,
            'API_KEY': api_key,
            'API_VALUE_UNIT': api_unit,
        }

        return mock.patch.object(
            self.plugin, 'get_setting', side_effect=lambda key: values[key]
        )

    def test_irr_settings_are_available(self):
        """Expose API selection and manual USD to IRR rate settings."""
        self.assertIn('API_ENABLED', self.plugin.SETTINGS)
        self.assertNotIn('USE_API', self.plugin.SETTINGS)
        self.assertIn('USD_IRR_RATE', self.plugin.SETTINGS)
        self.assertIn('API_KEY', self.plugin.SETTINGS)
        self.assertIn('API_VALUE_UNIT', self.plugin.SETTINGS)
        self.assertFalse(self.plugin.SETTINGS['API_VALUE_UNIT'].get('required', False))

    def test_manual_rate_setting_requires_positive_finite_value(self):
        """Reject manual rates which cannot be used for conversion."""
        validator = self.plugin.SETTINGS['USD_IRR_RATE']['validator'][-1]

        for value in [0, -1, float('nan'), float('inf')]:
            with self.subTest(value=value), self.assertRaises(ValidationError):
                validator(value)

        validator(1_878_000)

    def test_manual_usd_irr_rate(self):
        """Use configured rial per dollar value without a network request."""
        with (
            self.plugin_settings(api_enabled=False, manual_rate=1_878_000),
            mock.patch.object(self.plugin, '_api_rate') as api_rate,
        ):
            rates = self.plugin.update_exchange_rates('USD', ['USD', 'IRR'])

        api_rate.assert_not_called()
        self.assertEqual(rates, {'USD': 1.0, 'IRR': 1_878_000.0})

    @mock.patch.object(iran_exchange.requests, 'get')
    def test_api_usd_irr_rate(self, request_get):
        """Read and normalize the latest Navasan USD sell rate."""
        request_get.return_value.json.return_value = {
            'usd_sell': {
                'value': '۱۸۷٬۸۰۰',
                'timestamp': 1_786_406_400,
                'date': '1405-05-21 12:00:00',
            }
        }

        with self.plugin_settings(api_enabled=True):
            rates = self.plugin.update_exchange_rates('USD', ['USD', 'IRR'])

        request_get.assert_called_once_with(
            'https://api.navasan.tech/latest/',
            params={'item': 'usd_sell', 'api_key': 'test-key'},
            headers={'Accept': 'application/json'},
            timeout=10,
        )
        self.assertEqual(rates, {'USD': 1.0, 'IRR': 1_878_000.0})

    def test_irr_base_aborts_update(self):
        """Reject an IRR base because stored reciprocal precision is insufficient."""
        with self.plugin_settings(manual_rate=2_000_000):
            rates = self.plugin.update_exchange_rates('IRR', ['IRR', 'USD'])

        self.assertEqual(rates, {})

    def test_unsupported_currency_aborts_update(self):
        """Reject configurations outside the USD and IRR phase-one scope."""
        with self.plugin_settings(manual_rate=2_000_000):
            rates = self.plugin.update_exchange_rates('USD', ['USD', 'IRR', 'EUR'])

        self.assertEqual(rates, {})

    def test_invalid_manual_rate_aborts_update(self):
        """Do not replace stored rates when the configured rate is invalid."""
        with self.plugin_settings(manual_rate=0):
            rates = self.plugin.update_exchange_rates('USD', ['USD', 'IRR'])

        self.assertEqual(rates, {})

    @mock.patch.object(iran_exchange.requests, 'get')
    def test_invalid_api_response_aborts_update(self, request_get):
        """Do not replace stored rates when Navasan returns malformed data."""
        request_get.return_value.json.return_value = {'usd_sell': {}}

        with self.plugin_settings(api_enabled=True):
            rates = self.plugin.update_exchange_rates('USD', ['USD', 'IRR'])

        self.assertEqual(rates, {})

    def test_api_refresh_is_scheduled_every_eight_hours(self):
        """Refresh within Navasan's free monthly request allowance."""
        self.assertEqual(
            self.plugin.get_scheduled_tasks(),
            {
                'refresh_usd_irr': {
                    'func': 'refresh_usd_irr',
                    'schedule': 'I',
                    'minutes': 480,
                }
            },
        )

    @mock.patch('InvenTree.tasks.update_exchange_rates')
    def test_scheduled_refresh_exits_when_api_is_disabled(self, update_rates):
        """Do not consume the API while its switch is disabled."""
        with self.plugin_settings(api_enabled=False):
            self.plugin.refresh_usd_irr()

        update_rates.assert_not_called()

    @mock.patch('InvenTree.tasks.update_exchange_rates')
    def test_scheduled_refresh_exits_when_plugin_is_not_selected(self, update_rates):
        """Do not refresh rates when another currency plugin is selected."""
        with (
            self.plugin_settings(api_enabled=True),
            mock.patch.object(
                iran_exchange,
                'get_global_setting',
                return_value='another-currency-plugin',
            ),
        ):
            self.plugin.refresh_usd_irr()

        update_rates.assert_not_called()

    @mock.patch('InvenTree.tasks.update_exchange_rates')
    def test_scheduled_refresh_updates_selected_api_plugin(self, update_rates):
        """Force a rate update when API consumption is enabled and selected."""
        with (
            self.plugin_settings(api_enabled=True),
            mock.patch.object(
                iran_exchange, 'get_global_setting', return_value=self.plugin.slug
            ),
        ):
            self.plugin.refresh_usd_irr()

        update_rates.assert_called_once_with(force=True)
