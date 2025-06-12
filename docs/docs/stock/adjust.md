---
title: Stock Adjustments
---

## Stock Adjustments

InvenTree provides simple yet powerful management of stock levels. Multiple stock adjustment options are available, and each type of adjustment is automatically tracked to maintain a complete stock history.

Stock adjustments can be accessed in any stock items table using the "Stock Options" dropdown entries:

{{ image("stock/stock_options.png", "Stock Options") }}

### Move Stock

Multiple stock items can be moved to a new location in a single operation. Each item is moved to the selected location, and a stock tracking entry is added to the stock item history.

{{ image("stock/stock_move.png", "Stock Move") }}

### Add Stock

Add parts to a stock item record - for example putting parts back into stock. The in-stock quantity for each selected item is increased by the given amount.

{{ image("stock/stock_add.png", "Stock Add") }}

### Remove Stock

Remove parts from a stock item record - for example taking parts from stock for use. The in-stock quantity for each selected item is decreased by the given amount.

{{ image("stock/stock_remove.png", "Stock Remove") }}

### Count Stock

Count stock items (stocktake) to record the number of items in stock at a given point of time. The quantity for each part is pre-filled with the current quantity based on stock item history.

{{ image("stock/stock_count.png", "Stock Count") }}

### Merge Stock

Users can merge two or more stock items together.

The conditions for merging stock items are the following:

- a stock item cannot be merged with itself
- only stock items referring to the same part can be merged
- supplier parts between all items have to match, unless user explicitly allows supplier parts to be different (see below)
- stock status between all items have to match, unless user explicitly allows stock status to be different (see below).

Moreover, if one of the item:

- is assigned to a sale order
- or is installed in another item
- or contains other items
- or is assigned to a customer
- or is currently in production
- or is serialized

then the merge would not be possible.

If the conditions are met, the process of merging will add up the stock quantity for all items involved in the merge and create a new stock item with the final calculated quantity.

To merge stock items, check two or more items in a stock table and click on the {{ icon("packages", title="Stock Actions") }} icon above the table, then click on {{ icon("arrow-merge", title="Merge") }} menu option.

In the Merge Stock Items form, user can decide to allow mismatched suppliers or status to be merged together (disabled by default).

{{ image("stock/stock_item_merge.png", "Stock Item Merge") }}

Select the location for the new stock item and confirm the merge, then click on <span class="badge inventree confirm">Submit</span> to process the merge.
