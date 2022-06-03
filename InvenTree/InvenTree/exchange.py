"""Exchangerate backend to use `exchangerate.host` to get rates."""

import ssl
from urllib.error import URLError
from urllib.request import urlopen

from django.db.utils import OperationalError

import certifi
from djmoney.contrib.exchange.backends.base import SimpleExchangeBackend

from common.settings import currency_code_default, currency_codes


class InvenTreeExchange(SimpleExchangeBackend):
    """Backend for automatically updating currency exchange rates.

    Uses the `exchangerate.host` service API
    """

    name = "InvenTreeExchange"

    def __init__(self):
        """Set API url."""
        self.url = "https://api.exchangerate.host/latest"

        super().__init__()

    def get_params(self):
        """Placeholder to set API key. Currently not required by `exchangerate.host`."""
        # No API key is required
        return {
        }

    def get_response(self, **kwargs):
        """Custom code to get response from server.

        Note: Adds a 5-second timeout
        """
        url = self.get_url(**kwargs)

        try:
            context = ssl.create_default_context(cafile=certifi.where())
            response = urlopen(url, timeout=5, context=context)
            return response.read()
        except:
            # Returning None here will raise an error upstream
            return None

    def update_rates(self, base_currency=currency_code_default()):
        """Set the requested currency codes and get rates."""
        symbols = ','.join(currency_codes())

        try:
            super().update_rates(base=base_currency, symbols=symbols)
        # catch connection errors
        except URLError:
            print('Encountered connection error while updating')
        except OperationalError as e:
            if 'SerializationFailure' in e.__cause__.__class__.__name__:
                print('Serialization Failure while updating exchange rates')
                # We are just going to swallow this exception because the
                # exchange rates will be updated later by the scheduled task
            else:
                # Other operational errors probably are still show stoppers
                # so reraise them so that the log contains the stacktrace
                raise
