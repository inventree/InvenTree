---
title: Physical Units
---

## Physical Units

Support for real-world "physical" units of measure is implemented using the [pint](https://pint.readthedocs.io/en/stable/) Python library. This library provides the following core functions:

- Ensures consistent use of real units for your inventory management
- Convert between compatible units of measure from suppliers
- Enforce use of compatible units when creating part parameters
- Enable custom units as required

### Unit Conversion

InvenTree uses the pint library to convert between compatible units of measure. For example, it is possible to convert between units of mass (e.g. grams, kilograms, pounds, etc) or units of length (e.g. millimeters, inches, etc). This is a powerful feature that ensures that units are used consistently throughout the application.

### Engineering Notation

We support the use of engineering notation for units, which allows for easy conversion between units of different orders of magnitude. For example, the following values would all be considered *valid*:

- `10k3` : `10,300`
- `10M3` : `10,000,000`
- `3n02` : `0.00000000302`

### Scientific Notation

Scientific notation is also supported, and can be used to represent very large or very small numbers. For example, the following values would all be considered *valid*:

- `1E-3` : `0.001`
- `1E3` : `1000`
- `-123.45E-3` : `-0.12345`

!!! tip "Case Sensitive"
    Support for scientific notation is case sensitive. For example, `1E3` is a valid value, but `1e3` is not.

### Feet and Inches

Shorthand notation is supported for feet and inches. For example, the following values would all be considered *valid*:

- `3'`: `3 feet`
- `6"` : `6 inches`

However, note that compound measurements (e.g. `3'6"`) are not supported.

### Case Sensitivity

The pint library is case sensitive, and units must be specified in the correct case. For example, `kg` is a valid unit, but `KG` is not. In particular, you need to pay close attention when using SI prefixes (e.g. `k` for kilo, `M` for mega, `n` for nano, etc).

## Unit Support

Physical units are supported by the following InvenTree subsystems:

### Part

The [unit of measure](../part/part.md#units-of-measure) field for the [Part](../part/part.md) model uses real-world units.

### Supplier Part

The [supplier part](../part/part.md/#supplier-parts) model uses real-world units to convert between supplier part quantities and internal stock quantities. Unit conversion rules ensure that only compatible unit types can be supplied

### Part Parameter

The [part parameter template](../part/parameter.md#parameter-templates) model can specify units of measure, and part parameters can be specified against these templates with compatible units

## Custom Units

Out of the box, the Pint library provides a wide range of units for use. However, it may not be sufficient for a given application. In such cases, custom units can be easily defined to meet custom requirements.

Custom units can be defined to provide a new physical quantity, link existing units together, or simply provide an alias for an existing unit.

!!! tip "More Info"
    For further information, refer to the [pint documentation](https://pint.readthedocs.io/en/stable/advanced/defining.html) regarding custom unit definition

### Create Custom Units

To view, edit and create custom units, locate the *Physical Units* tab in the [settings panel](../settings/global.md).
