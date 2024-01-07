"""Sample plugin for providing dummy currency exchange data"""

import random

from django.utils.translation import gettext_lazy as _

from plugin import InvenTreePlugin
from plugin.mixins import CurrencyExchangeMixin


class SampleCurrencyExchangePlugin(CurrencyExchangeMixin, InvenTreePlugin):
    """Dummy currency exchange plugin which provides fake exchange rates"""

    NAME = "Sample Exchange"
    DESCRIPTION = _("Sample currency exchange plugin")
    SLUG = "samplecurrencyexchange"
    VERSION = "0.1.0"
    AUTHOR = _("InvenTree Contributors")

    def update_exchange_rates(self, base_currency: str, symbols: list[str]) -> dict:
        """Return dummy data for some currencies"""
        rates = {base_currency: 1.00}

        for symbol in symbols:
            rates[symbol] = random.randrange(5, 15) * 0.1

        return rates
