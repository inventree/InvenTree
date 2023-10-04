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

    EXCHANGE_URL = 'https://frankfurter.app'

    def update_exchange_rates(self, base_currency: str, symbols: list[str]) -> dict:
        """Request exchange rate data from external API"""

        print("updating exchange rates:", base_currency, symbols)
        return None
