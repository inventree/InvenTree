---
title: Required Build Quantity
---

## Required Build Quantity

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

Attrition Value = Required Quantity * Attrition Percentage
                = 300 * 0.02
                = 6

Required Quantity = Required Quantity + Attrition Value
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
