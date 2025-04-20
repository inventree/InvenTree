---
title: Suppliers
---


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

#### Disable Supplier Part

Supplier parts can be individually disabled - for example, if a supplier part is no longer available for purchase. By disabling the part in the InvenTree system, it will no longer be available for selection in new purchase orders. However, any existing purchase orders which reference the supplier part will remain intact.

The "active" status of a supplier part is clearly visible within the user interface:

{% with id="supplier_part_disable", url="order/disable_supplier_part.png", description="Disable Supplier Part" %}
{% include "img.html" %}
{% endwith %}

To change the "active" status of a supplier part, simply edit the supplier part details and set the `active` attribute:

{% with id="supplier_part_disable_edit", url="order/disable_supplier_part_edit.png", description="Disable Supplier Part" %}
{% include "img.html" %}
{% endwith %}

It is recommended to disable a supplier part rather than deleting it, as this will preserve the integrity of historical data.

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
