---
title: Currency Support
---

## Currency Support

InvenTree provides support for multiple currencies, allowing pricing information to be stored with base currency rates.

### Supported Currencies

InvenTree uses the [django-money](https://github.com/django-money/django-money) library, which in turn uses the [py-moneyed library](https://py-moneyed.readthedocs.io/en/latest/index.html). `py-moneyed` supports any currency which is defined in the [ISO 3166 standard](https://en.wikipedia.org/wiki/List_of_ISO_3166_country_codes) standard.

### Currency Conversion

Currency conversion is provided via the `django-money` library. Pricing data can be converted seamlessly between the available currencies.

### Currency Rate Updates

Currency conversion rates are periodically updated, via an external currency exchange server. Out of the box, InvenTree uses the [frankfurter.app](https://www.frankfurter.app/) service, which is an open source currency API made freely available.

#### Custom Rate Updates

If a different currency exchange backend is needed, or a custom implementation is desired, the currency exchange framework can be extended [via plugins](../extend/plugins/currency.md). Plugins which implement custom currency exchange frameworks can be easily integrated into the InvenTree framework.

### Currency Settings

Refer to the [global settings](./global.md#pricing-and-currency) documentation for more information on available currency settings.

#### Supported Currencies

While InvenTree can support any of the currencies defined in the ISO 3166 standard, the list of supported currencies can be limited to only those which are relevant to the user. The supported currencies are used to populate the currency selection dropdowns throughout the InvenTree interface.
