from djmoney.contrib.exchange.backends.base import BaseExchangeBackend


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
