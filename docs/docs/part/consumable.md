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

### Stock Items

Consumable parts can have stock items associated with them, the same as any other part. Stock levels for consumable parts can be tracked and managed as normal.

### Bills of Material

Consumable parts can be added as a subcomponent to the [Bills of Material](../manufacturing/bom.md) for an assembled part, in the same way as any other component.

### Build Orders

Unlike a regular component, a consumable part is not allocated to (or consumed by) a [Build Order](../manufacturing/build.md). When a build order is completed, stock quantities for consumable parts are not adjusted.

If stock levels for a consumable part need to be updated to reflect usage during a build, this must be done manually.
