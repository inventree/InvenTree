---
title: Currency Exchange Mixin
---

## CurrencyExchangeMixin

The `CurrencyExchangeMixin` class enabled plugins to provide custom backends for updating currency exchange rate information.

Any implementing classes must provide the `update_exchange_rates` method. A simple example is shown below (with fake data).

```python

from plugin import InvenTreePlugin
from plugin.mixins import CurrencyExchangeMixin

class MyFirstCurrencyExchangePlugin(CurrencyExchangeMixin, InvenTreePlugin):
    """Sample currency exchange plugin"""

    ...

    def update_exchange_rates(self, base_currency: str, symbols: list[str]) -> dict:
        """Update currency exchange rates.

        This method *must* be implemented by the plugin class.

        Arguments:
            base_currency: The base currency to use for exchange rates
            symbols: A list of currency symbols to retrieve exchange rates for

        Returns:
            A dictionary of exchange rates, or None if the update failed

        Raises:
            Can raise any exception if the update fails
        """

        rates = {
            'base_currency': 1.00
        }

        for sym in symbols:
            rates[sym] = random.randrange(5, 15) * 0.1

        return rates
```
