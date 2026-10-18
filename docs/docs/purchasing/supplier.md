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

Supplier parts can have a pack size defined, using the *Pack Quantity* field. This value is defined when creating or editing a supplier part. If left blank, the pack size is 1 - each item purchased from the supplier is a single unit of the base part.

The pack quantity describes how much of the base part is contained in a single pack, as sold by the supplier. For example:

| Base Part | Base Part Units | Supplier Sells | Pack Quantity |
| --- | --- | --- | --- |
| Screw | *(none)* | Bag of 100 screws | `100` |
| Wire | metres | 100 foot reel | `100 ft` |
| Paint | litres | 250 millilitre tin | `250 ml` |

### Pack Quantity Units

If the base part has a [unit of measure](../part/index.md#units-of-measure), the pack quantity can be specified in any *compatible* unit. The value is automatically converted into the units of the base part - in the examples above, a `100 ft` reel is equivalent to 30.48 metres of wire, and a `250 ml` tin is equivalent to 0.25 litres of paint.

If no units are provided, the pack quantity is assumed to be in the same units as the base part. If the base part does not have a unit of measure, the pack quantity must be a plain number.

The pack quantity must be greater than zero. An incompatible unit (e.g. specifying `250 ml` for a part tracked in metres) will result in an error.

!!! info "Read More"
    Read more about [supplier part units](../part/index.md#supplier-part-units) and [physical units of measure](../concepts/units.md)

### Quantities are Counted in Packs

When dealing with a supplier part, quantities are counted in *packs*, and prices are specified *per pack*. This matches how the supplier sells the item, and applies to:

- [Supplier price breaks](#supplier-part-pricing) - the quantity is the number of packs, and the price is the cost of a single pack
- [Purchase order](./purchase_order.md) line items - the quantity is the number of packs ordered, and the purchase price is the cost of a single pack

InvenTree converts these values into the units of the base part where required:

- When a purchase order line item is received, the quantity added to stock is the number of packs multiplied by the pack quantity. The purchase price recorded against the new stock item is the pack price divided by the pack quantity, i.e. the price per unit of the base part.
- When calculating [part pricing](../part/pricing.md), supplier price breaks and purchase history are divided by the pack quantity, so that prices from supplier parts with different pack sizes can be compared directly.

### Adding Stock Manually

When adding stock manually against a supplier part which has a pack size other than 1, the quantity can be specified in packs or in base part units. This is to allow the addition of items in opened packages.

Set the flag "Use pack size" (`use_pack_size` in the API) to True in order to add parts in packs. In this case, both the quantity *and* the purchase price are treated as values per pack, and converted to base part units when the stock item is created. If the flag is False, the quantity and purchase price are used as provided.

!!! warning "API Usage"
    When creating a stock item via the API against a supplier part with a pack size other than 1, the `use_pack_size` flag must be provided - otherwise the request will be rejected.

### Example

Consider a *Blue Paint* part, which is tracked in `litres`. A supplier sells this paint in 250ml tins, so the supplier part has a pack quantity of `250 ml`.

The supplier offers a price of €8.50 per tin, when buying 10 or more tins. This is entered as a supplier price break with a quantity of `10` and a price of `€8.50`.

- The price per litre of paint is €8.50 / 0.25 = €34.00, which is displayed in the *Unit Price* column of the supplier pricing table, and used for [part pricing](../part/pricing.md#supplier-pricing) calculations.
- A purchase order line for this supplier part, with a quantity of `12` and a purchase price of `€8.50`, represents twelve tins at €8.50 each.
- When the line item is received, 3 litres of paint are added to stock (12 x 0.25), with a purchase price of €34.00 per litre.

!!! tip "Bundled Items"
    A pack size only ever represents multiple units of the *same* part. If a supplier instead sells a kit or assortment of *different* components as a single purchasable item, refer to the [bundled items](./purchase_order.md#bundled-items) documentation instead.

## Supplier Part Pricing

Pricing information for a supplier part is specified as a set of *price breaks*, which are displayed on the <span class="badge inventree nav side">{{ icon("currency-dollar") }} Supplier Pricing</span> tab of the supplier part detail page:

{{ image("purchasing/supplier_price_breaks.png", "Supplier price breaks") }}

Each price break defines the price of the supplier part when purchasing at least the specified quantity. The table displays:

| Column | Description |
| --- | --- |
| Quantity | The minimum number of packs which must be purchased for this price break to apply |
| Supplier Price | The price of a single pack, as entered |
| Unit Price | The price per unit of the base part (the supplier price divided by the [pack quantity](#supplier-part-pack-size)) |

### Add Price Break

To add a new price break, click on the <span class="badge inventree add">{{ icon("plus-circle") }}</span> button above the pricing table. If the supplier part has a pack size other than 1, the form displays a reminder of the pack size, and how the quantity and price values are interpreted:

{{ image("purchasing/supplier_price_break_form.png", "Add supplier price break") }}

!!! warning "Price Per Pack"
    The price entered for a supplier price break is the price of a *single pack* - not the total price for the specified quantity, and not the price for a single unit of the base part.

Supplier price breaks are used to:

- Suggest a purchase price when adding a supplier part to a [purchase order](./purchase_order.md)
- Calculate [supplier pricing](../part/pricing.md#supplier-pricing) for the base part
