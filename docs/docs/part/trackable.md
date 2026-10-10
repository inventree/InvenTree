---
title: Trackable Parts
---

## Stock Tracking

Denoting a part as *Trackable* changes the way that [stock items](../stock/index.md) associated with the particular part are handled in the database. A trackable part also has more restrictions imposed by the database scheme.

For many parts in an InvenTree database, simply tracking current stock levels (and locations) is sufficient. However, some parts require more extensive tracking than simple stock level knowledge.

Generally, a stock item associated with a trackable part should have either a batch number or a serial number. This includes stock created manually or via an internal process (such as a [Purchase Order](../purchasing/purchase_order.md) or a [Build Order](../manufacturing/build.md)).

However, this is not strictly enforced when creating a [build output](../manufacturing/output.md#create-build-output) - see [below](#build-orders) for further information.

## Assign Serial Numbers

Serial numbers (for parts which are marked as trackable) are used in multiple forms and processes in InvenTree.

For faster input there are several ways to define the wanted serial numbers(SN):

| Marker | Input | Result | Description |
| --- | --- | --- | --- |
|  | `1` | `[1]` | single SN |
| , | `1,3,5` | `[1, 3, 5]` | list of SNs |
| - | `1-5` | `[1, 2, 3, 4, 5]` | stretch of SN |
| ~ | `~` (next SN is 8) | `[8]` | represents the next SN |
| `<start>`+ | `4+` (with 3 numbers needed) | `[4, 5, 6]` | all needed SNs from `<start>` |
| `<start>`+`<length>` | `2+2` | `[2, 3, 4]` | `<length>` SNs added to `<start>` |

These rules can be mix-and-matched with whitespaces or commas separating them.
For example:
`1 3-5 9+2` or `1,3-5,9+2` result in `[1, 3, 4, 5, 9, 10, 11]`
`~+2`(with next SN being 14) results in `[14, 15, 16]`
`~+`(with next SN being 14 and 2 numbers needed) results in `[14, 15]`


## Build Orders

[Build orders](../manufacturing/build.md) have some extra requirements when either building a trackable part, or using parts in the Bill of Materials which are themselves trackable.

### Build Outputs Without Serial Numbers

When [creating a build output](../manufacturing/output.md#create-build-output) for a trackable part, serial numbers are *not* required at the point of creation. This allows a batch quantity of build outputs to be created up-front, and serialized at some later stage - for example, after receiving a batch of unserialized units against an [external build order](../manufacturing/external.md).

If serial numbers are not provided, a single build output is created with the specified quantity, rather than one output per unit. This output can subsequently be assigned [serial numbers](#assign-serial-numbers), or split into individual serialized units, before it is completed.

!!! note "Tracked BOM Items"
    If the Bill of Materials for the part being built contains *tracked* (trackable) sub-components, serial numbers are still required when creating build outputs, regardless of whether the assembled part itself is trackable. This is necessary so that each tracked sub-component can be allocated against a specific build output. Refer to the [build allocation documentation](../manufacturing/allocate.md#tracked-build-outputs) for further information.
