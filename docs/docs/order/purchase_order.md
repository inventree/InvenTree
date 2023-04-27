---
title: Purchase Order
---

## Purchase Orders

Purchase orders allow to track which parts are bought from suppliers and manufacturers, therefore converting externally bought items into stock items / inventory.

To access the purchase order page, click on the <span class="badge inventree nav main"><span class='fas fa-shopping-cart'></span> Buy</span> navigation tab and click on <span class="badge inventree nav main"><span class='fas fa-list'></span> Purchase Orders</span> option in the dropdown list.

{% with id="purchase_order_list", url="order/po_list.png", description="Purchase Order List" %}
{% include "img.html" %}
{% endwith %}

### Purchase Order Status Codes

Each Purchase Order has a specific status code which indicates the current state of the order:

| Status | Description |
| --- | --- |
| Pending | The purchase order has been created, but has not been submitted to the supplier |
| In Progress | The purchase order has been issued to the supplier, and is in progress |
| Complete | The purchase order has been completed, and is now closed |
| Cancelled | The purchase order was cancelled, and is now closed |

### Purchase Order Currency

The currency code can be specified for an individual purchase order. If not specified, the default currency specified against the [supplier](./company.md#suppliers) will be used.

## Create Purchase Order

Once the purchase order page is loaded, click on <span class="badge inventree add"><span class='fas fa-plus-circle'></span> New Purchase Order</span> which opens the "Create Purchase Order" form.

A purchase order is linked to a specific supplier, select one in the list of existing suppliers.

!!! warning
	Only companies with the "Supplier" attribute enabled will be shown and can be selected

Fill out the rest of the form with the purchase order information then click on <span class="badge inventree confirm">Submit</span>

### Purchase Order Reference

Each Purchase Order is uniquely identified by its *Reference* field. Read more about [reference fields](../settings/reference.md).

### Add Line Items

On the purchase order detail page, user can link parts to the purchase order selecting the <span class="badge inventree nav side"><span class='fas fa-list'></span> Order Items</span> tab then clicking on the <span class="badge inventree add"><span class='fas fa-plus-circle'></span> Add Line Item</span> button.

Once the "Add Line Item" form opens, select a supplier part in the list.

!!! warning
    Only parts from the supplier selected for the purchase order will be shown and can be selected

Fill out the rest of the form then click on <span class="badge inventree confirm">Submit</span>

#### Upload File

It is possible to upload an exported purchase order from the supplier instead of manually entering each line item. To start the process, click on <span class="badge inventree confirm"><span class='fas fa-upload'></span> Upload File</span> button next to the <span class="badge inventree add"><span class='fas fa-plus-circle'></span> Add Line Item</span> button and follow the steps.

!!! info "Supported Formats"
	This process only supports tabular data and the following formats are supported: CSV, TSV, XLS, XLSX, JSON and YAML

### Issue Order

Once all the line items were added, click on the <span class='fas fa-paper-plane'></span> button on the main purchase order detail panel and confirm the order has been submitted.

### Receive Line Items

After receiving all the items from the order, the purchase order will convert the line items into stock items / inventory.

There are two options to mark items as "received":

* either individually: click on <span class='fas fa-clipboard-check'></span> button on each line item
* or globally: click on the <span class='fas fa-clipboard-check'></span> button on the main purchase order detail panel and confirm all items in the order have been received.

!!! note "Permissions"
	Marking line items as received requires the "Purchase order" ADD permission.

### Received Items

Each item marked as "received" is automatically converted into a stock item.

To see the list of stock items created from the purchase order, click on the <span class="badge inventree nav side"><span class='fas fa-sign-in-alt'></span> Received Items</span> tab.

### Complete Order

Once the quantity of all __received__ items is equal or above the quantity of all line items, the order will be automatically marked as __complete__.

It is also possible to complete the order before all items were received (or if there were missing items).
To do so, click on the <span class='fas fa-check-circle'></span> button on the main purchase order detail panel and confirm the order was completed.

### Cancel Order

In the event that the order won't be processed, user has the option of cancelling the order instead.
To do so, simply click on the <span class='fas fa-times-circle'></span> button on the main purchase order detail panel and confirm the purchase order has been cancelled.

### Duplicate Purchase Order

Duplicating a Purchase Order allows the user to quickly create a new *copy* of an existing order, using the same supplier and line item information.

To duplicate an existing order, select the *Duplicate Order* action from the menu in the top-right of the screen (as shown below):

{% with id="purchase_order_duplicate", url="order/po_duplicate.png", description="Duplicate Purchase Order" %}
{% include "img.html" %}
{% endwith %}

This opens the following dialog, where you can adjust the parameters of the new order before proceeding to actually create the new order. You can see in the screenshot below that some extra options are provided in this form, to control duplication of individual line items.

{% with id="purchase_order_duplicate_2", url="order/po_duplicate_2.png", description="Duplicate Purchase Order" %}
{% include "img.html" %}
{% endwith %}

A new purchase order is then created based on the currently selected order:

{% with id="purchase_order_duplicate_3", url="order/po_duplicate_3.png", description="Duplicate Purchase Order" %}
{% include "img.html" %}
{% endwith %}

### Calendar view

Using the button to the top right of the list of Purchase Orders, the view can be switched to a calendar view using the button <span class='fas fa-calendar-alt'></span>. This view shows orders with a defined target date only.

This view can be accessed externally as an ICS calendar using a URL like the following:
`http://inventree.example.org/api/order/calendar/purchase-order/calendar.ics`

by default, completed orders are not exported. These can be included by appending `?include_completed=True` to the URL.
