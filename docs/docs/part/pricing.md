---
title: Pricing
---

## Pricing

Pricing is an inherently complex topic, often subject to the particular requirements of the user. InvenTree attempts to provide a comprehensive pricing architecture which is useful without being proscriptive.

!!! warning "Raw Data Only"
    InvenTree stores raw pricing data, as provided by the user. Any calculations or decisions based on this data must take into consideration the context in which the data are entered.

### Terminology

Throughout this documentation (and within InvenTree) the concepts of *cost* and *price* are separated as follows:

| Term | Description |
| --- | --- |
| Price | The theoretical amount of money required to pay for something. |
| Cost | The actual amount of money paid. |

### Pricing Sources

Pricing information can be determined from multiple sources:

| Pricing Source | Description | Linked to |
| --- | --- | ---|
| Internal Price | How much a part costs to make | [Part](../part/part.md) |
| Supplier Price | The price to theoretically purchase a part from a given supplier (with price-breaks) | [Supplier](../order/company.md#suppliers) |
| Purchase Cost | Historical cost information for parts purchased | [Purchase Order](../order/purchase_order.md) |
| BOM Price | Total price for an assembly (total price of all component items) | [Part](../part/part.md) |

#### Override Pricing

In addition to caching pricing data as documented in the above table, manual pricing overrides can be specified for a particular part. Both the *minimum price* and *maximum price* can be specified manually, independent of the calculated values. If an manual price is specified for a part, it overrides any calculated value.

### Sale Pricing

Additionally, the following information is stored for each part, in relation to sale pricing:

| Pricing Source | Description | Linked to |
| --- | --- | --- |
| Sale Price | How much a salable item is sold for (with price-breaks) | [Part](../part/part.md) |
| Sale Cost | How much an item was sold for | [Sales Order](../order/sales_order.md) |

### Currency Support

InvenTree supports pricing data in multiple currencies, allowing integration with suppliers and customers using different currency systems.

Supported currencies must be configured as part of [the InvenTree setup process](../start/config.md#supported-currencies).

!!! info "Currency Support"
    InvenTree provides multi-currency pricing support via the [django-money](https://django-money.readthedocs.io/en/latest/) library.

#### Default Currency

Many of the pricing operations are performed in reference to a *Default Currency* (which can be selected for the particular InvenTree installation).

#### Conversion Rates

To facilitate conversion between different currencies, exchange rate data is provided via the [exchangerate.host](https://exchangerate.host/#/) API. Currency exchange rates are updated once per day.

!!! tip "Custom Exchange Rates"
    Custom exchange rates or databases can be used if desired.

## Pricing Tab

The pricing tab for a given Part provides all available pricing information for that part. It shows all price ranges and provides tools to calculate them.

The pricing tab is divided into different sections, based on the available pricing data.

!!! info "Pricing Data"
    As not all parts have the same pricing data available, the pricing tab display may be different from one part to the next

### Pricing Overview

At the top of the pricing tab, an *Overview* section shows a synopsis of the available pricing data:

{% with id="pricing_overview", url="part/pricing_overview.png", description="Pricing Overview" %}
{% include 'img.html' %}
{% endwith %}

This overview tab provides information on the *range* of pricing data available within each category. If pricing data is not available for a given category, it is marked as *No data*.

Each price range is calculated in the [Default Currency](#default-currency), independent of the currency in which the original pricing information is stored. This is necessary for operations such as data sorting, price comparison, etc. Note that while the *overview* information is calculated in a single currency, the original pricing information is still available in the original currency.

Price range data is [cached in the database](#price-data-caching) when underlying pricing information changes.

!!! tip "Refresh Pricing"
    While pricing data is [automatically updated](#data-updates), the user can also manually refresh the pricing calculations manually, by pressing the "Refresh" button in the overview section.

#### Overall Pricing

The *overall pricing* range is calculated based on the minimum and maximum of available pricing data. Note that *overall pricing* is the primary source of pricing data used in other pricing calculations (such as cumulative BOM costing, for example).

### Internal Pricing

A particular Part may have a set of *Internal Price Breaks* which denote quantity pricing set by the user. Internal pricing is set independent of any external pricing or BOM data - it is determined entirely by the user. If a part is purchased from external suppliers, then internal pricing may well be left blank.

If desired, price breaks can be specified based on particular quantities.

{% with id="pricing_internal", url="part/pricing_internal.png", description="Internal Pricing" %}
{% include 'img.html' %}
{% endwith %}

#### Pricing Override

If the **Internal Price Override** setting is enabled, then internal pricing data overrides any other available pricing (if present).

### Purchase History

If the Part is designated as *purchaseable*, then historical purchase cost information is displayed (and used to calculate overall pricing). Purchase history data is collected from *completed* [purchase orders](../order/purchase_order.md).

{% with id="pricing_purchase_history", url="part/pricing_purchase_history.png", description="Purchase History" %}
{% include 'img.html' %}
{% endwith %}

### Supplier Pricing

If supplier pricing information is available, this can be also used to determine price range data.

{% with id="pricing_supplier", url="part/pricing_supplier.png", description="Supplier Pricing" %}
{% include 'img.html' %}
{% endwith %}

### BOM Pricing

If a Part is designated as an *assembly*, then the [Bill of Materials](../build/bom.md) (BOM) can be used to determine the price of the assembly. The price of each component in the BOM is used to calculate the overall price of the assembly.

{% with id="pricing_bom", url="part/pricing_bom.png", description="BOM Pricing" %}
{% include 'img.html' %}
{% endwith %}

#### BOM Pricing Chart

The BOM *Pricing Chart* displays two separate "pie charts", with minimum and maximum price data for each item in the BOM. Note that prices are only shown for BOM items which have available pricing information.

!!! info "Complete Pricing Required"
    If pricing data is not available for all items in the BOM, the assembly pricing will be incomplete

### Variant Pricing

For *template* parts, the price of any *variants* of the template is taken into account:

{% with id="pricing_variants", url="part/pricing_variants.png", description="Variant Pricing" %}
{% include 'img.html' %}
{% endwith %}

### Sale Pricing

If the Part is designated as *Salable* then sale price breaks are made available. These can be configured as desired by the user, to define the desired sale price at various quantities.

{% with id="pricing_sale_price_breaks", url="part/pricing_sale_price_breaks.png", description="Sale Pricing" %}
{% include 'img.html' %}
{% endwith %}

### Sale History

If the Part is designated as *Salable* then historical sale cost information is available. Sale history data is collected from *completed* [sales orders](../order/sales_order.md).

{% with id="pricing_sale_history", url="part/pricing_sale_history.png", description="Sale History" %}
{% include 'img.html' %}
{% endwith %}

### Price Data Caching

Pricing calculations (and conversions) can be expensive to perform. This can make pricing data for complex Bills of Material time consuming to retrieve from the server, if not handled correctly.

For this reason, all information displayed in the [pricing overview](#pricing-overview) section is pre-calculated and *cached* in the database. This ensures that when it needs to be retrieved (e.g. viewing pricing for an entire BOM) it can be accessed immediately.

Pricing data is cached in the [default currency](#default-currency), which ensures that pricing can be compared across multiple parts in a consistent format.

#### Data Updates

The pricing data caching is intended to occur *automatically*, and generally be up-to-date without user interaction. Pricing data is re-calculated and cached by the [background worker](../settings/tasks.md) in the following ways:

- **Automatically** - If the underlying pricing data changes, part pricing is scheduled to be updated
- **Periodically** - A daily task ensures that any outdated or missing pricing is kept updated
- **Manually** - The user can manually recalculate pricing for a given part in the [pricing overview](#pricing-overview) display
