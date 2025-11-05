---
title: Suppliers
---


## Suppliers

A supplier is a [company](../concepts/company.md) which acts as an external vendor of parts and raw materials.

To access the supplier page, click on the <span class="badge inventree nav main">{{ icon("shopping-cart") }} Buy</span> navigation tab and click on <span class="badge inventree nav main">{{ icon("building") }} Suppliers</span> option in the dropdown list.

{{ image("purchasing/supplier_list.png", "Supplier List") }}

!!! info
    **Viewing**, **adding**, **editing** and **deleting** suppliers require the corresponding [Purchase Orders user permissions](../settings/permissions.md)

### Add Supplier

Once the supplier page is loaded, click on the <span class="badge inventree add">{{ icon("plus-circle") }} New Supplier</span> button: the "Create new Supplier" form opens. Fill-in the supplier information (`Company name` and `Company description` are required) then click on <span class="badge inventree confirm">Submit</span>

!!! info "Supplier vs Manufacturer"
    In the case the supplier is a manufacturer who sells directly to customers, you may want to enable the checkbox `is manufacturer` before submitting the form (you can also enable it later on).

### Supplier Parts

Supplier parts are linked to a supplier and defined as purchasable items.

!!! warning
    **Viewing**, **adding**, **editing** and **deleting** supplier parts require the corresponding [Purchase Orders user permissions](../settings/permissions.md)

#### Add Supplier Part

To create a supplier part, you have the following options:

1. navigate to a Part detail page then click on the <span class="badge inventree nav side">{{ icon("building") }} Suppliers</span> tab
0. navigate to a Supplier detail page then click on the <span class="badge inventree nav side">{{ icon("building") }} Supplied Parts</span> tab
0. navigate to a Manufacturer detail page then click on the <span class="badge inventree nav side">{{ icon("building") }} Supplied Parts</span> tab.

Whichever you pick, click on the <span class="badge inventree add">{{ icon("plus-circle") }} New Supplier Part</span> button to load the "Create new Supplier Part" form. Fill out the form with the supplier part information then click on <span class="badge inventree confirm">Submit</span>

#### Edit Supplier Part

To edit a supplier part, first access the supplier part detail page with one of the following options:

1. navigate to a Part detail page, click on the <span class="badge inventree nav side">{{ icon("building") }} Suppliers</span> tab then, in the <span class="badge inventree nav main">Part Suppliers</span> table, click on the corresponding _Supplier Part_ link
0. navigate to a Supplier detail page, click on the <span class="badge inventree nav side">{{ icon("building") }} Supplied Parts</span> tab then click on the corresponding _Supplier Part_ link
0. navigate to a Manufacturer detail page, click on the <span class="badge inventree nav side">{{ icon("building") }} Supplied Parts</span> tab then click on the corresponding _Supplier Part_ link.

After the supplier part details are loaded, click on the {{ icon("edit", color="blue", title="Edit") }} icon next to the supplier part image. Edit the supplier part information then click on <span class="badge inventree confirm">Submit</span>

#### Disable Supplier Part

Supplier parts can be individually disabled - for example, if a supplier part is no longer available for purchase. By disabling the part in the InvenTree system, it will no longer be available for selection in new purchase orders. However, any existing purchase orders which reference the supplier part will remain intact.

The "active" status of a supplier part is clearly visible within the user interface:

{{ image("purchasing/disable_supplier_part.png", "Disable Supplier Part") }}

To change the "active" status of a supplier part, simply edit the supplier part details and set the `active` attribute:

{{ image("purchasing/disable_supplier_part_edit.png", "Disable Supplier Part Edit") }}

It is recommended to disable a supplier part rather than deleting it, as this will preserve the integrity of historical data.

#### Delete Supplier Part

To delete a supplier part, first access the supplier part detail page like in the [Edit Supplier Part](#edit-supplier-part) section.

After the supplier part details are loaded, click on the {{ icon("trash", color="red", title="Delete") }} icon next to the supplier part image. Review the the information for the supplier part to be deleted, confirm the deletion using the checkbox then click on <span class="badge inventree confirm">Submit</span>

#### Supplier Part Availability

InvenTree supports tracking 'availability' information for supplier parts. While this information can be updated manually, it is more useful when used in conjunction with the InvenTree plugin system.

A custom can periodically request availability information (via a supplier API), and update this availability information for each supplier part.

If provided, availability information is displayed on the Supplier Part detail page.

{{ image("purchasing/supplier_part_availability.png", "Supplier Part Availability") }}

Availability information can be manually updated via the user interface:

{{ image("purchasing/update_availability.png", "Update Availability") }}

## Supplier Part Pack Size

Supplier parts can have a pack size defined. This value is defined when creating or editing a part. By default, the pack size is 1.

When buying parts, they are bought in packs. This is taken into account in Purchase Orders: if a supplier part with a pack size of 5 is bought in a quantity of 4, 20 parts will be added to stock when the parts are received.

When adding stock manually, the supplier part can be added in packs or in individual parts. This is to allow the addition of items in opened packages. Set the flag "Use pack size" (`use_pack_size` in the API) to True in order to add parts in packs.
