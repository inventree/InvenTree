---
title: Stock Disassembly
---

## Stock Disassembly

A stock item of an [assembly](../part/index.md#assembly) part can be *disassembled* back into its component parts, based on the [Bill of Materials](../manufacturing/bom.md) (BOM) for that part. This is the reverse of building an assembly - instead of consuming components to create an assembled item, the assembled item is broken back down into its constituent components.

This is useful in a number of scenarios, for example:

- An assembly is being reworked or scrapped, and the still-usable components need to be returned to stock
- A supplier ships a "bundled" or "kit" product as a single line item, which needs to be split apart into its individual components before the parts can be used or sold separately (see below)
- Correcting an assembly which was built or received in error

Disassembly is only available for a stock item whose part is marked as an *assembly*, and requires that the part has at least one [BOM line item](../manufacturing/bom.md#bom-line-items) defined.

To disassemble a stock item, navigate to the stock item detail page and select the *Disassemble* option from the actions menu. This requires that the user has the *Stock: Add* permission, and that the stock item is currently [in stock](./status.md).

{{ image("stock/stock_options.png", "Stock Options") }}

### Disassembly Form

The disassembly form is pre-populated with one line per BOM line item defined for the part, based on the quantity of assemblies being disassembled. Any line item marked as [consumable](../manufacturing/bom.md#consumable-bom-line-items) (whether the BOM line itself or its underlying part is marked consumable), or which points to a [virtual](../part/index.md) part, is excluded, as these components are not expected to be tracked as physical stock. This exclusion is enforced by the API - such a BOM line cannot be submitted for disassembly, even if referenced directly.

For each line, the following values may be adjusted:

| Field | Description |
| --- | --- |
| Quantity | The total quantity of the component part to generate. This is automatically scaled as the top-level *Quantity* field is changed, unless the user has manually edited it |
| Location | An optional destination location for the generated stock item. If not specified, the component is placed in the same location as the disassembled item (or the default location specified at the top of the form) |
| Status | An optional [stock status](./status.md) to apply to the generated stock item. If not specified, the component is created with the default *OK* status |
| Unit Cost | An optional unit cost (in the default currency) to record against the generated stock item, as a cost entry. If left blank, a share of the remaining cost of the disassembled item may be allocated automatically - but only in some circumstances (see [Component Costs](#component-costs)) |

A line item can be removed from the form entirely if that particular component is not required to be split out - for example, if it is being scrapped rather than returned to stock. A line cannot be removed if it has installed items associated with it (see below).

### Quantity

Only the *available* quantity of a stock item can be disassembled. A [serialized](./traceability.md#serial-numbers) stock item does not have an adjustable quantity - since it represents a single physical unit, it must always be disassembled in its entirety.

The original stock item is never deleted as a result of disassembly - its quantity is reduced by the disassembled amount, in order to preserve traceability. If a stock item is disassembled down to a zero quantity, it is retained in the database (in an *unavailable* state) rather than removed, even if the item has the [Delete on Deplete](./availability.md#delete-on-deplete) flag set. A serialized item cannot be reduced to a zero quantity, so in this case the original item is instead marked with a *Destroyed* status.

### Accounting for Installed Items

If the stock item being disassembled has other stock items [installed](../manufacturing/allocate.md#allocating-tracked-stock) within it (for example, tracked components that were installed during a build order), these installed items **must** be accounted for during disassembly:

- Each installed item is matched against a BOM line item, based on the component part (including any [substitute](../manufacturing/bom.md#substitute-bom-line-items) or [variant](../part/index.md#assembly) parts allowed for that line)
- Matched installed items are *uninstalled* directly, rather than being discarded and re-created - this preserves the original stock item, including its own stock tracking history, batch code, and cost entries
- The quantity requested for the matching BOM line is reduced by the quantity already covered by the installed item(s). A new stock item is only created for any remaining quantity - if the installed items fully cover the required quantity, no new stock item is created for that line
- Any installed item which does *not* match one of the selected BOM lines is still uninstalled (it cannot be left "installed" inside a smaller or non-existent parent), but its quantity is **not** subtracted from any line

Because installed items cannot be partially accounted for, **a stock item with any installed items must be disassembled in its entirety** - a partial disassembly (disassembling less than the full available quantity) is rejected if any items are currently installed.

The disassembly form displays a count of installed items against each matching BOM line, and lists any "leftover" installed items (which do not match a BOM line) in a separate warning panel.

### Component Costs

When a stock item is disassembled, a [cost entry](./costs.md) (with the *Material* cost type, and the *disassembly* source) may be recorded against each newly created component stock item:

- **Explicit unit cost:** If a *Unit Cost* is entered for a line, that cost is recorded against the generated stock item
- **Automatic allocation:** Lines without a *Unit Cost* share the *remaining cost* of the disassembled item, weighted by the existing [pricing](../part/pricing.md) data (average of minimum and maximum overall price, multiplied by the line quantity) for each component part

!!! warning "No Cost Recorded"
    Automatic allocation only happens if the disassembled item has a recorded [unit cost](./costs.md#unit-cost), **and** pricing data is available for **every** component without a *Unit Cost*. If pricing data is missing for any of these components, **no cost is recorded** for any of them - rather than recording an arbitrary split. To record a cost in this case, enter a *Unit Cost* for each component.

The *remaining cost* is calculated as follows:

- The cost of the disassembled units (unit cost &times; disassembled quantity)
- Less the cost of any [installed items](#accounting-for-installed-items) which are broken out - these keep their own cost entries, so their cost is not allocated again
- Less the total of any explicit *Unit Cost* values entered (unit cost &times; quantity)

If nothing remains (for example, the explicit costs already account for the full cost of the disassembled units), no cost is allocated. If the cost of the original stock item is a range (an estimate), the range is carried through to the allocated costs. Where the cost of an installed item is also a range, the *minimum* remaining cost deducts its *maximum* cost (and vice versa) - for example, a $10 - $12 assembly with a $1 - $8 installed item leaves $2 - $11 to be allocated.

Cost is only recorded against newly *created* stock items - matched installed items retain their own existing cost entries. The details of each automatic allocation are recorded in the source data of the cost entry.

#### Cost Information in the Form

The disassembly form explains how component costs will be recorded, and updates as unit costs are entered:

- **Automatic Cost Allocation:** The remaining cost (shown, where it can be calculated) will be allocated across the components without a *Unit Cost*
- **No Cost Will Be Recorded:** No cost will be recorded for the components without a *Unit Cost*. The reason is shown - for example, the disassembled item has no recorded cost (or its cost could not be converted to the default currency), the cost of an installed item could not be converted, or the components without pricing data are listed

The *Unit Cost* field of each line shows *Automatic* or *No cost recorded* (when left blank) accordingly. Users without the *Pricing* view role cannot view the cost and pricing data used for this calculation, and instead see a general explanation of these rules.

### Traceability

Disassembling a stock item generates a full audit trail:

- A `Disassembled into components` event is added to the [stock tracking history](./tracking.md) of the original stock item
- Each newly created component stock item records a `Created from disassembly` event, referencing the original stock item
- The *batch code* and source *purchase order* of the original stock item are copied directly to each generated component
- If the original stock item was generated by a build order, that build order cannot be directly copied to the new component (since the component was not actually built by that order) - instead, it is recorded as a reference within the `Created from disassembly` event

### Purchasing Bundled Items

Some suppliers only sell a group of components as a single bundled or "kit" product, rather than as individual purchasable line items. Such a bundle can be modelled as an assembly part, purchased and received as a single stock item, and later disassembled into its individual components - with cost and traceability data automatically apportioned across the generated components, as described above.

Refer to the [Bundled Items](../purchasing/purchase_order.md#bundled-items) documentation for a full description of how to set this up.

### Enforced Limitations

The following limitations are enforced when disassembling a stock item:

- The part associated with the stock item must be marked as an *assembly*
- The stock item must currently be [in stock](./status.md) - for example, it cannot be allocated to a sales order, installed in another assembly, or already fully consumed
- At least one BOM line item must be selected for disassembly
- The disassembly quantity cannot exceed the available quantity of the stock item
- A serialized stock item must be disassembled in its entirety (its quantity cannot be partially reduced)
- Each BOM line may only be referenced once per disassembly operation
- A selected BOM line must be a valid line item for the part associated with the stock item
- If the stock item has any installed items, it must be disassembled in its entirety
