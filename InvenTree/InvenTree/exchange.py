from common.settings import currency_code_default, currency_codes
from urllib.error import HTTPError, URLError

from djmoney.contrib.exchange.backends.base import SimpleExchangeBackend


class InvenTreeExchange(SimpleExchangeBackend):
    """
    Backend for automatically updating currency exchange rates.

    Uses the exchangerate.host service API
    """

    name = "InvenTreeExchange"

    def __init__(self):
        self.url = "https://api.exchangerate.host/latest"

        super().__init__()

    def get_params(self):
        # No API key is required
        return {
        }

    def update_rates(self, base_currency=currency_code_default()):

        symbols = ','.join(currency_codes())

        try:
            super().update_rates(base=base_currency, symbols=symbols)
        # catch connection errors
        except (HTTPError, URLError):
            print('Encountered connection error while updating')
