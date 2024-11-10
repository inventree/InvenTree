---
title: Stock
---

## Stock Location

A stock location represents a physical real-world location where *Stock Items* are stored. Locations are arranged in a cascading manner and each location may contain multiple sub-locations, or stock, or both.

### Icons

Stock locations can be assigned custom icons (either directly or through [Stock Location Types](#stock-location-type)). When using PUI there is a custom icon picker component available that can help to select the right icon. However in CUI the icon needs to be entered manually.

By default, the tabler icons package (with prefix: `ti`) is available. To manually select an item, search on the [tabler icons](https://tabler.io/icons) page for an icon and copy its name e.g. `bookmark`. Some icons have a filled and an outline version (if no variants are specified, it's an outline variant). Now these values can be put into the format: `<package-prefix>:<icon-name>:<variant>`. E.g. `ti:bookmark:outline` or `ti:bookmark:filled`.

If there are some icons missing in the tabler icons package, users can even install their own custom icon packs through a plugin. See [`IconPackMixin`](../extend/plugins/icon.md).

## Stock Location Type

A stock location type represents a specific type of location (e.g. one specific size of drawer, shelf, ... or box) which can be assigned to multiple stock locations. In the first place, it is used to specify an icon and having the icon in sync for all locations that use this location type, but it also serves as a data field to quickly see what type of location this is. It is planned to add e.g. drawer dimension information to the location type to add a "find a matching, empty stock location" tool.

## External Stock Location
An external stock location can be used to indicate that items in there might not be available
for immediate usage. Stock items in an external location are marked with an additional icon
in the build order line items view where the material is allocated.

{% with id="stock_external_icon", url="stock/stock_external_icon.png", description="External stock indication" %}
{% include 'img.html' %}
{% endwith %}

Anyhow there is no limitation on the stock item. It can be allocated as usual.

The external flag does not get inherited to sublocations.

## Stock Item

A *Stock Item* is an actual instance of a [*Part*](../part/part.md) item. It represents a physical quantity of the *Part* in a specific location.

### Stock Item Details

The *Stock Item* detail view shows information regarding the particular stock item:

**Part** - Which *Part* this stock item is an instance of

**Location** - Where is this stock item located?

**Quantity** - How many items are in stock?

**Supplier** - If this part was purchased from a *Supplier*, which *Supplier* did it come from?

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
