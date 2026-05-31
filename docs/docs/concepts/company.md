---
title: Companies
---


## Companies

External companies are represented by the *Company* database model. Each company may be classified into the following categories:

- [Customer](../sales/customer.md)
- [Supplier](../purchasing/supplier.md)
- [Manufacturer](../purchasing/manufacturer.md)

!!! tip "Multi Purpose"
    A company may be allocated to multiple categories, for example, a company may be both a supplier and a customer.

### Edit Company

To edit a company, click on the {{ icon("edit", color="blue", title="Edit Company") }} icon in the actions menu. Edit the company information, and then click on <span class='badge inventree confirm'>Submit</span>.

!!! warning "Permission Required"
    The edit button will not be available to users who do not have the required permissions to edit the company

### Disable Company

Rather than deleting a company, it is possible to disable it. This will prevent the company from being used in new orders, but will not remove it from the database. Additionally, any existing orders associated with the company (and other linked items such as supplier parts, for a supplier) will remain intact. Unless the company is re-enabled, it will not be available for selection in new orders.

It is recommended to disable a company rather than deleting it, as this will preserve the integrity of historical data.

To disable a company, simply edit the company details and set the `active` attribute to `False`:

{{ image("purchasing/company_disable.png", "Disable Company") }}

To re-enable a company, simply follow the same process and set the `active` attribute to `True`.

### Delete Company

To delete a company, click on the {{ icon("trash", color="red", title="Delete") }} icon under the actions menu. Confirm the deletion using the checkbox then click on <span class="badge inventree confirm">Submit</span>

!!! warning "Permission Required"
    The edit button will not be available to users who do not have the required permissions to delete the company

!!! danger "Take Care"
    Deleting a company instance will also remove any orders or supplied parts associated with that company!

### Contacts

Each company can have multiple assigned *Contacts*. A contact identifies an individual who is associated with the company, including information such as name, email address, phone number, etc.

The list of contacts associated with a particular company is available in the <span class='badge inventree nav main'>{{ icon("users") }} Contacts</span> navigation tab:

{{ image("purchasing/contact_list.png", "Company Contacts") }}

A *contact* can be assigned to orders, (such as [purchase orders](../purchasing/purchase_order.md) or [sales orders](../sales/sales_order.md)).

### Addresses

A company can have multiple registered addresses for use with all types of orders.
An address is broken down to internationally recognized elements that are designed to allow for formatting an address according to user needs.
Addresses are composed differently across the world, and InvenTree reflects this by splitting addresses into components:

| Field | Description |
| ----- | ----------- |
| Title | A descriptive name for the address (e.g. "Head Office", "Warehouse", etc)
| Line 1 | Main street address |
| Line 2 | Extra street address line |
| Postal Code | Also known as ZIP code, this is normally a number 3-5 digits in length |
| City | The city/region tied to the postal code |
| Province | The larger region the address is located in. Also known as State in some countries |
| Country | Country the address is located in |

Here are a couple of examples of how the address structure differs by country, but these components can construct a correctly formatted address for any given country.

**UK Address Format:**

```
Recipient
Line 1
Line 2
City
Postal Code
Country
```

**US Address Format:**
```
Recipient
Line 1
Line 2
City State Postal Code
Country
```

#### Primary Address

Each company can have exactly one (1) primary address.
This address is the default shown on the company profile, and the one that is automatically suggested when creating an order.
Marking a new address as primary will remove the mark from the old primary address.

!!! info "Effective order address"
    When an order ([Sales Order](../sales/sales_order.md)) has no explicit address assigned, InvenTree uses the customer's primary address as the effective delivery address. This fallback ensures that reports and shipping labels always have an address to render, even if none was explicitly chosen on the order.

#### Managing Addresses

Addresses can be accessed by the <span class='badge inventree nav main'>{{ icon("map-2") }} Addresses</span> navigation tab, from the company detail page.

Here, the addresses associated with the company are listed, and can be added, edited, or deleted.

{{ image("concepts/edit_address.png", "Edit Address") }}

### Internal Addresses

In addition to addresses linked to external companies, InvenTree supports **internal addresses** — addresses that belong to your own organization rather than to any external company.

Internal addresses are used when the delivery destination is one of your own sites rather than a customer or supplier location. Orders that use internal addresses include:

| Order Type | Address Meaning |
| --- | --- |
| [Purchase Order](../purchasing/purchase_order.md) | Optional delivery destination for incoming goods |
| [Return Order](../sales/return_order.md) | Optional location to which returned items are sent |
| [Transfer Order](../stock/transfer_order.md) | Optional destination for an internal stock transfer |

!!! info "Sales Orders use external addresses"
    [Sales Orders](../sales/sales_order.md) are addressed to the *customer*, so they use addresses linked to the customer company, not internal addresses.

#### Managing Internal Addresses

Internal addresses are managed from the **Admin Center**, under the *Internal Addresses* panel. Only staff users can create, edit, or delete internal addresses.

Each internal address uses the same fields as a company address (Title, Line 1, Line 2, Postal Code, City, Province, Country).

#### Primary Internal Address

One internal address can be marked as the **primary** address. This address is the default suggestion when assigning a delivery address to a new order. Marking a different address as primary will automatically remove the mark from the previous primary address.

!!! info "Effective order address"
    When a Purchase Order, Return Order, or Transfer Order has no explicit address assigned, InvenTree falls back to the primary internal address as the effective delivery address. This ensures that reports and shipping documents always have an address to render. If no internal address exists at all, the effective address is blank.
