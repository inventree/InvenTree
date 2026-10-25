---
title: Stock Tracking
---

## Stock Tracking

Stock tracking records the history of stock item adjustments, including the user who performed the action, the date of the action, and the changes made to the stock item (e.g. quantity or location). This allows users to maintain a complete history of stock item movements and adjustments over time.

Stock tracking history is recorded in the [audit log](../concepts/audit.md) - each stock operation is recorded as a named [event](../concepts/audit.md#events) against each affected stock item.

### Tracking Events

Stock tracking events are recorded automatically whenever a stock item is adjusted, either through manual adjustments or through automated processes such as order fulfillment or build completion.

Some examples of operations that record stock tracking events include:

- Manual stock adjustments (e.g. correcting inventory counts)
- Creation of new stock items (e.g. receiving new inventory)
- Allocation of stock items to orders (e.g. shipping items against sales orders)
- Consumption of stock items during build processes (e.g. using items to complete a build order)

### Tracking Event Types

Each stock tracking event records a specific *type*, indicating which operation triggered it:

{{ statuscodes("StockHistoryCode") }}

!!! info "Legacy Event Types"
    The *Legacy stock tracking entry*, *Edited stock item* and *Assigned serial number* event types are only present in stock history recorded by older versions of InvenTree. Edits to a stock item (e.g. changing the status) are now recorded as regular updates in the audit log, and serial numbers are recorded as part of the creation of the stock item.

## Viewing Stock Tracking History

Stock tracking events are recorded in the [audit log](../concepts/audit.md), along with any other changes made to a stock item. Each event records the user who performed the action, any notes provided, and additional information about the event (such as the quantity added or removed, or the order which the item was received against).

!!! warning "Audit Log Required"
    Stock tracking history is recorded in the audit log. If the audit log is disabled (via the `Enable Audit Log` system setting), **no stock tracking history is recorded**. Refer to the [audit log documentation](../concepts/audit.md#settings) for more information.

### Stock Item History

The stock tracking history for a particular stock item is displayed in the *History* panel of the *Stock Item Detail* page:

{{ image("stock/stock_item_history.png", "Stock item history") }}

Each entry displays the type of event, along with any changes made to the stock item, and any additional information recorded against the event (such as notes, quantities, or links to related orders and stock items).

### Part History

The history of all stock items for a particular part is displayed in the *History* panel of the *Part Detail* page, along with any changes made to the part itself:

{{ image("stock/part_stock_history.png", "Part stock history") }}

!!! info "Show Change History"
    The *History* panel is only displayed if the *Show Change History* user setting is enabled. Refer to the [audit log documentation](../concepts/audit.md#viewing-change-history) for more information.

!!! info "Deleted Stock Items"
    Even if a stock item is deleted from the system, the associated history is retained for historical reference. It is visible in the history of the part, but not in the history of the stock item (as the stock item itself has been deleted).

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

Stock tracking history is recorded in the audit log, and is subject to the [audit log settings](../concepts/audit.md#settings). For example, old stock tracking history can be automatically removed using the {{ globalsetting("AUDIT_LOG_DELETE_OLD_ENTRIES", short=True) }} setting.

!!! info "Audit Log Retention"
    The *Delete Old Stock Tracking Entries* and *Stock Tracking Deletion Interval* settings have been removed. The retention of stock tracking history is now controlled by the audit log settings.
