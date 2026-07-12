---
title: Stock Tracking
---

## Stock Tracking

Stock tracking entries record the history of stock item adjustments, including the user who performed the action, the date of the action, and the quantity change. This allows users to maintain a complete history of stock item movements and adjustments over time.

### Tracking Events

Stock tracking entries are created automatically whenever a stock item is adjusted, either through manual adjustments or through automated processes such as order fulfillment or build completion.

Some examples of events that may trigger stock tracking entries include:

- Manual stock adjustments (e.g. correcting inventory counts)
- Creation of new stock items (e.g. receiving new inventory)
- Allocation of stock items to orders (e.g. shipping items against sales orders)
- Consumption of stock items during build processes (e.g. using items to complete a build order)

## Viewing Stock Tracking History

There are multiple ways to view the stock tracking history for a particular stock item or part via the user interface.

### Stock Item Tracking History

The stock tracking history for a particular stock item can be viewed on the *Stock Item Detail* page, under the *Stock Tracking* tab:

{{ image("stock/stock_item_tracking_history.png", title="Stock tracking tab") }}

This view displays all tracking entries associated with the particular stock item.

### Part Tracking History

Additionally, the stock tracking history for a particular part can be viewed on the *Part Detail* page, under the *Stock History* tab:

{{ image("stock/part_tracking_history.png", title="Part stock tracking history") }}

This view displays all tracking entries associated with any stock item linked to the particular part.

!!! info "Deleted Stock Items"
    Even if a stock item is deleted from the system, the associated stock tracking entries are retained for historical reference. They will be visible in the part tracking history, but not in the stock item tracking history (as the stock item itself has been deleted).

## Installed Stock Items

A stock item can be *installed* inside another stock item, forming a parent/child relationship between the two. This is used to represent physical assembly - for example, a serialized PCB assembly which has been fitted with a tracked sub-component, such as a wireless module or a pre-programmed IC.

An installed stock item is no longer available for regular stock actions (it cannot be moved, allocated to an order, or built into another assembly) while it remains installed - it is only accessible "through" its parent item.

### How Items Become Installed

There are two ways that a stock item can become installed inside another:

- **Tracked build allocation** - when a [tracked BOM item](../manufacturing/allocate.md#allocating-tracked-stock) is allocated to a build order and the build output is completed, the allocated stock item is automatically installed into the completed build output
- **Manual installation** - from the *Stock Item Detail* page, a user can manually install one stock item into another, using the *Install Item* action. By default, the selected item's part must appear in the [Bill of Materials](../manufacturing/bom.md) of the parent item's part - this check can be disabled using the {{ globalsetting("STOCK_ENFORCE_BOM_INSTALLATION", short=True) }} setting

### Viewing Installed Items

Any stock items installed within a particular stock item are displayed on the *Installed Items* tab of the *Stock Item Detail* page.

By default, installed stock items are hidden from general stock item tables (as they are not directly available for use) - this can be changed using the {{ globalsetting("STOCK_SHOW_INSTALLED_ITEMS", short=True) }} setting.

### Removing Installed Items

An installed stock item can be removed (uninstalled) from its parent using the *Uninstall Item* action, which returns the item to a selected stock location and makes it available for regular stock actions once more.

Additionally, installed items are automatically uninstalled when the parent item is [disassembled](./disassemble.md#accounting-for-installed-items) into its component parts - refer to that page for a detailed description of how installed items are matched against Bill of Materials line items during disassembly.

## Stock Tracking Settings

There are a number of configuration options available for controlling the behavior of stock tracking functionality in the [system settings view](../settings/global.md):

| Name | Description | Default | Units |
| ---- | ----------- | ------- | ----- |
{{ globalsetting("STOCK_TRACKING_DELETE_OLD_ENTRIES") }}
{{ globalsetting("STOCK_TRACKING_DELETE_DAYS") }}
