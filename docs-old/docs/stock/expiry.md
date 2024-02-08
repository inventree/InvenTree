---
title: Stock Expiry
---

## Stock Expiry

InvenTree supports stock expiration dates, which allows individual stock items to be automatically marked as *expired* past a certain calendar date.

The stock expiry feature is disabled by default, and must be enabled via the settings menu:

{% with id="stock_expiry", url="stock/enable_stock_expiry.png", description="Enable stock expiry feature" %}
{% include 'img.html' %}
{% endwith %}

!!! info "Non Expiring Stock"
    If a Stock Item is not expected to expire, leave the expiry date field blank, or zero

### Add Expiry Date

When creating a new stock item, the expiry date can be manually set by the user.

{% with id="expiry_create", url="stock/expiry_date_create.png", description="Add expiry date" %}
{% include 'img.html' %}
{% endwith %}

If an expiry date is defined for a particular stock item, it will be displayed on the detail page. If the expiry date has passed (and the stock item is *expired*) then this will also be indicated.

{% with id="item_expired", url="stock/item_expired.png", description="Display expiry date" %}
{% include 'img.html' %}
{% endwith %}

The expiry date can be adjusted in the stock item edit form.

{% with id="expiry_edit", url="stock/expiry_date_edit.png", description="Edit expiry date" %}
{% include 'img.html' %}
{% endwith %}

### Filter Expired Stock

The various stock display tables can be filtered by *expired* status, and also display a column for the expiry date for each stock item.

{% with id="stock_table_expiry", url="stock/stock_table_expiry.png", description="Filter by stock expiry" %}
{% include 'img.html' %}
{% endwith %}

### Index Page

If the stock expiry feature is enabled, expired stock are listed on the InvenTree home page, to provide visibility of expired stock to the users.

## Part Expiry Time

In addition to allowing manual configuration of expiry dates on a per-item basis, InvenTree also provides the ability to set a "default expiry time" for a particular Part. This expiry time (specified in *days*) is then used to automatically calculate the expiry date when creating a new Stock Item as an instance of the given Part.

For example, if a Part has a default expiry time of 30 days, then any Stock Items created for that Part will automatically have their expiry date set to 30 days in the future.

!!! info "Non Expiring Parts"
    If a part is not expected to expire, set the default expiry time to 0 (zero) days.

If a Part has a non-zero default expiry time, it will be displayed on the Part details page

{% with id="part_expiry_display", url="stock/part_expiry_display.png", description="Part expiry" %}
{% include 'img.html' %}
{% endwith %}

The Part expiry time can be altered using the Part editing form.

{% with id="part_expiry_edit", url="stock/part_expiry.png", description="Edit part expiry" %}
{% include 'img.html' %}
{% endwith %}

## Sales and Build Orders

By default, expired Stock Items cannot be added to neither a Sales Order nor a Build Order. This behavior can be adjusted using the *Sell Expired Stock* and *Build Expired Stock* settings:

{% with id="sell_build_expired", url="stock/sell_build_expired_stock.png", description="Sell Build Expired Stock" %}
{% include 'img.html' %}
{% endwith %}
