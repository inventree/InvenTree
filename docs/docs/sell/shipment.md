---
title: Shipments
---

## Shipments

Shipments are used to track sales items when they are shipped to customers. Multiple shipments can be created against a [Sales Order](./so.md), allowing line items to be sent to customers in multiple deliveries.

On the main Sales Order detail page, the order shipments are split into two categories, *Pending Shipments* and *Completed Shipments*:

### Pending Shipments

The *Pending Shipments* panel displays the shipments which have not yet been sent to the customer.

- Each shipment displays the items which have been allocated to it
- Pending sales order items can be allocated to these shipments
- New shipments can be created if the order is still open

{% with id="pending-shipments", url="sell/pending_shipments.png", description="Pending shipments" %}
{% include "img.html" %}
{% endwith %}

#### Creating a new Shipment

To create a new shipment for a sales order, press the *New Shipment* button above the pending shipments table.

#### Completing a Shipment

To complete a shipment, press the *Complete Shipment* button associated with the particular shipment:

{% with id="complete-shipment", url="sell/complete_shipment.png", description="Complete shipment" %}
{% include "img.html" %}
{% endwith %}

Alternatively, pending shipments can be completed by selecting the *Complete Shipments* action from the sales order actions menu:

{% with id="complete-shipment-action", url="sell/complete_shipment_action.png", description="Complete shipment" %}
{% include "img.html" %}
{% endwith %}

### Completed Shipments

{% with id="completed-shipments", url="sell/completed_shipments.png", description="Completed shipments" %}
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

{% with id="edit-shipment", url="sell/edit_shipment.png", description="Edit shipment" %}
{% include "img.html" %}
{% endwith %}
