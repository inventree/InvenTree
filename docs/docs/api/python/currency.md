---
title: Python Currency Support
---

## Currency Support

InvenTree provides native support for multiple currencies, which can mean that data require conversion between these currencies, at defined exchange rates.

The InvenTree server maintains a set of exchange rates, which are updated periodically. These exchange rates are available via the [InvenTree API](../api.md), and can be used by the Python bindings.

### CurrencyManager Class

The Python bindings provide the `CurrencyManager` class, which takes care of retrieving currency exchange data from the server. This class can be instantiated as shown below:

```python
from inventree.currency import CurrencyManager

# The manager class must be passed a valid InvenTreeAPI instance
manager = CurrencyManager(api)

# Access the 'base currency' data
base_currency = manager.getBaseCurrency()

# Access the 'exchange rate' data
rates = manager.getExchangeRates()
```

### Currency Conversion

Currency conversion is performed by passing the value of currency, as well as the *source* and *target* currency codes to the currency manager.

!!! warning "Missing Currency Data"
    The currency conversion only works if the manager class has valid information on both the *source* and *target* currency exchange rates!

```python
from inventree.currency import CurrencyManager

manager = CurrencyManager(api)

# Convert from AUD to CAD
cad = manager.convertCurrency(12.54, 'AUD', 'CAD')

# Convert from NZD to USD
usd = manager.convertCurrency(99.99, 'NZD', 'USD')
```

### Exchange Rate Update

To request a manual update of currency data (from the server), run the following command:

```python
from inventree.currency import CurrencyManager

manager = CurrencyManager(api)
manager.refreshExchangeRates()
```
