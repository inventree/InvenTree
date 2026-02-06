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

## Stock Tracking Settings

There are a number of configuration options available for controlling the behavior of stock tracking functionality in the [system settings view](../settings/global.md):

| Name | Description | Default | Units |
| ---- | ----------- | ------- | ----- |
{{ globalsetting("STOCK_TRACKING_DELETE_OLD_ENTRIES") }}
{{ globalsetting("STOCK_TRACKING_DELETE_DAYS") }}
