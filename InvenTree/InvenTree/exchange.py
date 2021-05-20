from django.core.exceptions import ImproperlyConfigured
from django.conf import settings as inventree_settings

from djmoney import settings as djmoney_settings
from djmoney.contrib.exchange.backends.base import BaseExchangeBackend

from common.models import InvenTreeSetting


def get_exchange_rate_backend():
    """ Return the exchange rate backend set by user """

    if 'InvenTreeManualExchangeBackend' in inventree_settings.EXCHANGE_BACKEND:
        return InvenTreeManualExchangeBackend()
    else:
        return InvenTreeFixerExchangeBackend()


class InvenTreeManualExchangeBackend(BaseExchangeBackend):
    """
    Backend for manually updating currency exchange rates

    See the documentation for django-money: https://github.com/django-money/django-money

    Specifically: https://github.com/django-money/django-money/tree/master/djmoney/contrib/exchange/backends
    """

    name = 'inventree'
    url = None
    default_currency = None
    currencies = []

    def update_default_currency(self):

        self.default_currency = InvenTreeSetting.get_setting('INVENTREE_DEFAULT_CURRENCY', inventree_settings.BASE_CURRENCY)

    def __init__(self, url=None):

        self.url = url

        self.update_default_currency()

        self.currencies = inventree_settings.CURRENCIES

        super().__init__()

    def get_rates(self, **kwargs):
        """ Returns a mapping <currency>: <rate> """

        return {}


class InvenTreeFixerExchangeBackend(InvenTreeManualExchangeBackend):
    """
    Backend for updating currency exchange rates using Fixer.IO API
    """

    name = 'fixer.io'
    access_key = None

    def get_api_key(self):
        """ Get API key from global settings """

        fixer_api_key = InvenTreeSetting.get_setting('INVENTREE_FIXER_API_KEY', '').strip()

        if not fixer_api_key:
            # API key not provided
            return None

        return fixer_api_key

    def __init__(self):
        """ Override FixerBackend init to get access_key from global settings """

        fixer_api_key = self.get_api_key()

        if fixer_api_key is None:
            raise ImproperlyConfigured("fixer.io API key is needed to use InvenTreeFixerExchangeBackend")
        
        self.access_key = fixer_api_key

        super().__init__(url=djmoney_settings.FIXER_URL)

    def update_rates(self):
        """ Override update_rates method using currencies found in the settings
        """
        
        symbols = ','.join(self.currencies)

        super().update_rates(base_currency=self.base_currency, symbols=symbols)
