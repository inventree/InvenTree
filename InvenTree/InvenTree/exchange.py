"""Exchangerate backend to use `frankfurter.app` to get rates."""

from decimal import Decimal
from urllib.error import URLError

from django.db.utils import OperationalError

import requests
from djmoney.contrib.exchange.backends.base import SimpleExchangeBackend

from common.settings import currency_code_default, currency_codes


class InvenTreeExchange(SimpleExchangeBackend):
    """Backend for automatically updating currency exchange rates.

    Uses the `frankfurter.app` service API
    """

    name = "InvenTreeExchange"

    def __init__(self):
        """Set API url."""
        self.url = "https://api.frankfurter.app/latest"

        super().__init__()

    def get_params(self):
        """Placeholder to set API key. Currently not required by `frankfurter.app`."""
        # No API key is required
        return {
        }

    def get_response(self, **kwargs):
        """Custom code to get response from server.

        Note: Adds a 5-second timeout
        """
        url = self.get_url(**kwargs)

        try:
            response = requests.get(url=url, timeout=5)
            return response.content
        except Exception:
            # Something has gone wrong, but we can just try again next time
            # Raise a TypeError so the outer function can handle this
            raise TypeError

    def get_rates(self, **params):
        """Intersect the requested currency codes with the available codes."""
        rates = super().get_rates(**params)

        # Add the base currency to the rates
        rates[params["base_currency"]] = Decimal("1.0")

        return rates

    def update_rates(self, base_currency=None):
        """Set the requested currency codes and get rates."""
        # Set default - see B008
        if base_currency is None:
            base_currency = currency_code_default()

        symbols = ','.join(currency_codes())

        try:
            super().update_rates(base=base_currency, symbols=symbols)
        # catch connection errors
        except URLError:
            print('Encountered connection error while updating')
        except TypeError:
            print('Exchange returned invalid response')
        except OperationalError as e:
            if 'SerializationFailure' in e.__cause__.__class__.__name__:
                print('Serialization Failure while updating exchange rates')
                # We are just going to swallow this exception because the
                # exchange rates will be updated later by the scheduled task
            else:
                # Other operational errors probably are still show stoppers
                # so reraise them so that the log contains the stacktrace
                raise
