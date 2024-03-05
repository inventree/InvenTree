---
title: Purchase Orders
---

## Purchase Order List

The purchase order list display lists all purchase orders:

{% with id="po_list", url="app/po_list.png", maxheight="240px", description="Purchase order list" %}
{% include "img.html" %}
{% endwith %}

Select an individual purchase order to display the detail view for that order.

### Filtering

Displayed purchase orders can be subsequently filtered using the search input at the top of the screen

## Purchase Order Detail

{% with id="po_detail", url="app/po_detail.png", maxheight="240px", description="Purchase order details" %}
{% include "img.html" %}
{% endwith %}

### Edit Order Details

From the detail view, select the *Edit* button in the top-right of the screen. This opens the purchase order editing display:

{% with id="edit_po", url="app/po_edit.png", maxheight="240px", description="Edit purchase order" %}
{% include "img.html" %}
{% endwith %}

### Line Items

The *Line Items* tab shows the line items associated with this purchase order:

{% with id="po_lines", url="app/po_lines.png", maxheight="240px", description="Purchase order line items" %}
{% include "img.html" %}
{% endwith %}

Long press on a particular line item to receive the item into stock.

### Stock Items

Once items have been received into stock against a particular purchase order, they are displayed in the *Stock Items* tab:

{% with id="po_stock", url="app/po_stock.png", maxheight="240px", description="Purchase order stock items" %}
{% include "img.html" %}
{% endwith %}
