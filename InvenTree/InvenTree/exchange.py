from django.conf import settings as inventree_settings

from djmoney.contrib.exchange.backends.base import BaseExchangeBackend
from djmoney.contrib.exchange.models import Rate

from common.models import InvenTreeSetting


def get_exchange_rate_backend():
    """ Return the exchange rate backend set by user """

    custom = InvenTreeSetting.get_setting('CUSTOM_EXCHANGE_RATES', False)

    if custom:
        return InvenTreeManualExchangeBackend()
    else:
        return ExchangeRateHostBackend()


class InvenTreeManualExchangeBackend(BaseExchangeBackend):
    """
    Backend for manually updating currency exchange rates

    See the documentation for django-money: https://github.com/django-money/django-money

    Specifically: https://github.com/django-money/django-money/tree/master/djmoney/contrib/exchange/backends
    """

    name = 'inventree'
    url = None
    custom_rates = True
    base_currency = None
    currencies = []

    def update_default_currency(self):
        """ Update to base currency """

        self.base_currency = InvenTreeSetting.get_setting('INVENTREE_DEFAULT_CURRENCY', 'USD')

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


class ExchangeRateHostBackend(InvenTreeManualExchangeBackend):
    """
    Backend for https://exchangerate.host/
    """

    name = "exchangerate.host"

    def __init__(self):
        self.url = "https://api.exchangerate.host/latest"

        self.custom_rates = False

        super().__init__(url=self.url)

    def get_params(self):
        # No API key is required
        return {}

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
