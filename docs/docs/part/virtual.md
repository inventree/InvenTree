---
title: Virtual Parts
---

## Virtual Parts

A *Virtual* part can be used to represent non-physical items in the InvenTree system. Virtual parts cannot have stock items associated with them, as they not physically exist.

Virtual parts can be used to represent things such as:

- Software licenses
- Labor costs
- Process steps

Apart from the fact that virtual parts cannot have stock items, they behave in the same way as regular parts.

### Stock Items

Virtual parts cannot have stock items associated with them. User interface elements related to stock items are hidden when viewing a virtual part.

### Bills of Material

Virtual parts can be added as a subcomponent to the [Bills of Material](../manufacturing/bom.md) for an assembled part. This can be useful to represent labor costs, or other non-physical components which are required to build an assembly.

Even though the virtual parts are not allocated during the build process, they are still listed in the BOM and can be included in cost calculations.

### Build Orders

When creating a [Build Order](../manufacturing/build.md) for an assembly which includes virtual parts in its BOM, the virtual parts will be hidden from the list of required parts. This is because virtual parts do not need to be allocated during the build process.

The parts are still available in the BOM, and the cost of the virtual parts will be included in the total cost of the build.

### Sales Orders

Virtual parts can be added to [Sales Orders](../sales/sales_order.md) in the same way as regular parts. This can be useful to represent services, or other non-physical items which are being sold.

When a sales order is fulfilled, virtual parts will not be allocated from stock, but they will be included in the order and the total cost.

Virtual parts do not need to be allocated during the fulfillment process, as they do not physically exist.
