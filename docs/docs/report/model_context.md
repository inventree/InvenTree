---
title: Model Context
---

## Model Context Variables

Each [report context](./context_variables.md) exposes one or more underlying model instances to the template (e.g. `order`, `part`, `item`). In addition to the explicit context variables documented on that page, templates can access any field or property of these model instances directly.

This page documents, for each reportable model type, the available:

- **Fields**: Database fields defined on the model (including those inherited from mixins / abstract base classes)
- **Properties**: `@property` attributes which have been explicitly marked with the `@report_attribute` decorator, making them discoverable here

Not every attribute or method available on a model instance is listed here - only database fields, and properties explicitly marked for discovery. For a full list of attributes and methods, refer to the source code for the particular model type.

### Company

{{ model_fields("company") }}
{{ model_properties("company") }}

### Build Order

{{ model_fields("build") }}
{{ model_properties("build") }}

### Build Line

{{ model_fields("buildline") }}
{{ model_properties("buildline") }}

### Sales Order

{{ model_fields("salesorder") }}
{{ model_properties("salesorder") }}

### Sales Order Shipment

{{ model_fields("salesordershipment") }}
{{ model_properties("salesordershipment") }}

### Return Order

{{ model_fields("returnorder") }}
{{ model_properties("returnorder") }}

### Purchase Order

{{ model_fields("purchaseorder") }}
{{ model_properties("purchaseorder") }}

### Transfer Order

{{ model_fields("transferorder") }}
{{ model_properties("transferorder") }}

### Stock Item

{{ model_fields("stockitem") }}
{{ model_properties("stockitem") }}

### Stock Location

{{ model_fields("stocklocation") }}
{{ model_properties("stocklocation") }}

### Part

{{ model_fields("part") }}
{{ model_properties("part") }}

The following `Part` methods accept optional arguments, and so are not included in the automatically-generated properties table above:

| Variable | Description |
|----------|-------------|
| required_build_order_quantity | The amount required for build orders |
| build_order_allocations | Query set with all build order allocations for that part |
| build_order_allocation_count | The amount allocated for build orders |
| required_sales_order_quantity | The amount required for sales orders |
| sales_order_allocation_count | The amount allocated for sales orders |
| required_order_quantity | The total amount required for build orders and sales orders |
| allocation_count | The total amount allocated for build orders and sales orders |

## Related Model Types

Some *related* model types are not themselves directly reportable, but are referenced by a field or `@report_attribute` property on a reportable model (e.g. `PartCategory` via `part.category`, `SupplierPart` via `part.default_supplier` or `stockitem.supplier_part`).

These are discovered automatically - there is no manually-maintained list of related models here. If a reportable model gains a new field or `@report_attribute` property pointing at another model, that model will automatically appear in this section.

{{ related_model_context() }}
