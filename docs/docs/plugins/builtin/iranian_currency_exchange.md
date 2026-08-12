---
title: Iranian Currency Exchange
---

## Iranian Currency Exchange

The **Iranian Currency Exchange** plugin provides a USD to IRR exchange rate.
It uses a manually configured rate by default and can optionally fetch the
free-market USD rate from [TGJU](https://www.tgju.org/currency).

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

Leave **Enable TGJU USD rate consumer** disabled and enter **Manual USD to IRR
rate** as the number of Iranian rials per one US dollar. The plugin then makes
no TGJU requests, so rate updates work without an Internet connection. After
changing the manual rate, open Currency Management and select **Refresh
exchange rates** to apply it immediately.

### TGJU consumer

Enable **Enable TGJU USD rate consumer** to fetch the rate from TGJU instead of
using the manual value. The plugin reads TGJU's HTML using XPath, with these
sources in order:

1. [`https://www.tgju.org/currency`](https://www.tgju.org/currency), first using
   the semantic market-row XPath:

   ```xpath
   string((//tr[@data-market-row='price_dollar_rl']/@data-price)[1])
   ```

   It then tries the XPath equivalent of TGJU's displayed-price selector:

   ```xpath
   string((//*[@id='l-price_dollar_rl']//*[contains(concat(' ', normalize-space(@class), ' '), ' info-price ')])[1])
   ```

2. [`https://www.tgju.org/profile/price_dollar_rl`](https://www.tgju.org/profile/price_dollar_rl),
   using the current-rate field as a page-level fallback:

   ```xpath
   string((//*[@data-target='profile-tour-current_rate']//*[@data-col='info.last_trade.PDrCotVal'])[1])
   ```

The extracted value is Iranian rials per US dollar. It is stored as returned;
the plugin does not multiply the value by ten.

InvenTree's Django-Q2 scheduler refreshes the TGJU-provided rate every three
hours. No Celery worker is required.

The scheduled task does nothing while the TGJU consumer is disabled or this
plugin is not the selected currency update plugin. A failed request, invalid
rate, or TGJU DOM change which prevents the XPath selectors from matching
returns no update. In that case, the last valid exchange rates remain stored
and their last-update timestamp is not advanced. The manual value is an
operator-selected offline alternative; it is not applied automatically after
a TGJU fetch failure.

### Scope

This first implementation accepts only a `USD` base and the `USD,IRR` supported
currency set. Individual InvenTree money fields can store values in either
currency. It does not create paired USD and IRR price columns or save a
historical exchange-rate snapshot on each price record.
