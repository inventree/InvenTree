---
title: Sales Orders
---

## Sales Order List

The sales order list display shows all sales orders:

{% with id="so_list", url="app/so_list.png", maxheight="240px", description="Sales order list" %}
{% include "img.html" %}
{% endwith %}

Select an individual sales order to display the detail view for that order.

### Filtering

Displayed sales orders can be subsequently filtered using the search input at the top of the screen

## Sales Order Detail

Select an individual order to show the detailed view for that order:

{% with id="so_detail", url="app/so_detail.png", maxheight="240px", description="Sales order details" %}
{% include "img.html" %}
{% endwith %}

### Edit Order Details

From the detail view, select the *Edit* button in the top-right of the screen. This opens the sales order editing display.

### Line Items

View the line items associated with the selected order:

{% with id="so_lines", url="app/so_lines.png", maxheight="240px", description="Sales order lines" %}
{% include "img.html" %}
{% endwith %}
