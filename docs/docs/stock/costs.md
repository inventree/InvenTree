---
title: Stock Item Costs
---

## Stock Item Costs

InvenTree records what each individual [stock item](./index.md) actually *cost*. Where [part pricing](../part/pricing.md) describes what a part *should* cost (from supplier price breaks, BOM data, etc.), stock item costs track the real costs associated with a particular batch of stock - such as the price paid to the supplier, freight and import duty, or fees.

!!! info "Cost vs. Price"
    Refer to the [pricing terminology](../concepts/pricing.md#terminology) documentation for the distinction between *cost* and *price* within InvenTree.

A stock item can have any number of *cost entries*, each of which records a single contribution to the cost of the stock item. The cost entries are added together to give the [unit cost](#unit-cost) of the stock item.

!!! info "Per Unit Costs"
    All stock item costs are recorded *per unit* of the stock item. For example, a freight charge of $50 for a delivery of 100 units is recorded as a cost of $0.50 per unit. This ensures that the costs remain correct when a stock item is [split](./adjust.md) into multiple items.

## Cost Entries

Each cost entry has the following attributes:

| Attribute | Description |
| --- | --- |
| Cost Type | The category of the cost (see [below](#cost-types)) |
| Currency | The currency in which the cost is specified |
| Unit Cost | The cost per unit of the stock item. An [estimated](#estimated-costs) cost is specified as a range (minimum and maximum unit cost) |
| Source | Who (or what) created the cost entry (see [below](#cost-sources)) |
| Notes | Optional notes - for example, a reference to an invoice, or the original (lump sum) amount |
| User | The user who last created or updated the cost entry |
| Converted Unit Cost | The unit cost, converted to the [default currency](../concepts/pricing.md#default-currency) (see [currency conversion](#currency-conversion)) |

Negative costs are allowed, to record rebates, credits or other corrections.

### Cost Types

The *cost type* describes *what* a cost is for:

{{ statuscodes("CostType") }}

### Estimated Costs

If the exact cost is not known, a cost can be recorded as an *estimate* by specifying a range of costs (a minimum and a maximum unit cost). For example, freight charges may be estimated when stock is received, and corrected once the freight invoice arrives.

A cost range is carried through to the [unit cost](#unit-cost) of the stock item, which is then also displayed as a range.

### Cost Sources

The *source* of a cost entry identifies who (or what) created it:

| Source | Description |
| --- | --- |
| `manual` | Entered manually by a user (via the user interface or the API). All cost entries created via the API are recorded as `manual` entries |
| `purchase_order` | Recorded when the item was [received against a purchase order](#receiving-purchase-orders) |
| `merge` | Recorded when stock items were [merged](#merging-stock-items) |
| `disassembly` | Recorded when the item was created by [disassembling](#disassembly) another stock item |
| `build` | Reserved for costs recorded by build orders |
| `legacy` | Migrated from the *purchase price* of the stock item, from an earlier version of InvenTree (see [legacy purchase prices](#legacy-purchase-prices)) |
| `plugin:<slug>` | Created by the [plugin](#plugin-support) with the specified slug |

## Unit Cost

The *unit cost* of a stock item is the sum of all its cost entries, calculated in the [default currency](../concepts/pricing.md#default-currency). The unit cost is recalculated automatically whenever a cost entry is added, edited or removed.

The unit cost is displayed on the *Stock Details* panel of the stock item, along with the *Total Cost* of the stock item (the unit cost multiplied by the stock quantity):

{{ image("stock/stock_unit_cost.png", "Stock item unit cost") }}

If any of the cost entries could not be included in the unit cost (for example, if no [exchange rate](#currency-conversion) is available for its currency), the unit cost is marked as *Incomplete*.

### Stock Tables

Stock tables display the *Unit Cost* of each stock item (this column is hidden by default, and can be enabled via the column selector), and the *Stock Value* of each stock item:

{{ image("stock/stock_table_unit_cost.png", "Stock table unit cost") }}

The *Stock Value* is calculated from the unit cost of the stock item. If the stock item does not have any recorded costs, the stock value is instead estimated from the [pricing data](../part/pricing.md) of the part.

Stock tables can also be filtered by the *Has Unit Cost* filter, and sorted by *Unit Cost*.

## Item Costs Panel

The cost entries for a stock item are displayed in the *Item Costs* panel on the stock item detail page:

{{ image("stock/stock_costs_panel.png", "Stock item costs panel") }}

From this panel, cost entries can be added, edited and removed (subject to the [required permissions](#permissions)).

### Adding a Cost

To add a cost to a stock item, click on the {{ icon("plus", color="green") }} button in the *Item Costs* panel. Select the *Cost Type* and *Currency*, and enter the *Unit Cost*:

{{ image("stock/stock_cost_form.png", "Add stock item cost") }}

To record an [estimated cost](#estimated-costs), enable the *Estimate* option, and enter the minimum and maximum unit cost:

{{ image("stock/stock_cost_form_estimate.png", "Add estimated stock item cost") }}

When editing an existing cost entry, the *Estimate* option is automatically enabled if the cost is specified as a range.

## How Costs are Recorded

In addition to costs entered manually, InvenTree records stock item costs automatically as stock is received, created and modified.

### Receiving Purchase Orders

When items are received against a [purchase order](../purchasing/purchase_order.md#item-cost) line item which has a price, a *Purchase* cost is recorded against each of the created stock items:

- The line item price is per supplier pack, so it is divided by the [pack quantity](../purchasing/supplier.md#supplier-part-pack-size) of the supplier part, to give a cost per unit of the stock item
- The cost is recorded in the currency of the purchase order line item

### Duplicating Stock Items

When a stock item is duplicated, the cost entries of the original stock item are copied to the new stock item(s), unless the *Copy Costs* option is disabled:

{{ image("stock/stock_duplicate_copy_costs.png", "Copy costs when duplicating a stock item") }}

The *Copy Costs* option is only displayed for users who can view stock item costs - for any other user, costs are always copied.

### Splitting Stock

As costs are recorded per unit, any operation which creates a new stock item from part of an existing stock item copies the cost entries of the original stock item to the new stock item. This includes:

- [Splitting or moving](./adjust.md) part of a stock item
- [Serializing](../part/trackable.md) a stock item
- Consuming part of a stock item in a [build order](../manufacturing/build.md)
- Shipping part of a stock item against a [sales order](../sales/sales_order.md)
- Transferring or returning part of a stock item (via a [transfer order](./transfer_order.md) or [return order](../sales/return_order.md))

### Merging Stock Items

When stock items are merged, the costs of the merged stock items are combined into a single cost entry per [cost type](#cost-types), calculated as the average unit cost weighted by the quantity of each stock item:

- Stock items which do not have *any* recorded costs have an unknown cost, and are excluded from the calculation
- If all costs of a particular type are in the same currency, the average is calculated in that currency. Otherwise, the average is calculated in the [default currency](../concepts/pricing.md#default-currency)
- The original cost entries are recorded in the *source data* of the new cost entries

### Disassembly

When a stock item is [disassembled](./disassemble.md), *Material* cost entries are recorded against the generated component stock items - either the unit cost entered for each component, or a share of the remaining cost of the disassembled item (allocated using part pricing data). If pricing data is not available for every component without an entered unit cost, no cost is recorded for those components. Refer to the [disassembly documentation](./disassemble.md#component-costs) for more information.

### Legacy Purchase Prices

Earlier versions of InvenTree recorded a single *purchase price* against each stock item. When upgrading, any existing purchase price is converted into a *Purchase* cost entry with the `legacy` source.

## Currency Conversion

Each cost entry is converted to the [default currency](../concepts/pricing.md#default-currency) when it is recorded, using the [exchange rates](../concepts/pricing.md#exchange-rate-data) available at that time. Both the original and the converted values are stored against the cost entry.

The [unit cost](#unit-cost) is calculated from the stored converted values, so that the cost of a stock item does not change with subsequent changes in exchange rates.

!!! warning "Missing Exchange Rates"
    If no exchange rate is available for the currency of a cost entry, the cost entry is excluded from the unit cost, and the unit cost is marked as *Incomplete*. Such cost entries are displayed as *Not converted* in the [Item Costs](#item-costs-panel) panel.

!!! warning "Changing the Default Currency"
    If the default currency is changed, existing cost entries remain converted to the previous default currency, and are excluded from the unit cost (which is marked as *Incomplete*) until they are converted to the new default currency.

### Re-Converting Costs

Whenever the [exchange rates](../concepts/pricing.md#exchange-rate-data) are updated (including when the default currency is changed), any cost entries which have not been converted to the current default currency are converted again, using the new exchange rates. The unit cost of each affected stock item is then recalculated.

This means that a cost entry which could not be converted when it was recorded (for example, because no exchange rate was available for its currency) is included in the unit cost of the stock item once an exchange rate becomes available.

A cost entry is also converted again if it is edited, or if the stock item is [merged](#merging-stock-items) with other stock items.

!!! info "Existing Conversions"
    Cost entries which have already been converted to the default currency are *not* converted again when the exchange rates change - the cost of a stock item reflects the exchange rate at the time the cost was recorded.

## How Stock Costs are Used

### Part Pricing

If the {{ globalsetting("PRICING_USE_STOCK_PRICING", short=True) }} setting is enabled, the *Purchase* costs of the stock items for a part are included in the [purchase history](../part/pricing.md#purchase-history) of the part. Refer to the [part pricing](../part/pricing.md#stock-item-costs) documentation for more information.

### Stocktake

The unit cost of each stock item is used to calculate the value of stock on hand, when performing a [stocktake](../part/stocktake.md).

## Permissions

Stock item costs are covered by the *Pricing* [user role](../settings/permissions.md#roles), in addition to the *Stock Items* role:

| Action | Required Permissions |
| --- | --- |
| View costs | *Pricing* (view) and *Stock Items* (view) |
| Add a cost entry | *Pricing* (add) and *Stock Items* (change) |
| Edit a cost entry | *Pricing* (change) and *Stock Items* (change) |
| Delete a cost entry | *Pricing* (delete) and *Stock Items* (change) |

If a user does not have *view* permission for the *Pricing* role, the *Item Costs* panel, the unit cost of the stock item, and the *Unit Cost* column in stock tables are hidden. The *Has Unit Cost* filter and *Unit Cost* sorting options are also ignored for such users.

!!! info "Automatically Recorded Costs"
    Costs which are recorded automatically, as part of another operation, do not require the *Pricing* role. For example, a user who can receive items against a purchase order records the cost of the received items, and a user who can disassemble a stock item can enter the unit cost of the generated components.

### History

Changes to stock item costs are recorded in the [history](../concepts/audit.md) of the stock item. These entries are only visible to users with *view* permission for the *Pricing* role.

## Report Templates

The cost data of a stock item can be accessed in [report and label templates](../report/index.md):

| Attribute | Description |
| --- | --- |
| `item.cost` | The unit cost of the stock item (does not exist if the stock item has no costs) |
| `item.cost.min_cost` | Minimum unit cost (in the default currency) |
| `item.cost.max_cost` | Maximum unit cost (in the default currency) |
| `item.cost.currency` | The currency of the unit cost |
| `item.cost.incomplete` | True if any cost entry could not be included |
| `item.cost_entries.all` | The individual cost entries of the stock item |

For example:

```html
{% raw %}
{% load report %}

{% if item.cost %}
Unit cost: {% render_currency item.cost.min_cost_money %}
{% endif %}

{% for entry in item.cost_entries.all %}
{{ entry.get_cost_type_display }}: {% render_currency entry.min_cost_money %}
{% endfor %}
{% endraw %}
```

!!! warning "Purchase Price Removed"
    The `purchase_price` attribute of the stock item has been removed. Any template (or [plugin](../plugins/index.md)) which still references `item.purchase_price` (or `item.purchase_price_currency`) raises an error, and must be updated to use the cost data described above.

## API Access

Stock item costs are available via the following API endpoints:

| Endpoint | Description |
| --- | --- |
| `/api/pricing/stock-cost-entry/` | List, create, edit and delete cost entries |
| `/api/pricing/stock-cost/` | The (read-only) unit cost of each stock item |

Additionally, the stock item API (`/api/stock/`) supports:

- The optional `pricing_detail` field, which includes the unit cost of each stock item
- The `has_unit_cost` filter, and the `unit_cost` ordering option
- The `copy_costs` option, when [duplicating](#duplicating-stock-items) a stock item

!!! info "Read Only Fields"
    The `source` and `source_data` fields of a cost entry are read-only via the API. Cost entries created via the API are always recorded with the `manual` source, and the source of an existing cost entry cannot be changed.

Refer to the [API schema](../api/schema.md) documentation for more information.

## Limitations

The following are not currently supported:

- **Setting a cost when creating stock:** A cost cannot be entered when creating a new stock item (via the user interface or the API). Add the cost via the [Item Costs](#item-costs-panel) panel (or the `/api/pricing/stock-cost-entry/` API endpoint) once the stock item has been created
- **Stock item import and export:** Costs are not included when [importing](../concepts/data_import.md) or [exporting](../concepts/data_export.md) stock item data. The cost entries of a single stock item can be exported from the [Item Costs](#item-costs-panel) panel

!!! warning "Importing Older Database Backups"
    Database backups created by an earlier version of InvenTree contain the (removed) `purchase_price` field of each stock item, and cannot be imported directly into this version. Instead, import the backup into the *same* version of InvenTree which created it, and then [update](../start/migrate.md#migrating-data-to-newer-version) to this version - the purchase prices are then migrated to [legacy](#legacy-purchase-prices) cost entries.

## Plugin Support

[Plugins](../plugins/index.md) can record stock item costs - for example, to calculate landed costs from an external freight system. Cost entries created by a plugin should use the `plugin:<slug>` [source](#cost-sources), so that they can be identified (and replaced) by the plugin:

```python
from djmoney.money import Money

from pricing.models import CostSource, StockItemCostEntry
from pricing.status_codes import CostType

# Replace any previous cost entries created by this plugin, for this stock item
StockItemCostEntry.objects.replace_costs(
    stock_item,
    CostSource.plugin(self.slug),
    [
        {
            'cost_type': CostType.LANDED,
            'min_cost': Money(1.50, 'USD'),
            'max_cost': Money(2.25, 'USD'),
            'notes': 'Estimated freight',
        }
    ],
)
```

The unit cost of the stock item is recalculated automatically.
