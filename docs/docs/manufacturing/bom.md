---
title: Bill of Materials
---

## Bill of Materials

A Bill of Materials (BOM) defines the list of component parts required to make an assembly, [create builds](./build.md) and allocate inventory.

A part which can be built from other sub components is called an *Assembly*.

{{ image("build/bom_flat.png", "Flat BOM Table") }}

## BOM Line Items

A BOM for a particular assembly is comprised of a number (zero or more) of BOM "Line Items", each of which has the following properties:

| Property | Description |
| --- | --- |
| Part | A reference to another *Part* object which is required to build this assembly |
| Reference | Optional reference field to describe the BOM Line Item, e.g. part designator |
| Quantity | The quantity of *Part* required for the assembly |
| Attrition | Estimated attrition losses for a production run. Expressed as a percentage of the base quantity (e.g. 2%) |
| Setup Quantity | An additional quantity of the part which is required to account for fixed setup losses during the production process. This is added to the base quantity of the BOM line item |
| Rounding Multiple | A value which indicates that the required quantity should be rounded up to the nearest multiple of this value. |
| Consumable | A boolean field which indicates whether this BOM Line Item is *consumable* |
| Inherited | A boolean field which indicates whether this BOM Line Item will be "inherited" by BOMs for parts which are a variant (or sub-variant) of the part for which this BOM is defined. |
| Optional | A boolean field which indicates if this BOM Line Item is "optional" |
| Note | Optional note field for additional information

### Consumable BOM Line Items

If a BOM line item is marked as *consumable*, this means that while the part and quantity information is tracked in the BOM, this line item does not get allocated to a [Build Order](./build.md). This may be useful for certain items that the user does not wish to track through the build process, as they may be low value, in abundant stock, or otherwise complicated to track.

In the example below, see that the *Wood Screw* line item is marked as consumable. It is clear that 12 screws are required for each assembled *Table*, but the screws will not be tracked through the build process, as this line item is marked as *consumable*

{{ image("build/bom_consumable_item.png", "Consumable BOM Item") }}

Further, in the [Build Order](./build.md) stock allocation table, we see that this line item cannot be allocated, as it is *consumable*.

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

## BOM Creation

BOMs can be created manually, by adjusting individual line items, or by upload an existing BOM file.

### Add BOM Item

To manually add a BOM item, navigate to the part/assembly detail page then click on the "BOM" tab. On top of the tab view, click on the {{ icon("edit", color="blue", title="Edit") }} icon then, after the page reloads, click on the {{ icon("plus-circle") }} icon.

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

## Required Quantity Calculation

When a new [Build Order](./build.md) is created, the required production quantity of each component part is calculated based on the BOM line items defined for the assembly being built. To calculate the required production quantity of a component part, the following considerations are made:

### Base Quantity

The base quantity of a BOM line item is defined by the `Quantity` field of the BOM line item. This is the number of parts which are required to build one assembly. This value is multiplied by the number of assemblies which are being built to determine the total quantity of parts required.

```
Required Quantity = Base Quantity * Number of Assemblies
```

### Attrition

The `Attrition` field of a BOM line item is used to account for expected losses during the production process. This is expressed as a percentage of the `Base Quantity` (e.g. 2%).

If a non-zero attrition percentage is specified, it is applied to the calculated `Required Quantity` value.

```
Required Quantity = Required Quantity * (1 + Attrition Percentage)
```

!!! info "Optional"
    The attrition percentage is optional. If not specified, it defaults to 0%.

### Setup Quantity

The `Setup Quantity` field of a BOM line item is used to account for fixed losses during the production process. This is an additional quantity of the part which is required to ensure that the production run can be completed successfully. This value is added to the calculated `Required Quantity`.

```
Required Quantity = Required Quantity + Setup Quantity
```

!!! info "Optional"
    The setup quantity is optional. If not specified, it defaults to 0.

### Rounding Multiple

The `Rounding Multiple` field of a BOM line item is used to round the calculated `Required Quantity` value to the nearest multiple of the specified value. This is useful for ensuring that the required quantity is a whole number, or to meet specific packaging requirements.

```
Required Quantity = ceil(Required Quantity / Rounding Multiple) * Rounding Multiple
```

!!! info "Optional"
    The rounding multiple is optional. If not specified, no rounding is applied to the calculated production quantity.

### Example Calculation

Consider a BOM line item with the following properties:

- Base Quantity: 3
- Attrition: 2% (0.02)
- Setup Quantity: 10
- Rounding Multiple: 25

If we are building 100 assemblies, the required quantity would be calculated as follows:

```
Required Quantity = Base Quantity * Number of Assemblies
                  = 3 * 100
                  = 300

Overage Value = Required Quantity * Overage Percentage
              = 300 * 0.02
              = 6

Required Quantity = Required Quantity + Overage Value
                  = 300 + 6
                  = 306

Required Quantity = Required Quantity + Setup Quantity
                  = 306 + 10
                  = 316

Required Quantity = ceil(Required Quantity / Rounding Multiple) * Rounding Multiple
                  = ceil(316 / 25) * 25
                  = 13 * 25
                  = 325

```

So the final required production quantity of the component part would be `325`.

!!! info "Calculation"
    The required quantity calculation is performed automatically when a new [Build Order](./build.md) is created.
