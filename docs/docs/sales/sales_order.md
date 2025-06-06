---
title: Sales Orders
---

## Sales Orders

Sales orders allow tracking of which stock items are sold to customers, therefore converting stock items / inventory into externally sold items.

### View Sales Orders

To navigate to the Sales Order display, select *Sales* from the main navigation menu, and *Sales Orders* from the sidebar:

{{ image("order/so_display.png", "Sales Order display") }}

The following view modes are available:

#### Table View

*Table View* provides a list of Sales Orders, which can be filtered to display a subset of orders according to user supplied parameters.

{{ image("order/so_list.png", "Sales Order list") }}

#### Calendar View

*Calendar View* shows a calendar display with outstanding sales orders.

{{ image("order/so_calendar.png", "Sales Order calendar") }}

### Sales Order Status Codes

Each Sales Order has a specific status code, which represents the state of the order:

| Status | Description |
| --- | --- |
| Pending | The sales order has been created, but has not been finalized or submitted |
| In Progress | The sales order has been issued, and is in progress |
| On Hold | The sales order has been placed on hold, but is still active |
| Shipped | The sales order has been shipped, but is not yet complete |
| Complete | The sales order is fully completed, and is now closed |
| Cancelled | The sales order was cancelled, and is now closed |
| Lost | The sales order was lost, and is now closed |
| Returned | The sales order was returned, and is now closed |

**Source Code**

Refer to the source code for the Sales Order status codes:

::: order.status_codes.SalesOrderStatus
    options:
        show_bases: False
        show_root_heading: False
        show_root_toc_entry: False
        show_source: True
        members: []

Sales Order Status supports [custom states](../concepts/custom_states.md).

### Sales Order Currency

The currency code can be specified for an individual sales order. If not specified, the default currency specified against the [customer](./customer.md) will be used.

## Create a Sales Order

Once the sales order page is loaded, click on <span class="badge inventree add">{{ icon("plus-circle") }} New Sales Order</span> which opens the "Create Sales Order" form.

A Sales Order is linked to a specific customer, select one in the list of existing customers.

!!! warning "Customers Only"
	Only companies with the "Customer" attribute enabled will be shown and can be selected

Fill out the rest of the form with the sales order information then click on <span class="badge inventree confirm">Submit</span> to create the order.

### Sales Order Reference

Each Sales Order is uniquely identified by its *Reference* field. Read more about [reference fields](../settings/reference.md).

### Add Line Items

On the sales order detail page, user can link parts to the sales order selecting the <span class="badge inventree nav side">{{ icon("list") }}</span> Line Items</span> tab then clicking on the <span class="badge inventree add">{{ icon("plus-circle") }} Add Line Item</span> button.

Once the "Add Line Item" form opens, select a part in the list.

!!! warning
    Only parts that have the "Salable" attribute enabled will be shown and can be selected

Fill out the rest of the form then click on <span class="badge inventree confirm">Submit</span>

## Shipments

After all line items were added to the sales order, user needs to create one or more [shipments](#sales-order-shipments) in order to allocate stock for those parts.

In order to create a new shipment:

1. Click on the <span class="badge inventree nav side">{{ icon("truck-loading") }} Pending Shipments</span> tab
2. Click on <span class="badge inventree add">{{ icon("plus-circle") }} New Shipment</span> button, fill out the form with the shipment number (tracking number can be added but is optional) then click on <span class="badge inventree confirm">Submit</span>

Repeat the two steps above to create more shipments.

### Allocate Stock Items

After shipments were created, user can either:

* Allocate stock items for that part to the sales order (click on {{ icon("arrow-right") }} button)
* Create a build order for that part to cover the quantity of the sales order (click on {{ icon("tools") }} button)

During the allocation process, user is required to select the desired shipment that will contain the stock items.

### Complete Shipment

To complete a shipment, click on the <span class="badge inventree nav side">{{ icon("truck-loading") }} Pending Shipments</span> tab then click on {{ icon("truck-delivery") }} button shown in the shipment table.

Fill out the "Complete Shipment" form then click on <span class="badge inventree confirm">Submit</span>.

To view all the completed shipment, click on the <span class="badge inventree nav side">{{ icon("truck-delivery") }} Completed Shipments</span> tab. In the completed shipments table, click on each shipment to view the shipment details.

## Complete Order

Once all items in the sales order have been shipped, click on <span class="badge inventree add">{{ icon("circle-check", color="green") }} Complete Order</span> to mark the sales order as shipped. Confirm then click on <span class="badge inventree confirm">Submit</span> to complete the order.

## Cancel Order

To cancel the order, click on the {{ icon("tools") }} menu button next to the <span class="badge inventree add">{{ icon("circle-check", color="green") }} Complete Order</span> button, then click on the "{{ icon("tools") }} Cancel Order" menu option. Confirm then click on the <span class="badge inventree confirm">Submit</span> to cancel the order.

## Order Scheduling

Sales orders can be scheduled for a future date, to allow for order scheduling.

### Start Date

The *Start Date* of the sales order is the date on which the order is scheduled to be issued, allowing work to begin on the order.

### Target Date

The *Target Date* of the sales order is the date on which the order is scheduled to be completed and shipped.

### Overdue Orders

If the *Target Date* of the sales order has passed, the order will be marked as *overdue*.

## Calendar view

Using the button to the top right of the list of Sales Orders, the view can be switched to a calendar view using the button {{ icon("calendar") }}. This view shows orders with a defined target date only.

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

{{ image("order/pending_shipments.png", "Pending shipments") }}

#### Creating a new Shipment

To create a new shipment for a sales order, press the *New Shipment* button above the pending shipments table.

#### Completing a Shipment

To complete a shipment, press the *Complete Shipment* button associated with the particular shipment:

{{ image("order/complete_shipment.png", "Complete shipment") }}

### Completed Shipments

{{ image("order/completed_shipments.png", "Completed shipments") }}

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

{{ image("order/edit_shipment.png", "Edit shipment") }}

## Sales Order Settings

The following [global settings](../settings/global.md) are available for sales orders:

| Name | Description | Default | Units |
| ---- | ----------- | ------- | ----- |
{{ globalsetting("SALESORDER_REFERENCE_PATTERN") }}
{{ globalsetting("SALESORDER_REQUIRE_RESPONSIBLE") }}
{{ globalsetting("SALESORDER_DEFAULT_SHIPMENT") }}
{{ globalsetting("SALESORDER_EDIT_COMPLETED_ORDERS") }}
{{ globalsetting("SALESORDER_SHIP_COMPLETE") }}
