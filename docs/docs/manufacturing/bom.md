---
title: Bill of Materials
---

## Bill of Materials

A Bill of Materials (BOM) defines the list of component parts required to make an assembly, [create build orders](./build.md) and allocate inventory.

A part which can be built from other sub components is called an *Assembly*.

{{ image("build/bom_flat.png", "Flat BOM Table") }}

## BOM Line Items

A BOM for a particular assembly is comprised of a number (zero or more) of BOM "Line Items", each of which has the following properties:

| Property | Description |
| --- | --- |
| Part | A reference to another *Part* object which is required to build this assembly |
| Reference | Optional reference field to describe the BOM Line Item, e.g. part designator |
| Raw Amount | The raw quantity of the part required for the assembly, which can be expressed in different units of measure, e.g. `2 cm`, `1/2 inch`, `200 kg`. |
| Quantity | The quantity of *Part* required for the assembly - this value is automatically calculated from the "raw amount" field, taking into account the units of measure associated with the underlying part. |
| Attrition | Estimated attrition losses for a production run. Expressed as a percentage of the base quantity (e.g. 2%) |
| Setup Quantity | An additional quantity of the part which is required to account for fixed setup losses during the production process. This is added to the base quantity of the BOM line item |
| Rounding Multiple | A value which indicates that the required quantity should be rounded up to the nearest multiple of this value. |
| Consumable | A boolean field which indicates whether this BOM Line Item is *consumable* |
| Inherited | A boolean field which indicates whether this BOM Line Item will be "inherited" by BOMs for parts which are a variant (or sub-variant) of the part for which this BOM is defined. |
| Optional | A boolean field which indicates if this BOM Line Item is "optional" |
| Note | Optional note field for additional information

### Units of Measure

The `raw_amount` field allows the user to specify the required quantity of a particular part in different [units of measure](../concepts/units.md). The units of measure are determined by the underlying part definition. For example, if the part is defined with a default unit of measure of "kg", the user can specify the required quantity in "g", "mg", "lb", etc.

The `raw_amount` field is stored as a string, and the `quantity` field is automatically calculated from the `raw_amount` field, taking into account the units of measure associated with the underlying part. This allows for greater flexibility in specifying the required quantity of a particular part, while still maintaining accurate tracking of inventory and production requirements.

If the underlying part does not have a defined unit of measure, the `raw_amount` field is not allowed to have any units of measure specified, and the `quantity` field is simply a numeric representation of the `raw_amount` field.

### Fractional Representation

The `raw_amount` field also allows for fractional representation of the required quantity. For example, if the required quantity is 0.5 kg, the user can specify this as `500 g`, `0.5 kg`, `1/2 kg`, etc. The `quantity` field will be automatically calculated as 0.5 kg, regardless of the specific representation used in the `raw_amount` field.

### Consumable BOM Line Items

If a BOM line item is marked as *consumable*, this means that while the part and quantity information is tracked in the BOM, this line item does not get allocated to a [Build Order](./build.md). This may be useful for certain items that the user does not wish to track through the build process, as they may be low value, in abundant stock, or otherwise complicated to track.

In the example below, see that the *Wood Screw* line item is marked as consumable. It is clear that 12 screws are required for each assembled *Table*, but the screws will not be tracked through the build process, as this line item is marked as *consumable*

{{ image("build/bom_consumable_item.png", "Consumable BOM Item") }}

Further, in the [Build Order](./build.md) stock allocation table, we see that this line item cannot be allocated, as it is *consumable*.

### Optional BOM Line Items

If a BOM line item is marked as *optional*, this means that the part and quantity information is tracked in the BOM, but this line item is not required to be allocated to a [Build Order](./build.md). This may be useful for certain items which are not strictly required for the build process to be completed.

When completing a Build Order, the user can choose whether to include optional items in the build process or not. If optional items are included, they will be allocated to the Build Order as normal. If optional items are excluded, they will not be allocated to the Build Order, and the build process can be completed without them.

### Substitute BOM Line Items

Where alternative parts can be used when building an assembly, these parts are assigned as *Substitute* parts in the Bill of Materials. A particular line item may have multiple substitute parts assigned to it. When allocating stock to a [Build Order](./build.md), stock items associated with any of the substitute parts may be allocated against the particular line item.

!!! tip "Available Quantity"
    When calculating the *available quantity* of a particular line item in a BOM, stock quantities associated with substitute parts are included in the calculation.

### Inherited BOM Line Items

When using the InvenTree [template / variant](../part/template.md) feature, it may be useful to make use of the *inheritance* capability of BOM Line Items.

If a BOM Line Item is designed as *Inherited*, it will be automatically included in the BOM of any part which is a variant (or sub-variant) of the part for which the BOM Line Item is defined.

This is particularly useful if a template part is defined with the "common" BOM items which exist for all variants of that template.

Consider the example diagram below:

{{ image("build/inherited_bom.png", "Inherited BOM Line Items") }}

**Template Part A** has two BOM line items defined: *A1* and *A2*.

- *A1* is inherited by all variant parts underneath *Template Part A*
- *A2* is not inherited, and is only included in the BOM for *Template Part A*

**Variant B** has two line items:

- *A1* is inherited from parent part *A*
- *B1* is defined for part *B* (and is also defined as an inherited BOM Line Item)

**Variant C**

- *A1* inherited from *A*
- *C1* defined for *C*

**Variant D**

- *A1* inherited from *A*
- *B1* inherited from *B*
- *D1* defined for *D*

**Variant E**

- Well, you get the idea.

Note that inherited BOM Line Items only flow "downwards" in the variant inheritance chain. Parts which are higher up the variant chain cannot inherit BOM items from child parts.

!!! info "Editing Inherited Items"
    When editing an inherited BOM Line Item for a template part, the changes are automatically reflected in the BOM of any variant parts.

