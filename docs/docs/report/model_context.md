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

Some *related* model types are not themselves directly reportable, but are commonly accessed as nested attributes from a reportable model (e.g. `part.category`, `company.primary_address`, `stockitem.supplier_part`). These are documented by hand below, as they are not yet covered by the automatic discovery process.

### Part Category

`PartCategory` is not itself a reportable model, but is commonly accessed via `part.category`:

| Variable | Description |
|----------|-------------|
| name | Name of this category |
| parent | Parent category |
| default_location | Default [StockLocation](#stock-location) object for parts in this category or child categories |
| default_keywords | Default keywords for parts created in this category |

### Address

`Address` is commonly accessed via `company.primary_address`, or by iterating over a `Company`'s associated addresses:

| Variable | Description |
|----------|-------------|
| line1 | First line of the postal address |
| line2 | Second line of the postal address |
| postal_code | ZIP code of the city |
| postal_city | City name |
| country | Country name |

### Contact

| Variable | Description |
|----------|-------------|
| company | Company object where the contact belongs to |
| name | First and second name of the contact |
| phone | Phone number |
| email | Email address |
| role | Role of the contact |

### SupplierPart

`SupplierPart` is commonly accessed via `stockitem.supplier_part`, or `part.default_supplier`:

| Variable | Description |
|----------|-------------|
| part | Link to the master Part (Obsolete) |
| source_item | The sourcing [StockItem](#stock-item) linked to this [SupplierPart](#supplierpart) instance |
| supplier | [Company](#company) that supplies this part |
| SKU | Stock keeping unit (supplier part number) |
| link | Link to external website for this supplier part |
| description | Descriptive notes field |
| note | Longer form note field |
| base_cost | Base charge added to order independent of quantity e.g. "Reeling Fee" |
| multiple | Multiple that the part is provided in |
| packaging | packaging that the part is supplied in, e.g. "Reel" |
| pretty_name | The IPN, supplier name, supplier SKU and (if not null) manufacturer string joined by `|`. Ex. `P00037 | Company | 000021` |
| unit_pricing | The price for one unit. |
| price_breaks | Return the associated price breaks in the correct order |
| has_price_breaks | Whether this [SupplierPart](#supplierpart) has price breaks |
| manufacturer_string | Format a MPN string for this [SupplierPart](#supplierpart). Concatenates manufacture name and part number. |

### User

`User` is commonly accessed via fields such as `order.created_by` or `stockitem.stocktake_user`:

| Variable | Description |
|----------|-------------|
| username | the username of the user |
| first_name | The first name of the user |
| last_name | The last name of the user |
| email | The email address of the user |
| pk | The primary key of the user |
