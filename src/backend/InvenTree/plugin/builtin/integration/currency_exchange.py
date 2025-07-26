"""Builtin plugin for requesting exchange rates from an external API."""

from django.utils.translation import gettext_lazy as _

import structlog

from plugin import InvenTreePlugin
from plugin.mixins import APICallMixin, CurrencyExchangeMixin, SettingsMixin

logger = structlog.get_logger('inventree')


class InvenTreeCurrencyExchange(APICallMixin, CurrencyExchangeMixin, InvenTreePlugin):
    """Default InvenTree plugin for currency exchange rates.

    Fetches exchange rate information from frankfurter.app
    """

    NAME = 'InvenTreeCurrencyExchange'
    SLUG = 'inventreecurrencyexchange'
    AUTHOR = _('InvenTree contributors')
    TITLE = _('InvenTree Currency Exchange')
    DESCRIPTION = _('Default currency exchange integration')
    VERSION = '1.0.0'

    def update_exchange_rates(self, base_currency: str, symbols: list[str]) -> dict:
        """Request exchange rate data from external API."""
        response = self.api_call(
            'latest',
            url_args={'from': [base_currency], 'to': symbols},
            simple_response=False,
        )

        if response.status_code == 200:
            rates = response.json().get('rates', {})
            rates[base_currency] = 1.00

            return rates
        logger.warning(
            'Failed to update exchange rates from %s: Server returned status %s',
            self.api_url,
            response.status_code,
        )
        return {}

    @property
    def api_url(self):
        """Return the API URL for this plugin."""
        return 'https://api.frankfurter.app'


class ExchangeRateHostPlugin(
    APICallMixin, CurrencyExchangeMixin, SettingsMixin, InvenTreePlugin
):
    """Plugin for fetching exchange rates from a exchangerate.host.

    This plugin requires an API key to be set in the plugin settings.
    """

    SLUG = 'exchangeratehost'
    AUTHOR = _('InvenTree contributors')
    NAME = _('ExchangeRate.host Exchange')
    DESCRIPTION = _('Fetches currency exchange rates from the exchangerate.host API')
    VERSION = '1.0.0'

    SETTINGS = {
        'API_KEY': {
            'name': _('API Key'),
            'description': _('API key for exchangerate.host'),
            'default': '',
        }
    }

    @property
    def api_url(self):
        """Return the API URL for this plugin."""
        return 'https://api.exchangerate.host'

    def update_exchange_rates(self, base_currency: str, symbols: list[str]) -> dict:
        """Request exchange rate data from exchangerate.host."""
        api_key = self.get_setting('API_KEY', backup_value='')

        if not api_key:
            logger.warning('API key for exchangerate.host is not set.')
            return {}

        response = self.api_call(
            'live',
            url_args={'access_key': api_key, 'source': base_currency},
            simple_response=False,
        )

        if response.status_code != 200:
            logger.warning(
                'Failed to update exchange rates from %s: Server returned status %s',
                self.api_url,
                response.status_code,
            )
            return {}

        data = response.json().get('quotes', None) or {}

        rates = {}

        for symbol in symbols:
            # The API returns rates in the format 'USDAUD', where 'USD' is the base currency, and 'AUD' (e.g.) is the target currency.
            if rate := data.get(f'{base_currency}{symbol}', None):
                rates[symbol] = rate

        return rates
