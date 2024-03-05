---
title: Sales Orders
---

## Sales Orders

Sales orders allow tracking of which stock items are sold to customers, therefore converting stock items / inventory into externally sold items.

To access the sales order page, click on the <span class="badge inventree nav main"><span class='fas fa-truck'></span> Sell</span> navigation tab and click on <span class="badge inventree nav main"><span class='fas fa-list'></span> Sales Orders</span> option in the dropdown list.

{% with id="sales_order_list", url="order/so_list.png", description="Sales Order List" %}
{% include "img.html" %}
{% endwith %}

### Sales Order Status Codes

Each Sales Order has a specific status code, which represents the state of the order:

| Status | Description |
| --- | --- |
| Pending | The sales order has been created, but has not been finalized or submitted |
| In Progress | The sales order has been issued, and is in progress |
| Shipped | The sales order has been completed, and is now closed |
| Cancelled | The sales order was cancelled, and is now closed |

### Sales Order Currency

The currency code can be specified for an individual sales order. If not specified, the default currency specified against the [customer](./company.md#customers) will be used.

## Create a Sales Order

Once the sales order page is loaded, click on <span class="badge inventree add"><span class='fas fa-plus-circle'></span> New Sales Order</span> which opens the "Create Sales Order" form.

A Sales Order is linked to a specific customer, select one in the list of existing customers.

!!! warning "Customers Only"
	Only companies with the "Customer" attribute enabled will be shown and can be selected

Fill out the rest of the form with the sales order information then click on <span class="badge inventree confirm">Submit</span> to create the order.

### Sales Order Reference

Each Sales Order is uniquely identified by its *Reference* field. Read more about [reference fields](../settings/reference.md).

#### Add Line Items

On the sales order detail page, user can link parts to the sales order selecting the <span class="badge inventree nav side"><span class='fas fa-list-ol'></span> Line Items</span> tab then clicking on the <span class="badge inventree add"><span class='fas fa-plus-circle'></span> Add Line Item</span> button.

Once the "Add Line Item" form opens, select a part in the list.

!!! warning
    Only parts that have the "Salable" attribute enabled will be shown and can be selected

Fill out the rest of the form then click on <span class="badge inventree confirm">Submit</span>

#### Shipments

After all line items were added to the sales order, user needs to create one or more [shipments](#sales-order-shipments) in order to allocate stock for those parts.

In order to create a new shipment:

1. Click on the <span class="badge inventree nav side"><span class='fas fa-truck-loading'></span> Pending Shipments</span> tab
2. Click on <span class="badge inventree add"><span class='fas fa-plus-circle'></span> New Shipment</span> button, fill out the form with the shipment number (tracking number can be added but is optional) then click on <span class="badge inventree confirm">Submit</span>

Repeat the two steps above to create more shipments.

#### Allocate Stock Items

After shipments were created, user can either:

* allocate stock items for that part to the sales order (click on <span class='fas fa-sign-in-alt'></span> button)
* or create a build order for that part to cover the quantity of the sales order (click on <span class='fas fa-tools'></span> button)

During the allocation process, user is required to select the desired shipment that will contain the stock items.

#### Complete Shipment

To complete a shipment, click on the <span class="badge inventree nav side"><span class='fas fa-truck-loading'></span> Pending Shipments</span> tab then click on <span class='fas fa-truck'></span> button shown in the shipment table.

Fill out the "Complete Shipment" form then click on <span class="badge inventree confirm">Submit</span>.

To view all the completed shipment, click on the <span class="badge inventree nav side"><span class='fas fa-truck'></span> Completed Shipments</span> tab. In the completed shipments table, click on the <span class='fas fa-plus'></span> icon next to each shipment reference to see the items and quantities which were shipped.

### Complete Order

Once all items in the sales order have been shipped, click on <span class="badge inventree add"><span class='fas fa-check-circle'></span> Complete Order</span> to mark the sales order as complete.

### Cancel Order

To cancel the order, click on the <span class='fas fa-tools'></span> menu button next to the <span class="badge inventree add"><span class='fas fa-check-circle'></span> Complete Order</span> button, then click on the "<span class='fas fa-tools'></span> Cancel Order" menu option. Confirm then click on the <span class="badge inventree confirm">Submit</span> to cancel the order.


### Calendar view

Using the button to the top right of the list of Sales Orders, the view can be switched to a calendar view using the button <span class='fas fa-calendar-alt'></span>. This view shows orders with a defined target date only.

This view can be accessed externally as an ICS calendar using a URL like the following:
`http://inventree.example.org/api/order/calendar/sales-order/calendar.ics`

By default, completed orders are not exported. These can be included by appending `?include_completed=True` to the URL.

## Sales Order Shipments


Shipments are used to track sales items when they are shipped to customers. Multiple shipments can be created against a [Sales Order](./sales_order.md), allowing line items to be sent to customers in multiple deliveries.

On the main Sales Order detail page, the order shipments are split into two categories, *Pending Shipments* and *Completed Shipments*:

### Pending Shipments

The *Pending Shipments* panel displays the shipments which have not yet been sent to the customer.

- Each shipment displays the items which have been allocated to it
- Pending sales order items can be allocated to these shipments
- New shipments can be created if the order is still open

{% with id="pending-shipments", url="order/pending_shipments.png", description="Pending shipments" %}
{% include "img.html" %}
{% endwith %}

#### Creating a new Shipment

To create a new shipment for a sales order, press the *New Shipment* button above the pending shipments table.

#### Completing a Shipment

To complete a shipment, press the *Complete Shipment* button associated with the particular shipment:

{% with id="complete-shipment", url="order/complete_shipment.png", description="Complete shipment" %}
{% include "img.html" %}
{% endwith %}

Alternatively, pending shipments can be completed by selecting the *Complete Shipments* action from the sales order actions menu:

{% with id="complete-shipment-action", url="order/complete_shipment_action.png", description="Complete shipment" %}
{% include "img.html" %}
{% endwith %}

### Completed Shipments

{% with id="completed-shipments", url="order/completed_shipments.png", description="Completed shipments" %}
{% include "img.html" %}
{% endwith %}

### Shipment Data

Each shipment provides the following data fields:

#### Reference

A unique number for the shipment, used to identify each shipment within a sales order. By default, this value starts at `1` for the first shipment (for each order) and automatically increments for each new shipment.

#### Tracking Number

An optional field used to store tracking number information for the shipment.

#### Invoice Number

An optional field used to store an invoice reference for the shipment.

#### Link

An optional URL field which can be used to provide a link to an external URL.

All these fields can be edited by the user:

{% with id="edit-shipment", url="order/edit_shipment.png", description="Edit shipment" %}
{% include "img.html" %}
{% endwith %}
