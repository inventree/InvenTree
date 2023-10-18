"""Builtin plugin for requesting exchange rates from an external API."""


import logging

from django.utils.translation import gettext_lazy as _

from plugin import InvenTreePlugin
from plugin.mixins import APICallMixin, CurrencyExchangeMixin

logger = logging.getLogger('inventree')


class InvenTreeCurrencyExchange(APICallMixin, CurrencyExchangeMixin, InvenTreePlugin):
    """Default InvenTree plugin for currency exchange rates.

    Fetches exchange rate information from frankfurter.app
    """

    NAME = "InvenTreeCurrencyExchange"
    SLUG = "inventreecurrencyexchange"
    AUTHOR = _('InvenTree contributors')
    TITLE = _("InvenTree Currency Exchange")
    DESCRIPTION = _("Default currency exchange integration")
    VERSION = "1.0.0"

    def update_exchange_rates(self, base_currency: str, symbols: list[str]) -> dict:
        """Request exchange rate data from external API"""
        response = self.api_call(
            'latest',
            url_args={
                'from': [base_currency],
                'to': symbols,
            },
            simple_response=False
        )

        if response.status_code == 200:

            rates = response.json().get('rates', {})
            rates[base_currency] = 1.00

            return rates
        logger.warning("Failed to update exchange rates from %s: Server returned status %s", self.api_url, response.status_code)
        return None

    @property
    def api_url(self):
        """Return the API URL for this plugin"""
        return 'https://api.frankfurter.app'
