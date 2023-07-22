---
title: Physical Units
---

## Physical Units

Support for real-world "physical" units of measure is implemented using the [pint](https://pint.readthedocs.io/en/stable/) Python library. This library provides the following core functions:

- Ensures consistent use of real units for your inventory management
- Convert between compatible units of measure from suppliers
- Enforce use of compatible units when creating part parameters
- Enable custom units as required

## Unit Support

Physical units are supported by the following InvenTree subsystems:

### Part

The [unit of measure](../part/part.md#units-of-measure) field for the [Part](../part/part.md) model uses real-world units.

### Supplier Part

The [supplier part](../part/part/#supplier-parts) model uses real-world units to convert between supplier part quantities and internal stock quantities. Unit conversion rules ensure that only compatible unit types can be supplied

### Part Parameter

The [part parameter template](../part/parameter.md#parameter-templates) model can specify units of measure, and part parameters can be specified against these templates with compatible units

## Custom Units

Out of the box, the Pint library provides a wide range of units for use. However, it may not be sufficient for a given application. In such cases, custom units can be easily defined to meet custom requirements.

Custom units can be defined to provide a new physical quantity, link existing units together, or simply provide an alias for an existing unit.

!!! tip "More Info"
    For further information, refer to the [pint documentation](https://pint.readthedocs.io/en/stable/advanced/defining.html) regarding custom unit definition

### Create Custom Units

To view, edit and create custom units, locate the *Physical Units* tab in the [settings panel](../settings/global.md).
