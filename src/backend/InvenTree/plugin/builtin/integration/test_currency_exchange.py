"""Tests for the builtin currency exchange plugin."""

from unittest import mock

from django.core.exceptions import ValidationError
from django.test import TestCase

from plugin.builtin.integration import iranian_currency_exchange as iran_exchange

TGJU_TABLE_HTML = """
<html>
  <head><meta charset="UTF-8"></head>
  <body>
    <table>
      <tr data-market-row="price_dollar_rl" data-price="\u06f1\u066c\u06f8\u06f7\u06f8\u066c\u06f0\u06f0\u06f0"></tr>
    </table>
  </body>
</html>
""".encode()

TGJU_STICKY_HTML = b"""
<html>
  <body>
    <li id="l-price_dollar_rl">
      <span><span class="info-price">1,878,000</span></span>
    </li>
  </body>
</html>
"""

TGJU_PROFILE_HTML = b"""
<html>
  <body>
    <div data-target="profile-tour-current_rate">
      <span class="price" data-col="info.last_trade.PDrCotVal">1,878,000</span>
    </div>
  </body>
</html>
"""


class IranianCurrencyExchangeTests(TestCase):
    """Test Iranian rial currency exchange behavior."""

    def setUp(self):
        """Create a currency exchange plugin instance."""
        self.plugin = iran_exchange.IranianCurrencyExchange()

    def plugin_settings(self, *, api_enabled=False, manual_rate=0):
        """Return deterministic plugin settings for a test."""
        values = {'API_ENABLED': api_enabled, 'USD_IRR_RATE': manual_rate}

        return mock.patch.object(
            self.plugin, 'get_setting', side_effect=lambda key: values[key]
        )

    def test_irr_settings_are_available(self):
        """Expose API selection and manual USD to IRR rate settings."""
        self.assertIn('API_ENABLED', self.plugin.SETTINGS)
        self.assertNotIn('USE_API', self.plugin.SETTINGS)
        self.assertIn('USD_IRR_RATE', self.plugin.SETTINGS)
        self.assertNotIn('API_KEY', self.plugin.SETTINGS)
        self.assertNotIn('API_VALUE_UNIT', self.plugin.SETTINGS)

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
            mock.patch.object(self.plugin, '_tgju_rate') as tgju_rate,
        ):
            rates = self.plugin.update_exchange_rates('USD', ['USD', 'IRR'])

        tgju_rate.assert_not_called()
        self.assertEqual(rates, {'USD': 1.0, 'IRR': 1_878_000.0})

    @mock.patch.object(iran_exchange.requests, 'get')
    def test_tgju_currency_xpath_usd_irr_rate(self, request_get):
        """Extract the free-market USD rate from TGJU's semantic table row."""
        request_get.return_value.content = TGJU_TABLE_HTML

        with self.plugin_settings(api_enabled=True):
            rates = self.plugin.update_exchange_rates('USD', ['USD', 'IRR'])

        request_get.assert_called_once_with(
            'https://www.tgju.org/currency',
            headers={
                'Accept': 'text/html',
                'User-Agent': 'InvenTree Iranian Currency Exchange/1.0',
            },
            timeout=10,
        )
        self.assertEqual(rates, {'USD': 1.0, 'IRR': 1_878_000.0})

    @mock.patch.object(iran_exchange.requests, 'get')
    def test_tgju_reference_selector_xpath_usd_irr_rate(self, request_get):
        """Support the TGJU element used by dollar-tomans-api."""
        request_get.return_value.content = TGJU_STICKY_HTML

        with self.plugin_settings(api_enabled=True):
            rates = self.plugin.update_exchange_rates('USD', ['USD', 'IRR'])

        self.assertEqual(request_get.call_count, 1)
        self.assertEqual(rates, {'USD': 1.0, 'IRR': 1_878_000.0})

    @mock.patch.object(iran_exchange.requests, 'get')
    def test_tgju_profile_xpath_fallback(self, request_get):
        """Fall back to TGJU's USD profile when the currency page changes."""
        currency_response = mock.Mock(content=b'<html></html>')
        profile_response = mock.Mock(content=TGJU_PROFILE_HTML)
        request_get.side_effect = [currency_response, profile_response]

        with self.plugin_settings(api_enabled=True):
            rates = self.plugin.update_exchange_rates('USD', ['USD', 'IRR'])

        self.assertEqual(
            [call.args[0] for call in request_get.call_args_list],
            [
                'https://www.tgju.org/currency',
                'https://www.tgju.org/profile/price_dollar_rl',
            ],
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

    def test_missing_irr_aborts_update(self):
        """Do not clear the stored IRR rate when IRR is not configured."""
        with self.plugin_settings(manual_rate=2_000_000):
            rates = self.plugin.update_exchange_rates('USD', ['USD'])

        self.assertEqual(rates, {})

    def test_invalid_manual_rate_aborts_update(self):
        """Do not replace stored rates when the configured rate is invalid."""
        with self.plugin_settings(manual_rate=0):
            rates = self.plugin.update_exchange_rates('USD', ['USD', 'IRR'])

        self.assertEqual(rates, {})

    @mock.patch.object(iran_exchange.requests, 'get')
    def test_invalid_tgju_html_aborts_update(self, request_get):
        """Do not replace stored rates when neither TGJU XPath matches."""
        request_get.return_value.content = b'<html></html>'

        with self.plugin_settings(api_enabled=True):
            rates = self.plugin.update_exchange_rates('USD', ['USD', 'IRR'])

        self.assertEqual(request_get.call_count, 2)
        self.assertEqual(rates, {})

    def test_tgju_refresh_is_scheduled_every_three_hours(self):
        """Refresh the TGJU rate every three hours."""
        self.assertEqual(
            self.plugin.get_scheduled_tasks(),
            {
                'refresh_usd_irr': {
                    'func': 'refresh_usd_irr',
                    'schedule': 'I',
                    'minutes': 180,
                }
            },
        )

    @mock.patch('InvenTree.tasks.update_exchange_rates')
    def test_scheduled_refresh_exits_when_api_is_disabled(self, update_rates):
        """Do not consume TGJU while its switch is disabled."""
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
        """Force a rate update when TGJU consumption is enabled and selected."""
        with (
            self.plugin_settings(api_enabled=True),
            mock.patch.object(
                iran_exchange, 'get_global_setting', return_value=self.plugin.slug
            ),
        ):
            self.plugin.refresh_usd_irr()

        update_rates.assert_called_once_with(force=True)
