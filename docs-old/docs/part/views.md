---
title: Part Views
---

## Part Views

The main part view is divided into 4 different panels:

1. Categories
2. Details
3. Tabs
4. Content of each tab

{% with id="part_view_intro", url="part/part_view_intro.png", description="Part View Introduction" %}
{% include 'img.html' %}
{% endwith %}
<p></p>

## Categories

The categories of each part is displayed on the top navigation bar as show in the above screenshot.
[Click here](./part.md#part-category) for more information about categories.

## Part Details

Details provides information about the particular part. Parts details can be displayed in the header panel clicking on "Show Part Details" toggle button.

{% with id="part_overview", url="part/part_overview.png", description="Part details" %}
{% include 'img.html' %}
{% endwith %}
<p></p>

A Part is defined in the system by the following parameters:

**Internal Part Number (IPN)** - A special code which can be used to link a part to a numbering system. The IPN field is not required, but may be useful where a part numbering system has been defined.

**Name** - The Part name is a simple (unique) text label

**Description** - Longer form text field describing the Part

**Revision** - An optional revision code denoting the particular version for the part. Used when there are multiple revisions of the same master part object.

**Keywords** - Optional few words to describe the part and make the part search more efficient.

**External Link** - An external URL field is provided to link to an external page. This could be useful the part has extra documentation located on an external server.

**Creation Date** - Indicates when the part was created and by which user (label on right-hand side)

**Units** - Units of measure (UoM) for this Part. The default is 'pcs'

## Part Tabs

The Part view page organizes part data into sections, displayed as tabs. Each tab has its own function, which is described in this section.

### Parameters

Parts can have multiple defined parameters.

[Read about Part parameters](./parameter.md)

### Variants

If a part is a *Template Part* then the *Variants* tab will be visible.

[Read about Part templates](./template.md)

### Stock

The *Stock* tab shows all the stock items for the selected *Part*. The user can quickly determine how many parts are in stock, where they are located, and the status of each *Stock Item*.

{% with id="part_stock", url="part/part_stock.png", description="Part Stock" %}
{% include 'img.html' %}
{% endwith %}

#### Functions

The following functions are available from the *Part Stock* view.

##### Export

Exports the stocktake data for the selected Part. Launches a dialog to select export options, and then downloads a file containing data for all stock items for this Part.

##### New Stock Item

Launches a dialog to create a new *Stock Item* for the selected *Part*.

##### Stock Actions

If stock items are selected in the table, stock actions are enabled via the drop-down menu.

### Allocations

The *Allocated* tab displays how many units of this part have been allocated to pending build orders and/or sales orders. This tab is only visible if the Part is a *component* (meaning it can be used to make assemblies), or it is *salable* (meaning it can be sold to customers).

### Bill of Materials

The *BOM* tab displays the [Bill of Materials](../build/bom.md) - a list of sub-components used to build an assembly. Each row in the BOM specifies a quantity of another Part which is required to build the assembly. This tab is only visible if the Part is an *assembly* (meaning it can be build from other parts).

### Build Orders

The *Build Orders* tab shows a list of the builds for this part. It provides a view for important build information like quantity, status, creation and completion dates.

### Used In

The *Used In* tab displays a list of other parts that this part is used to make. This tab is only visible if the Part is a *component*.

### Suppliers

The *Suppliers* tab displays all the *Part Suppliers* and *Part Manufacturers* for the selected *Part*.

This tab is only visible if the *Part* is designated as *Purchaseable*.

{% with id="part_manufacturers_suppliers", url="part/part_manufacturers_suppliers.png", description="Part Suppliers and Manufacturers" %}
{% include 'img.html' %}
{% endwith %}

### Purchase Orders

The *Part Purchase Orders* tab lists all the Purchase Orders against the selected part.

This tab is only displayed if the part is marked as *Purchaseable*.

### Sales Orders

The *Sales Orders* tab shows a list of the sales orders for this part. It provides a view for important sales order information like customer, status, creation and shipment dates.

### Scheduling

The *Scheduling* tab provides an overview of the *predicted* future availability of a particular part. Refer to the [scheduling documentation](./scheduling.md) for further information.

### Stocktake

The *Stocktake* tab provide historical stock level information, based on user-provided stocktake data. Refer to the [stocktake documentation](./stocktake.md) for further information.

### Tests

If a part is marked as *trackable*, the user can define tests which must be performed on any stock items which are instances of this part. [Read more about testing](./test.md).

### Related Parts

Related Part denotes a relationship between two parts, when users want to show their usage is "related" to another part or simply emphasize a link between two parts.

Related parts can be added and are shown under a table of the same name in the "Part" view:

{% with id="related_parts", url="part/part_related.png", description="Related Parts Example View" %}
{% include 'img.html' %}
{% endwith %}

This feature can be enabled or disabled in the global part settings:

{% with id="related_parts_setting", url="part/part_related_setting.png", description="Related Parts Example View" %}
{% include 'img.html' %}
{% endwith %}

### Attachments

The *Part Attachments* tab displays file attachments associated with the selected *Part*. Multiple file attachments (such as datasheets) can be uploaded for each *Part*.

### Notes

A part may have notes attached, which support markdown formatting.