## BOM Editing

Bills of Material (BOMs) can be created manually, by adjusting individual line items, or by uploading (importing) an existing BOM file.

### Editing Mode

By default, the BOM is displayed in "view" mode. To edit the BOM, click on the {{ icon("edit", color="blue", title="Edit") }} icon at the top of the BOM panel. This will enable editing mode, which allows you to add, adjust or delete BOM line items.

!!! warning "Permissions"
    Only users with the appropriate permissions can edit BOMs. If you do not have permission to edit the BOM, the "Edit" icon will not be visible.

### Importing a BOM

BOM data can be imported from an existing file (such as CSV or Excel) from the *BOM* panel for a particular part/assembly. This process is a special case of the more general [data import process](../settings/import.md).

At the top of the *BOM* panel, click on the {{ icon("file-arrow-left", color="green", title="Import BOM Data") }} icon to open the import dialog.

### Add BOM Item

To manually add a BOM item, navigate to the part/assembly detail page then click on the *BOM* panel tab. On top of the *BOM* view, click on the {{ icon("edit", color="blue", title="Edit") }} icon then, after the page reloads, click on the {{ icon("plus-circle") }} icon.

The `Create BOM Item` form will be displayed:

{{ image("build/bom_add_item.png", "Create BOM Item Form") }}

Fill-out the required fields then click on <span class="badge inventree confirm">Submit</span> to add the BOM item to this part's BOM.

### Add Substitute for BOM Item

To manually add a substitute for a BOM item, click on the {{ icon("transfer") }} icon in the *Actions* columns.

The `Edit BOM Item Substitutes` form will be displayed:

{{ image("build/bom_substitute_item.png", "Edit BOM Item Substitutes") }}

Select a part in the list and click on "Add Substitute" button to confirm.

## Multi Level BOMs

Multi-level (hierarchical) BOMs are natively supported by InvenTree. A Bill of Materials (BOM) can contain sub-assemblies which themselves have a defined BOM. This can continue for an unlimited number of levels.

## BOM Validation

InvenTree maintains a "validated" flag for each assembled part. When set, this flag indicates that the production requirements for this part have been validated, and that the BOM has not been changed since the last validation.

A BOM "checksum" is stored against each part, which is a hash of the BOM line items associated with that part. This checksum is used to determine whether the BOM has changed since the last validation. Whenever a BOM line item is created, adjusted or deleted, any assemblies which are associated with that BOM must be validated to ensure that the BOM is still valid.

### BOM Checksum

The following BOM item fields are used when calculating the BOM checksum:

- *Assembly ID* - The unique identifier of the assembly associated with the BOM line item.
- *Component ID* - The unique identifier of the component part associated with the BOM line item.
- *Reference* - The reference field of the BOM line item.
- *Quantity* - The quantity of the component part required for the assembly.
- *Attrition* - The attrition percentage of the BOM line item.
- *Setup Quantity* - The setup quantity of the BOM line item.
- *Rounding Multiple* - The rounding multiple of the BOM line item.
- *Consumable* - Whether the BOM line item is consumable.
- *Inherited* - Whether the BOM line item is inherited.
- *Optional* - Whether the BOM line item is optional.
- *Allow Variants* - Whether the BOM line item allows variants.

If any of these fields are changed, the BOM checksum is recalculated, and any assemblies associated with the BOM are marked as "not validated".

The user must then manually revalidate the BOM for the assembly/

### BOM Validation Status

To view the "validation" status of an assembled part, navigate to the "Bill of Materials" tab of the part detail page. The validation status is displayed at the top of the BOM table:

{{ image("build/bom_validated.png", "BOM Validation Status") }}

If the BOM requires revalidation, the status will be displayed as "Not Validated". Additionally the "Validate BOM' button will be displayed at the top of the BOM table, allowing the user to revalidate the BOM.

{{ image("build/bom_invalid.png", "BOM Not Validated") }}

## BOM Comparison

It is possible to compare the BOM of one assembly with another assembly. This comparison can highlight different component parts, quantities and other properties of the BOM line items.

To compare the BOM of one assembly with another, navigate to the "Bill of Materials" tab of the part detail page, then click on the {{ icon("git-compare", color="blue", title="Compare BOM") }} icon at the top of the BOM table:

{{ image("build/bom_compare_icon.png", "BOM Compare") }}

This will open the BOM comparison view, which allows you to select a secondary assembly to compare with the primary assembly. The BOM line items of the two assemblies will be displayed side by side, with differences highlighted:

{{ image("build/bom_compare.png", "BOM Compare") }}

### Display Mode

When comparing BOMs from two different assemblies, the user can select from the following view modes:

| View Mode | Description |
| --- | --- |
| *Show all parts* | Display all BOM line items from both assemblies. Differences are highlighted. |
| *Show different parts* | Display only the BOM line items which are different between the two assemblies. |
| *Show common parts* | Display only the BOM line items which are common between the two assemblies. |

In each case, any differences between the BOM line items are highlighted in red.

## Replacing Components

When a component is used in the BOM for multiple assemblies, it can be time consuming to update the BOM for each assembly when a change is required. InvenTree provides a "Replace Component" function which streamlines the process of replacing a component part with another part across multiple BOMs.

To replace a component part within multiple assemblies:

- Navigate to the [Used In](../part/views.md#used-in) tab of the component part detail page
- Select the assemblies you wish to update by ticking the checkbox next to each assembly
- Click on the {{ icon("replace", color="blue", title="Replace Component") }} icon to open the "Replace Component" dialog

The following dialog will be displayed, which allows the user to select a new component part to replace the existing component part in the BOM of the selected assemblies:

{{ image("build/replace_component.png", "Replace Component") }}
