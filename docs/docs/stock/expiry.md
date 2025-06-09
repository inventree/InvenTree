---
title: Stock Expiry
---

## Stock Expiry

InvenTree supports stock expiration dates, which allows individual stock items to be automatically marked as *expired* past a certain calendar date.

The stock expiry feature is disabled by default, and must be enabled via the settings menu:

{{ image("stock/enable_stock_expiry.png", title="Enable stock expiry feature") }}


!!! info "Non Expiring Stock"
    If a Stock Item is not expected to expire, leave the expiry date field blank, or zero

### Add Expiry Date

When creating a new stock item, the expiry date can be manually set by the user.

{{ image("stock/expiry_date_create.png", title="Add expiry date") }}

If an expiry date is defined for a particular stock item, it will be displayed on the detail page. If the expiry date has passed (and the stock item is *expired*) then this will also be indicated.

{{ image("stock/item_expired.png", title="Display expiry date") }}

The expiry date can be adjusted in the stock item edit form.

{{ image("stock/expiry_date_edit.png", title="Edit expiry date") }}

### Filter Expired Stock

The various stock display tables can be filtered by *expired* status, and also display a column for the expiry date for each stock item.

{{ image("stock/stock_table_expiry.png", title="Filter by stock expiry") }}

### Index Page

If the stock expiry feature is enabled, expired stock are listed on the InvenTree home page, to provide visibility of expired stock to the users.

## Part Expiry Time

In addition to allowing manual configuration of expiry dates on a per-item basis, InvenTree also provides the ability to set a "default expiry time" for a particular Part. This expiry time (specified in *days*) is then used to automatically calculate the expiry date when creating a new Stock Item as an instance of the given Part.

For example, if a Part has a default expiry time of 30 days, then any Stock Items created for that Part will automatically have their expiry date set to 30 days in the future.

!!! info "Non Expiring Parts"
    If a part is not expected to expire, set the default expiry time to 0 (zero) days.

If a Part has a non-zero default expiry time, it will be displayed on the Part details page

{{ image("stock/part_expiry_display.png", title="Display part expiry") }}

The Part expiry time can be altered using the Part editing form.

{{ image("stock/part_expiry.png", title="Edit part expiry") }}

## Sales and Build Orders

By default, expired Stock Items cannot be added to neither a Sales Order nor a Build Order. This behavior can be adjusted using the *Sell Expired Stock* and *Build Expired Stock* settings:

{{ image("stock/sell_build_expired_stock.png", title="Sell and build expired stock") }}
