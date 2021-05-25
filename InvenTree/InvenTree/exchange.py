from django.core.exceptions import ImproperlyConfigured
from django.conf import settings as inventree_settings

from djmoney import settings as djmoney_settings
from djmoney.contrib.exchange.backends.base import BaseExchangeBackend
from djmoney.contrib.exchange.models import Rate

from common.models import InvenTreeSetting


def get_exchange_rate_backend():
    """ Return the exchange rate backend set by user """

    if 'InvenTreeManualExchangeBackend' in inventree_settings.EXCHANGE_BACKEND:
        return InvenTreeManualExchangeBackend()
    elif 'InvenTreeFixerExchangeBackend' in inventree_settings.EXCHANGE_BACKEND:
        return InvenTreeFixerExchangeBackend()
    else:
        raise ImproperlyConfigured('Exchange Backend wrongly configured')


class InvenTreeManualExchangeBackend(BaseExchangeBackend):
    """
    Backend for manually updating currency exchange rates

    See the documentation for django-money: https://github.com/django-money/django-money

    Specifically: https://github.com/django-money/django-money/tree/master/djmoney/contrib/exchange/backends
    """

    name = 'inventree'
    url = None
    base_currency = None
    currencies = []

    def update_default_currency(self):
        """ Update to base currency """

        self.base_currency = InvenTreeSetting.get_setting('INVENTREE_DEFAULT_CURRENCY', inventree_settings.BASE_CURRENCY)

    def __init__(self, url=None):
        """ Overrides init to update url, base currency and currencies """

        self.url = url

        self.update_default_currency()

        # Update name
        self.name = self.name + '-' + self.base_currency.lower()

        self.currencies = inventree_settings.CURRENCIES

        super().__init__()

    def get_rates(self, **kwargs):
        """ Returns a mapping <currency>: <rate> """

        return kwargs.get('rates', {})

    def get_stored_rates(self):
        """ Returns stored rate for specified backend and base currency """

        stored_rates = {}

        stored_rates_obj = Rate.objects.all().prefetch_related('backend')

        for rate in stored_rates_obj:
            # Find match for backend and base currency
            if rate.backend.name == self.name and rate.backend.base_currency == self.base_currency:
                # print(f'{rate.currency} | {rate.value} | {rate.backend} | {rate.backend.base_currency}')
                stored_rates[rate.currency] = rate.value

        return stored_rates


class InvenTreeFixerExchangeBackend(InvenTreeManualExchangeBackend):
    """
    Backend for updating currency exchange rates using Fixer.IO API
    """

    name = 'fixer'
    access_key = None

    def get_api_key(self):
        """ Get API key from global settings """

        fixer_api_key = InvenTreeSetting.get_setting('INVENTREE_FIXER_API_KEY', '').strip()

        if not fixer_api_key:
            # API key not provided
            return None

        self.access_key = fixer_api_key

    def __init__(self):
        """ Override init to get access_key from global settings """

        self.get_api_key()

        if self.access_key is None:
            raise ImproperlyConfigured("fixer.io API key is needed to use InvenTreeFixerExchangeBackend")
        
        super().__init__(url=djmoney_settings.FIXER_URL)

    def get_params(self):
        """ Returns parameters (access key) """

        return {"access_key": self.access_key}

    def update_rates(self, base_currency=None):
        """ Override update_rates method using currencies found in the settings
        """

        if base_currency:
            self.base_currency = base_currency
        else:
            self.update_default_currency()
        
        symbols = ','.join(self.currencies)

        super().update_rates(base_currency=self.base_currency, symbols=symbols)

    def get_rates(self, **params):
        """ Returns a mapping <currency>: <rate> """

        # Set base currency
        params.update(base=self.base_currency)

        response = self.get_response(**params)

        try:
            return self.parse_json(response)['rates']
        except KeyError:
            # API response did not contain any rate
            pass

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
