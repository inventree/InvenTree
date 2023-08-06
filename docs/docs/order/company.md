---
title: External Companies
---

## Companies

External companies are represented by the *Company* database model. Each company may be classified into the following categories:

- [Customer](#customers)
- [Supplier](#suppliers)
- [Manufacturer](#manufacturers)

!!! tip Multi Purpose
    A company may be allocated to multiple categories

### Edit Company

To edit a company, click on the <span class='fas fa-edit'>Edit Company</span> icon in the actions menu. Edit the company information, and then click on <span class='badge inventree confirm'>Submit</span>.

!!! warning "Permission Required"
    The edit button will not be available to users who do not have the required permissions to edit the company

### Delete Company

To delete a company, click on the <span class='fas fa-trash-alt'></span> icon under the actions menu. Confirm the deletion using the checkbox then click on <span class="badge inventree confirm">Submit</span>

!!! warning "Permission Required"
    The edit button will not be available to users who do not have the required permissions to delete the company

!!! danger "Take Care"
    Deleting a company instance will also remove any orders or supplied parts associated with that company!

### Contacts

Each company can have multiple assigned *Contacts*. A contact identifies an individual who is associated with the company, including information such as name, email address, phone number, etc.

The list of contacts associated with a particular company is available in the <span class='badge inventree nav main'><span class='fas fa-users'></span> Contacts</span> navigation tab:

{% with id="contact_list", url="order/contact_list.png", description="Contact List" %}
{% include "img.html" %}
{% endwith %}


A *contact* can be assigned to orders, (such as [purchase orders](./purchase_order.md) or [sales orders](./sales_order.md)).

### Addresses

A company can have multiple registered addresses for use with all types of orders.
An address is broken down to internationally recognised elements that are designed to allow for formatting an address according to user needs.
Addresses are composed differently across the world, and Inventree reflects this by splitting addresses into components:
- Line 1: Main street address
- Line 2: Extra street address line
- Postal Code: Also known as ZIP code, this is normally a number 3-5 digits in length
- City: The city/region tied to the postal code
- Province: The larger region the address is located in. Also known as State in the US
- Country: Country the address is located in, written in CAPS

Here are a couple of examples of how the address structure differs by country, but these components can construct a correctly formatted address for any given country.

UK address format:
Recipient
Line 1
Line 2
City
Postal Code
Country

US Address Format:
Recipient
Line 1
Line 2
City State Postal Code
Country


Addresses can be accessed by the <span class='badge inventree nav main'><span class='fas fa-map-marked'></span> Addresses</span> navigation tab.

#### Primary Address

Each company can have exactly one (1) primary address.
This address is the default shown on the company profile, and the one that is automatically suggested when creating an order.
Marking a new address as primary will remove the mark from the old primary address.

## Customers

A *customer* is an external client to whom parts or services are sold.

To access the customer page, click on the <span class="badge inventree nav main"><span class='fas fa-truck'></span> Sell</span> navigation tab and click on <span class="badge inventree nav main"><span class='fas fa-user-tie'></span> Customers</span> option in the dropdown list.

!!! warning
	**Viewing**, **adding**, **editing** and **deleting** customers require the corresponding [Sales Orders user permissions](../settings/permissions.md)

### Add Customer

Once the customer page is loaded, click on the <span class="badge inventree add"><span class='fas fa-plus-circle'></span> New Customer</span> button: the "Create new Customer" form opens. Fill-in the manufacturer information (`Company name` and `Company description` are required) then click on <span class="badge inventree confirm">Submit</span>

## Manufacturers

A manufacturer is an external **producer** of parts and raw materials.

!!! info
	**Viewing**, **adding**, **editing** and **deleting** manufacturers require the corresponding [Purchase Orders user permissions](../settings/permissions.md)

To access the list of manufacturers , click on the <span class="badge inventree nav main"><span class='fas fa-shopping-cart'></span> Buy</span> navigation tab and click on <span class="badge inventree nav main"><span class='fas fa-industry'></span> Manufacturers</span> option in the dropdown list.

{% with id="manufacturer_list", url="order/manufacturer_list.png", description="Manufacturer List" %}
{% include "img.html" %}
{% endwith %}

### Add Manufacturer

Once the manufacturer page is loaded, click on the <span class="badge inventree add"><span class='fas fa-plus-circle'></span> New Manufacturer</span> button: the "Create new Manufacturer" form opens. Fill-in the manufacturer information (`Company name` and `Company description` are required) then click on <span class="badge inventree confirm">Submit</span>

!!! info "Manufacturer vs Supplier"
	In the case the manufacturer sells directly to customers, you may want to enable the checkbox `is supplier` before submitting the form (you can also enable it later on). Purchase orders rely exclusively on [supplier parts](#supplier-parts), therefore the manufacturer will need to be set as a supplier too.


### Manufacturer Parts

Manufacturer parts are linked to a manufacturer and defined as manufacturable items.

!!! warning
	**Viewing**, **adding**, **editing** and **deleting** manufacturer parts require the corresponding [Purchase Orders user permissions](../settings/permissions.md)

#### Add Manufacturer Part

To create a manufacturer part, you have the following options:

* either navigate to a Part detail page then click on the <span class="badge inventree nav side"><span class='fas fa-building'></span> Suppliers</span> tab
* or navigate to a Manufacturer detail page then click on the <span class="badge inventree nav side"><span class='fas fa-industry'></span> Manufactured Parts</span> tab.

Whichever you pick, click on the <span class="badge inventree add"><span class='fas fa-plus-circle'></span> New Manufacturer Part</span> button to load the "Create New Manufacturer Part" form. Fill out the form with the manufacturer part information then click on <span class="badge inventree confirm">Submit</span>

#### Edit Manufacturer Part

To edit a manufacturer part, first access the manufacturer part detail page with one of the following options:

* either navigate to a Part detail page, click on the <span class="badge inventree nav side"><span class='fas fa-building'></span> Suppliers</span> tab then, in the <span class="badge inventree nav main">Part Manufacturers</span> table, click on the _MPN_ link
* or navigate to a Manufacturer detail page, click on the <span class="badge inventree nav side"><span class='fas fa-industry'></span> Manufactured Parts</span> tab then click on the _MPN_ link.

After the manufacturer part details are loaded, click on the <span class='fas fa-edit'></span> icon next to the manufacturer part image. Edit the manufacturer part information then click on <span class="badge inventree confirm">Submit</span>

#### Delete Manufacturer Part

To delete a manufacturer part, first access the manufacturer part detail page like in the [Edit Manufacturer Part](#edit-manufacturer-part) section.

After the manufacturer part details are loaded, click on the <span class='fas fa-trash-alt'></span> icon next to the manufacturer part image. Review the the information for the manufacturer part to be deleted, confirm the deletion using the checkbox then click on <span class="badge inventree confirm">Submit</span>

## Suppliers

A supplier is an external **vendor** of parts and raw materials.

To access the supplier page, click on the <span class="badge inventree nav main"><span class='fas fa-shopping-cart'></span> Buy</span> navigation tab and click on <span class="badge inventree nav main"><span class='fas fa-building'></span> Suppliers</span> option in the dropdown list.

{% with id="supplier_list", url="order/supplier_list.png", description="Supplier List" %}
{% include "img.html" %}
{% endwith %}

!!! info
	**Viewing**, **adding**, **editing** and **deleting** suppliers require the corresponding [Purchase Orders user permissions](../settings/permissions.md)

### Add Supplier

Once the supplier page is loaded, click on the <span class="badge inventree add"><span class='fas fa-plus-circle'></span> New Supplier</span> button: the "Create new Supplier" form opens. Fill-in the supplier information (`Company name` and `Company description` are required) then click on <span class="badge inventree confirm">Submit</span>

!!! info "Supplier vs Manufacturer"
	In the case the supplier is a manufacturer who sells directly to customers, you may want to enable the checkbox `is manufacturer` before submitting the form (you can also enable it later on).

### Supplier Parts

Supplier parts are linked to a supplier and defined as purchasable items.

!!! warning
	**Viewing**, **adding**, **editing** and **deleting** supplier parts require the corresponding [Purchase Orders user permissions](../settings/permissions.md)

#### Add Supplier Part

To create a supplier part, you have the following options:

1. navigate to a Part detail page then click on the <span class="badge inventree nav side"><span class='fas fa-building'></span> Suppliers</span> tab
0. navigate to a Supplier detail page then click on the <span class="badge inventree nav side"><span class='fas fa-building'></span> Supplied Parts</span> tab
0. navigate to a Manufacturer detail page then click on the <span class="badge inventree nav side"><span class='fas fa-building'></span> Supplied Parts</span> tab.

Whichever you pick, click on the <span class="badge inventree add"><span class='fas fa-plus-circle'></span> New Supplier Part</span> button to load the "Create new Supplier Part" form. Fill out the form with the supplier part information then click on <span class="badge inventree confirm">Submit</span>

#### Edit Supplier Part

To edit a supplier part, first access the supplier part detail page with one of the following options:

1. navigate to a Part detail page, click on the <span class="badge inventree nav side"><span class='fas fa-building'></span> Suppliers</span> tab then, in the <span class="badge inventree nav main">Part Suppliers</span> table, click on the corresponding _Supplier Part_ link
0. navigate to a Supplier detail page, click on the <span class="badge inventree nav side"><span class='fas fa-building'></span> Supplied Parts</span> tab then click on the corresponding _Supplier Part_ link
0. navigate to a Manufacturer detail page, click on the <span class="badge inventree nav side"><span class='fas fa-building'></span> Supplied Parts</span> tab then click on the corresponding _Supplier Part_ link.

After the supplier part details are loaded, click on the <span class='fas fa-edit'></span> icon next to the supplier part image. Edit the supplier part information then click on <span class="badge inventree confirm">Submit</span>

#### Delete Supplier Part

To delete a supplier part, first access the supplier part detail page like in the [Edit Supplier Part](#edit-supplier-part) section.

After the supplier part details are loaded, click on the <span class='fas fa-trash-alt'></span> icon next to the supplier part image. Review the the information for the supplier part to be deleted, confirm the deletion using the checkbox then click on <span class="badge inventree confirm">Submit</span>

#### Supplier Part Availability

InvenTree supports tracking 'availability' information for supplier parts. While this information can be updated manually, it is more useful when used in conjunction with the InvenTree plugin system.

A custom can periodically request availability information (via a supplier API), and update this availability information for each supplier part.

If provided, availability information is displayed on the Supplier Part detail page.

{% with id="supplier_part_availability", url="order/supplier_part_availability.png", maxheight="240px", description="Supplier part availability" %}
{% include "img.html" %}
{% endwith %}

Availability information can be manually updated via the user interface:

{% with id="update_availability", url="order/update_availability.png", maxheight="240px", description="Update availability" %}
{% include "img.html" %}
{% endwith %}
