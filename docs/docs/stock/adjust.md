---
title: Stock Adjustments
---

## Stock Adjustments

InvenTree provides simple yet powerful management of stock levels. Multiple stock adjustment options are available, and each type of adjustment is automatically tracked to maintain a complete stock history.

Stock adjustments can be accessed in any stock items table using the "Stock Options" dropdown entries:

{% with id="stock_options", url="stock/stock_options.png", description="Stock Options" %}
{% include 'img.html' %}
{% endwith %}

### Move Stock

Multiple stock items can be moved to a new location in a single operation. Each item is moved to the selected location, and a stock tracking entry is added to the stock item history.

{% with id="stock_move", url="stock/stock_move.png", description="Stock movement" %}
{% include 'img.html' %}
{% endwith %}

### Add Stock

Add parts to a stock item record - for example putting parts back into stock. The in-stock quantity for each selected item is increased by the given amount.

{% with id="stock_add", url="stock/stock_add.png", description="Stock addition" %}
{% include 'img.html' %}
{% endwith %}

### Remove Stock

Remove parts from a stock item record - for example taking parts from stock for use. The in-stock quantity for each selected item is decreased by the given amount.

{% with id="stock_remove", url="stock/stock_remove.png", description="Stock removal" %}
{% include 'img.html' %}
{% endwith %}

### Count Stock

Count stock items (stocktake) to record the number of items in stock at a given point of time. The quantity for each part is pre-filled with the current quantity based on stock item history.

{% with id="stock_count", url="stock/stock_count.png", description="Stock count" %}
{% include 'img.html' %}
{% endwith %}

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

To merge stock items, check two or more items in a stock table and click on the <span class='fas fa-boxes'></span> icon above the table, then click on "<span class='fas fa-object-group'></span> Merge Stock" menu option.

In the Merge Stock Items form, user can decide to allow mismatched suppliers or status to be merged together (disabled by default).

{% with id="stock_item_merge", url="stock/stock_item_merge.png", description="Stock Item Merge" %}
{% include 'img.html' %}
{% endwith %}

Select the location for the new stock item and confirm the merge, then click on <span class="badge inventree confirm">Submit</span> to process the merge.
