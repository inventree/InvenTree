from django.conf import settings as inventree_settings

from djmoney import settings as djmoney_settings
from djmoney.contrib.exchange.backends.base import BaseExchangeBackend
from djmoney.contrib.exchange.backends import FixerBackend

from common.models import InvenTreeSetting


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


class InvenTreeFixerExchangeBackend(FixerBackend):
    """
    Backend for updating currency exchange rates using Fixer.IO API
    """

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

        super().__init__(url=djmoney_settings.FIXER_URL, access_key=fixer_api_key)

    def update_rates(self):
        """ Override update_rates method using currencies found in the settings """

        currencies = ','.join(inventree_settings.CURRENCIES)

        base = inventree_settings.BASE_CURRENCY

        super().update_rates(base_currency=base, symbols=currencies)

    def get_rates(self, **kwargs):
        """ Returns a mapping <currency>: <rate> """

        return {}
