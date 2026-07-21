---
title: Pricing Support
---

## Pricing

Pricing is an inherently complex topic, often subject to the particular requirements of the user. InvenTree attempts to provide a comprehensive pricing architecture which is useful without being prescriptive.

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

## Line Items

Orders (Purchase Orders, Sales Orders, and Return Orders) are made up of *line items*, each linking a *Quantity* to a *Unit Price*. A line item's *Line Total* is calculated as follows:

```
Line Total = Quantity * Unit Price
```

An order's overall *Total Price* is calculated by summing the *Line Total* of every line item and [extra line item](#extra-line-items) associated with the order.

### Extra Line Items

*Extra Line Items* provide a way to add itemized costs to an order which are not tied to a specific part or stock item - for example freight charges, service fees, or other miscellaneous costs. Extra line items support the same *Quantity* and *Unit Price* fields as regular line items, and are included in the order's *Total Price* calculation.

### Line Item Discount

Line items - and their associated [extra line items](#extra-line-items) - support an optional *Discount* field, expressed as a percentage between 0% and 100%. This is available on:

- [Purchase Order](../purchasing/purchase_order.md#add-line-items) line items and [extra line items](../purchasing/purchase_order.md#extra-line-items)
- [Sales Order](../sales/sales_order.md#add-line-items) line items and [extra line items](../sales/sales_order.md#extra-line-items)
- [Return Order](../sales/return_order.md#line-items) line items and [extra line items](../sales/return_order.md#extra-line-items)

If specified, the discount is applied to the *Line Total*, using the following formula:

```
Line Total = Quantity * Unit Price * (1 - Discount / 100)
```

!!! info "Optional"
    The discount percentage is optional, and defaults to 0% (no discount) if not specified.

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

The exchange rate data is provided by a [currency plugin](../plugins/mixins/currency.md) which fetches exchange rate data from an external source.

InvenTree includes a default currency plugin which fetches exchange rate data from the [frankfurter](https://frankfurter.dev/) API, which is an open source currency API made freely available.

However, the user can configure a custom currency plugin to fetch exchange rate data from a different source. If a different currency exchange backend is needed, or a custom implementation is desired, the currency exchange framework can be extended [via plugins](../plugins/mixins/currency.md). Plugins which implement custom currency exchange frameworks can be easily integrated into the InvenTree framework.

### Exchange Rate Updates

Currency exchange rates are updated periodically, using the configured currency plugin. The update frequency can be configured in the InvenTree settings.

## Pricing Settings

Refer to the [global settings](../settings/global.md#pricing-and-currency) documentation for more information on available currency settings.

## Rendering Currencies in Reports

Currency values can be rendered in report templates using the [`render_currency`](../report/helpers.md#render_currency) helper function. This function formats a currency amount according to a locale, and supports currency conversion within the template.

See the [report helpers documentation](../report/helpers.md#currency-formatting) for full details and examples.
