---
title: Manufacturers
---

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
    In the case the manufacturer sells directly to customers, you may want to enable the checkbox `is supplier` before submitting the form (you can also enable it later on). Purchase orders rely exclusively on [supplier parts](./supplier.md#supplier-parts), therefore the manufacturer will need to be set as a supplier too.


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
