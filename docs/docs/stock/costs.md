---
title: Stock Item Costs
---

## Stock Item Costs

!!! info "Pricing Support"
    Refer to the [Pricing Support](../concepts/pricing.md) documentation for a general introduction to cost and pricing concepts in InvenTree.

Each [stock item](./index.md) can have one or more *cost entries* recorded against it, representing the various contributions to its overall unit cost. These entries are automatically combined into a single cached *cost summary*, which is displayed throughout the InvenTree interface (for example in stock tables, and on the stock item detail page).

### Cost Entries

A *cost entry* records a single contribution to a stock item's unit cost, tagged with a [cost type](#cost-types), along with a *minimum* and *maximum* cost value (and their associated currency).

!!! info "Unit Cost, not Total Cost"
    Cost entries always represent a **per-unit** cost, not the total value of the stock item. To determine the total value of a stock item, multiply its unit cost by its quantity - see [Stock Value](#stock-value) below.

Only one cost entry may exist per *(stock item, cost type)* pair - adding a new entry of the same type as an existing one updates that entry in place, rather than creating a duplicate.

#### Cost Types

| Cost Type | Description |
| --- | --- |
| Purchase | Cost taken directly from a purchase (e.g. a received purchase order line item) |
| Landed | Purchase cost plus additional landed costs (freight, duty, handling, etc) |
| Material | Cost of BOM components consumed by a build order, from allocated stock which itself has a recorded cost |
| Material (Estimated) | Cost of BOM components consumed by a build order, from allocated stock with no recorded cost - estimated from the component part's price range instead |
| Manufacturing | Reserved for manufacturing *process* cost (e.g. labor, overhead) added during a build - distinct from Material, which is the cost of the components consumed |
| Manual | Cost manually entered (or overridden) by a user |
| System | Cost calculated automatically by the pricing system (e.g. a pricing plugin) |

!!! warning "Manufacturing Process Cost"
    *Manufacturing* process cost (labor, overhead) is not yet calculated anywhere - the cost type exists, but nothing populates it yet. Only *Material* cost (see [How Cost Entries are Created](#how-cost-entries-are-created) below) is currently recorded automatically from build orders - see [Known Limitations](#known-limitations) below.

### Cost Summary

The cost summary for a stock item is automatically (re)calculated as the sum of all of its cost entries, and cached for fast retrieval. It is not itself directly editable - it always reflects the current state of the underlying cost entries, and is recalculated automatically whenever an entry is added, updated, or removed.

If a stock item has no cost entries recorded against it, no cost summary is available for that item (rather than a summary reporting a zero cost).

!!! tip "Currency Conversion"
    While individual cost entries retain their own original currency, the cost summary is always calculated in the [default currency](../concepts/pricing.md#default-currency). If a currency conversion rate is not available for one of the entries, that entry is excluded from the summary rather than being included unconverted - the summary will never mix currencies.

### Viewing and Editing Cost Entries

Cost entries for a stock item can be viewed - and added, edited, or deleted - from the *Stock Item Cost* tab on the stock item detail page.

| Column | Description |
| --- | --- |
| Cost Type | The [cost type](#cost-types) of the entry |
| Minimum Cost | The minimum unit cost |
| Maximum Cost | The maximum unit cost |
| Date | The date the entry was last updated |
| Notes | Optional notes describing the entry |

!!! info "Permissions"
    Viewing, adding, editing and deleting cost entries requires the appropriate [Pricing permission role](../settings/permissions.md#roles), assigned via user groups.

### Displayed Cost Information

Cost summary information is displayed in a number of places throughout the InvenTree interface:

- The stock item detail page displays the *Unit Price* (unit cost) and *Stock Value* for the item, if cost data is available
- Stock tables can optionally display *Unit Price* and *Stock Value* columns - these are hidden by default, and only visible to users with the *Pricing* view permission

#### Stock Value

The *Stock Value* of a stock item is calculated as:

```
Stock Value = Unit Cost * Quantity
```

This value is not itself stored - it is calculated on the fly, from the cached cost summary and the item's current quantity.

### How Cost Entries are Created

Cost entries can be created (or updated) in a number of ways:

- **Manually**: a user with the appropriate permission can add, edit, or delete cost entries directly, via the *Stock Item Cost* tab described [above](#viewing-and-editing-cost-entries)
- **Purchase order receipt**: [receiving a line item](../purchasing/purchase_order.md#receive-line-items) against a purchase order automatically records a *Purchase* cost entry against each created stock item, based on the line item's unit price - see [Item Value Currency](../purchasing/purchase_order.md#item-value-currency)
- **Stock disassembly**: [disassembling](./disassemble.md#automatic-cost-allocation) a stock item automatically apportions its unit cost across the generated component stock items, recorded as a *Purchase* cost entry against each
- **Stock merge**: [merging](./adjust.md#merge-stock) two or more stock items automatically calculates a new *Purchase* cost entry for the merged item, as a quantity-weighted average of the cost of the merged items
- **Direct stock item creation / update**: the [Stock API](../api/index.md) accepts a `purchase_price` (and `purchase_price_currency`) value when creating or updating a stock item, which is recorded as a *Purchase* cost entry - this is a write-only convenience field, rather than a stored property of the stock item itself
- **Build order completion**: completing a [build order](../manufacturing/build.md) automatically records *Material* (or *Material (Estimated)*, if the allocated stock has no recorded cost) cost entries against each completed build output, based on the cost of the BOM components allocated to it - both stock directly allocated to a specific output, and stock allocated to the build order as a whole (apportioned evenly, per unit, across every completed output)

### Known Limitations

- **No cost history**: only the most recent value for each *(stock item, cost type)* pair is retained - there is no historical ledger of cost changes over time for a given stock item
- **Manufacturing process cost**: only the *cost of components* consumed by a build order is recorded automatically (as *Material* / *Material (Estimated)*) - manufacturing *process* cost (labor, overhead) is not yet calculated anywhere, even though the *Manufacturing* cost type exists for this purpose. This is planned for a future release.
- **Consumable and virtual BOM lines**: build order material cost does not yet account for consumable or virtual BOM lines - see the "Manufacturing Costs" section of `dev/todo/pricing.md` for the follow-up plan
- **CSV import**: bulk cost data cannot currently be imported via the stock item CSV import process

### Related Documentation

- [Pricing Support](../concepts/pricing.md) - general pricing and currency concepts
- [Part Pricing](../part/pricing.md) - part-level pricing, which incorporates stock item cost data into purchase history calculations
