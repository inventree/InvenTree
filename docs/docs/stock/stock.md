---
title: Stock
---

## Stock Location

A stock location represents a physical real-world location where *Stock Items* are stored. Locations are arranged in a cascading manner and each location may contain multiple sub-locations, or stock, or both.

## Stock Item

A *Stock Item* is an actual instance of a [*Part*](../part/part.md) item. It represents a physical quantity of the *Part* in a specific location.

### Stock Item Details

The *Stock Item* detail view shows information regarding the particular stock item:

**Part** - Which *Part* this stock item is an instance of

**Location** - Where is this stock item located?

**Quantity** - How many items are in stock?

**Supplier** - If this part was purcahsed from a *Supplier*, which *Supplier* did it come from?

**Supplier Part** - Link to the particular *Supplier Part*, if appropriate.

**Last Updated** - Date that the stock quantity was last updated

**Last Stocktake** - Date of most recent stocktake (count) of this item

**Status** - Status of this stock item

### Stock Tracking

Every time a *Stock Item* is adjusted, a *Stock Tracking* entry is automatically created. This ensures a complete history of the *Stock Item* is maintained as long as the item is in the system.

Each stock tracking historical item records the user who performed the action.

## Supplier Part Pack Size

Supplier parts can have a pack size defined. This value is defined when creating or editing a part. By default, the pack size is 1.

When buying parts, they are bought in packs. This is taken into account in Purchase Orders: if a supplier part with a pack size of 5 is bought in a quantity of 4, 20 parts will be added to stock when the parts are received.

When adding stock manually, the supplier part can be added in packs or in individual parts. This is to allow the addition of items in opened packages. Set the flag "Use pack size" (`use_pack_size` in the API) to True in order to add parts in packs.
