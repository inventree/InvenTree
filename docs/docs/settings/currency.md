---
title: Currency Support
---

## Currency Support

InvenTree provides support for multiple currencies, allowing pricing information to be stored with base currency rates.

### Configuration

To specify which currencies are supported, refer to the [currency configuration](../start/config.md#supported-currencies) section

### Currency Conversion

Currency conversion is provided via the [django-money](https://github.com/django-money/django-money) library. Pricing data can be converted seamlessly between the available currencies.

### Currency Rate Updates

Currency conversion rates are periodically updated, via an external currency exchange server. Out of the box, InvenTree uses the [frankfurter.app](https://www.frankfurter.app/) service, which is an open source currency API made freely available.

#### Custom Rate Updates

If a different currency exchange backend is needed, or a custom implementation is desired, the currency exchange framework can be extended [via plugins](../extend/plugins/currency.md). Plugins which implement custom currency exchange frameworks can be easily integrated into the InvenTree framework.

### Currency Settings

In the [settings screen](./global.md), under the *Pricing* section, the following currency settings are available:

{% with id="currency-settings", url="settings/currency.png", description="Currency Exchange Settings" %}
{% include 'img.html' %}
{% endwith %}
