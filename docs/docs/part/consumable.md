---
title: Consumable Parts
---

## Consumable Parts

A *Consumable* part is one which is generally used up, or expended, during a build or other process, rather than being tracked and allocated as a discrete item.

Consumable parts can be used to represent things such as:

- Glue or adhesive
- Solder
- Cleaning fluid
- Fasteners or other low-value hardware
- Other general workshop supplies

Marking a part as consumable is intended to help distinguish these types of supplies from other parts in the inventory, making it easier to filter and report on "real" stock items versus general consumables.

### Why Mark a Part as Consumable?

Not every item required to complete a build needs to be tracked and allocated with the same rigor as a high-value component. A part might be marked as consumable because it is:

- Low value, making the overhead of precise allocation not worth the effort
- Kept in abundant stock, such that running out is unlikely to be a concern
- Difficult to track in discrete units, such as a fluid or adhesive
- Not something the business needs (or wants) visibility into at the build order level

Marking a part as consumable communicates this intent clearly wherever the part is used, without needing to remember to configure each individual BOM line item.

### Stock Items

Consumable parts can have stock items associated with them, the same as any other part. Stock levels for consumable parts can be tracked and managed as normal.

### Bills of Material

Consumable parts can be added as a subcomponent to the [Bills of Material](../manufacturing/bom.md) for an assembled part, in the same way as any other component.

### Build Orders

Unlike a regular component, a consumable part is not allocated to (or consumed by) a [Build Order](../manufacturing/build.md). When a build order is completed, stock quantities for consumable parts are not adjusted.

If stock levels for a consumable part need to be updated to reflect usage during a build, this must be done manually.

### Consumable BOM Line Items

Separately from the *Consumable* flag on the part itself, an individual [BOM line item](../manufacturing/bom.md#consumable-bom-line-items) can also be marked as *consumable*.

This allows a part which is **not** normally marked as consumable to be treated as consumable *for the purposes of a specific BOM*. For example, a fastener which is usually tracked precisely in one assembly might be treated as consumable in another assembly, without needing to change the underlying part definition.

In other words:

- The part-level *Consumable* flag is a permanent property of the part, and applies everywhere that part is used.
- The BOM line item *Consumable* flag is a per-assembly override, and only affects how that part is treated within that particular BOM.

If a part is already marked as consumable, marking the corresponding BOM line item as consumable as well has no additional effect.
