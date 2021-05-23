from djmoney.contrib.exchange.backends.base import BaseExchangeBackend, SimpleExchangeBackend


class InvenTreeManualExchangeBackend(BaseExchangeBackend):
    """
    Backend for manually updating currency exchange rates

    See the documentation for django-money: https://github.com/django-money/django-money

    Specifically: https://github.com/django-money/django-money/tree/master/djmoney/contrib/exchange/backends
    """

    name = "inventree"
    url = None

    def get_rates(self, **kwargs):
        """
        Do not get any rates...
        """

        return {}


class ExchangeRateHostBackend(SimpleExchangeBackend):
    """
    Backend for https://exchangerate.host/
    """

    name = "exchangerate.host"

    def __init__(self):
        self.url = "https://api.exchangerate.host/latest"

    def get_params(self):
        # No API key is required
        return {}
