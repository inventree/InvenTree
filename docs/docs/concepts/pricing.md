---
title: Pricing Support
---

## Pricing

Pricing is an inherently complex topic, often subject to the particular requirements of the user. InvenTree attempts to provide a comprehensive pricing architecture which is useful without being proscriptive.

InvenTree provides support for multiple currencies, allowing pricing information to be stored with base currency rates.

!!! warning "Raw Data Only"
    InvenTree stores raw pricing data, as provided by the user. Any calculations or decisions based on this data must take into consideration the context in which the data are entered.

InvenTree uses the [django-money](https://github.com/django-money/django-money) library, which in turn uses the [py-moneyed library](https://py-moneyed.readthedocs.io/en/latest/index.html). `py-moneyed` supports any currency which is defined in the [ISO 3166 standard](https://en.wikipedia.org/wiki/List_of_ISO_3166_country_codes) standard.


### Terminology

Throughout this documentation (and within InvenTree) the concepts of *cost* and *price* are separated as follows:

| Term | Description |
| --- | --- |
| Price | The theoretical amount of money required to pay for something. |
| Cost | The actual amount of money paid. |


## Currency Support

InvenTree supports pricing data in multiple currencies, allowing integration with suppliers and customers using different currency systems.

### Default Currency

Many of the pricing operations are performed in reference to a *Default Currency* (which can be selected for the particular InvenTree installation).

The default currency is user configurable in the InvenTree settings.

!!! warning "Setting Default Currency"
    Changing the default currency once the system in use may have unintended consequences. It is recommended to set the default currency during the initial setup of the InvenTree instance.

## Conversion Rates

To facilitate conversion between different currencies, exchange rate information is stored in the InvenTree database.

### Currency Codes

The list of support currency codes is user configurable in the InvenTree settings. It is recommended to select only the currencies which are relevant to the user.

While InvenTree can support any of the currencies defined in the ISO 3166 standard, the list of supported currencies can be limited to only those which are relevant to the user. The supported currencies are used to populate the currency selection dropdowns throughout the InvenTree interface.


### Exchange Rate Data

The exchange rate data is provided by a [currency plugin](../extend/plugins/currency.md) which fetches exchange rate data from an external source.

InvenTree includes a default currency plugin which fetches exchange rate data from the [frankfurter](https://frankfurter.dev/) API, which is an open source currency API made freely available.

However, the user can configure a custom currency plugin to fetch exchange rate data from a different source. If a different currency exchange backend is needed, or a custom implementation is desired, the currency exchange framework can be extended [via plugins](../extend/plugins/currency.md). Plugins which implement custom currency exchange frameworks can be easily integrated into the InvenTree framework.

### Exchange Rate Updates

Currency exchange rates are updated periodically, using the configured currency plugin. The update frequency can be configured in the InvenTree settings.

## Pricing Settings

Refer to the [global settings](../settings/global.md#pricing-and-currency) documentation for more information on available currency settings.
