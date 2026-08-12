---
title: Iranian Currency Exchange
---

## Iranian Currency Exchange

The **Iranian Currency Exchange** plugin provides a USD to IRR exchange rate.
It uses a manually configured rate by default and can optionally consume the
documented [Navasan latest-rates
API](https://www.navasan.tech/webserviceguide/#latest-rates).

The plugin uses InvenTree's existing Django-Q2 scheduler. No additional Celery
worker or settings package is required.

### Activation

This plugin is optional. Enable it in the plugin management interface, then
configure the following system settings:

- **Default Currency**: `USD`
- **Supported Currencies**: `USD,IRR`
- **Currency Update Plugin**: `Iranian Currency Exchange`
- **Currency Update Interval**: `0`
- **Enable schedule integration**: enabled

Setting **Currency Update Interval** to zero disables InvenTree's overlapping
daily currency task. The plugin schedule described below still runs because it
forces its selected update explicitly.

The USD base is required because the exchange-rate database stores six decimal
places. Storing the small reciprocal USD-per-IRR value would introduce a large
rounding error.

### Manual rate

Leave **Enable USD exchange rate API** disabled and enter **Manual USD to IRR
rate** as the number of Iranian rials per one US dollar. Rate updates then work
without an Internet connection. After changing the manual rate, open Currency
Management and select **Refresh exchange rates** to apply it immediately.

### API consumer

Set **Enable USD exchange rate API** to enabled, provide a Navasan API key, and
explicitly select the unit returned for the account:

- `IRR`: the API value is already in Iranian rials.
- `IRT`: the API value is in toman and is multiplied by ten exactly once.

The unit selection is intentionally required. Treating toman as rial would
produce a tenfold pricing error.

InvenTree's Django-Q2 scheduler refreshes the API-provided rate every eight
hours. This makes at most 93 scheduled requests in a 31-day month, below
Navasan's [current free allowance of 120 monthly
requests](https://www.navasan.tech/pricing/). Navasan currently limits free
keys to three months, so check the provider's current terms before deployment.

The scheduled task does nothing while the API consumer is disabled or this
plugin is not the selected currency update plugin. A failed request, invalid
response, missing key, or invalid rate returns no update, so the last valid
exchange rates remain stored and their last-update timestamp is not advanced.

### Scope

This first implementation accepts only a `USD` base and the `USD,IRR` supported
currency set. Individual InvenTree money fields can store values in either
currency. It does not create paired USD and IRR price columns or save a
historical exchange-rate snapshot on each price record.
