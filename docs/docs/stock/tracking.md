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

## Stock Tracking Settings

There are a number of configuration options available for controlling the behavior of stock tracking functionality in the [system settings view](../settings/global.md):

| Name | Description | Default | Units |
| ---- | ----------- | ------- | ----- |
{{ globalsetting("STOCK_TRACKING_DELETE_OLD_ENTRIES") }}
{{ globalsetting("STOCK_TRACKING_DELETE_DAYS") }}
