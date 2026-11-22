---
title: Stock
---

## Stock Item

A *Stock Item* is an actual instance of a [*Part*](../part/index.md) item. It represents a physical quantity of the *Part* in a specific location.

Each Part instance may have multiple stock items associated with it, in various quantities and locations. Additionally, each stock item may have a serial number (if the part is tracked by serial number) and may be associated with a particular supplier part (if the item was purchased from a supplier).

### Stock Item Details

Each *Stock Item* is linked to the following information:

**Part** - Which *Part* this stock item is an instance of

**Location** - Where is this stock item located?

**Quantity** - How many items are in stock?

**Supplier** - If this part was purchased from a *Supplier*, which *Supplier* did it come from?

**Supplier Part** - Link to the particular *Supplier Part*, if appropriate.

**Last Updated** - Date that the stock quantity was last updated

**Last Stocktake** - Date that this stock item was last counted

**Status** - Status of this stock item

**Serial Number** - If the part is tracked by serial number, the unique serial number of this stock item

**Batch Code** - If the part is tracked by batch code, the batch code of this stock item

## Stock Availability

InvenTree has a number of different mechanisms to determine whether stock is available for use. See the [Stock Availability](./availability.md) page for more information.

## Traceability

Stock items can be associated with a unique serial number and / or a batch code, which allows for traceability of individual stock items. This is particularly useful for tracking the history of specific items, and for ensuring that items can be traced back to their source (e.g. supplier, purchase order, etc).

Refer to the [traceability](./traceability.md) page for more information on how serial numbers and batch codes work in InvenTree.

## Stock Tracking

Every time a *Stock Item* is adjusted, a stock tracking event is automatically recorded in the [audit log](../concepts/audit.md). This ensures a complete history of the *Stock Item* is maintained.

Each stock tracking event records the user who performed the action. [Read more about stock tracking here](./tracking.md).

## Stock Locations

A stock location represents a physical real-world location where *Stock Items* are stored. Locations are arranged in a cascading manner and each location may contain multiple sub-locations, or stock, or both.

### Icons

Stock locations can be assigned custom icons (either directly or through [Stock Location Types](#stock-location-type)). In the web interface there is a custom icon picker component available that can help to select the right icon. However in CUI the icon needs to be entered manually.

By default, the tabler icons package (with prefix: `ti`) is available. To manually select an item, search on the [tabler icons](https://tabler.io/icons) page for an icon and copy its name e.g. `bookmark`. Some icons have a filled and an outline version (if no variants are specified, it's an outline variant). Now these values can be put into the format: `<package-prefix>:<icon-name>:<variant>`. E.g. `ti:bookmark:outline` or `ti:bookmark:filled`.

If there are some icons missing in the tabler icons package, users can even install their own custom icon packs through a plugin. See [`IconPackMixin`](../plugins/mixins/icon.md).

## Stock Location Type

A stock location type describes a kind of location, such as a drawer, shelf, or box. Multiple stock locations can share a type and use its default icon.

Open a type from **Admin Center → Location Types** or from the **Location Type** link in a stock location's details. Use the **Parameters** tab to record shared properties such as the internal dimensions of a drawer. Values are stored on the type, so you can update them in one place. Individual locations can also have their own parameters.

## External Stock Location

It may be useful to mark certain stock locations as *external*. An external stock location can be used to indicate that items in there might not be available for immediate usage. Stock items in an external location are marked with an additional icon
in the build order line items view where the material is allocated.

{{ image("stock/stock_external_icon.png", title="External stock indication") }}

The external flag does not get inherited to sublocations.

### Structural Locations

A stock location may be optionally marked as *structural*. Structural locations are used to represent physical locations which are not directly associated with stock items, but rather serve as a means of organizing the stock location hierarchy. For example, a structural location might represent a particular shelf or drawer within a warehouse, while the actual stock items are stored in sub-locations within that location.
