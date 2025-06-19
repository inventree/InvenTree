---
title: Context Variables
---


## Context Variables

Context variables are provided to each template when it is rendered. The available context variables depend on the model type for which the template is being rendered.

### Global Context

In addition to the model-specific context variables, the following global context variables are available to all templates:

{{ report_context("base", "global") }}

::: report.models.ReportTemplateBase.base_context
    options:
        show_source: True

### Report Context

In addition to the [global context](#global-context), all *report* templates have access to the following context variables:

{{ report_context("base", "report") }}

When using the `merge` context variable, the selected items are available in the `instances` list. {{ templatefile("report/inventree_stock_report_merge.html") }} shows a complete example. To access individual item attributes, you can either loop through the `instances` or access them by index like `instance.0.name`.

Below is an example template that generates a single report for some selected parts. Each part occupies a row in the table

```html
{% raw %}
<h2>Merged Report for Selected Parts</h2>
<table>
  <tr>
    <th>Name</th>
    <th>Description</th>
  </tr>
  {% for part in instances %}
    <tr>
      <td>{{ part.name }}</td>
      <td>{{ part.description }}</td>
    </tr>
  {% endfor %}
</table>
{% endraw %}
```

Note that custom plugins may also add additional context variables to the report context.

::: report.models.ReportTemplate.get_context
    options:
        show_source: True

### Label Context

In addition to the [global context](#global-context), all *label* templates have access to the following context variables:

{{ report_context("base", "label") }}

Note that custom plugins may also add additional context variables to the label context.

::: report.models.LabelTemplate.get_context
    options:
        show_source: True

## Template Types

Templates (whether for generating [reports](./report.md) or [labels](./labels.md)) are rendered against a particular "model" type. The following model types are supported, and can have templates renderer against them:

| Model Type | Description |
| --- | --- |
| [build](#build-order) | A [Build Order](../manufacturing/build.md) instance |
| [buildline](#build-line) | A [Build Order Line Item](../manufacturing/build.md) instance |
| [salesorder](#sales-order) | A [Sales Order](../sales/sales_order.md) instance |
| [returnorder](#return-order) | A [Return Order](../sales/return_order.md) instance |
| [purchaseorder](#purchase-order) | A [Purchase Order](../purchasing/purchase_order.md) instance |
| [stockitem](#stock-item) | A [StockItem](../stock/index.md#stock-item) instance |
| [stocklocation](#stock-location) | A [StockLocation](../stock/index.md#stock-location) instance |
| [part](#part) | A [Part](../part/index.md) instance |

### Build Order

When printing a report or label against a [Build Order](../manufacturing/build.md) object, the following context variables are available:

{{ report_context("models", "build") }}

::: build.models.Build.report_context
    options:
        show_source: True

### Build Line

When printing a report or label against a [BuildOrderLineItem](../manufacturing/build.md) object, the following context variables are available:

{{ report_context("models", "buildline") }}

::: build.models.BuildLine.report_context
    options:
        show_source: True

### Sales Order

When printing a report or label against a [SalesOrder](../sales/sales_order.md) object, the following context variables are available:

{{ report_context("models", "salesorder") }}

::: order.models.Order.report_context
    options:
        show_source: True

### Sales Order Shipment

When printing a report or label against a [SalesOrderShipment](../sales/sales_order.md#sales-order-shipments) object, the following context variables are available:

{{ report_context("models", "salesordershipment") }}

::: order.models.SalesOrderShipment.report_context
    options:
        show_source: True

### Return Order

When printing a report or label against a [ReturnOrder](../sales/return_order.md) object, the following context variables are available:

{{ report_context("models", "returnorder") }}

### Purchase Order

When printing a report or label against a [PurchaseOrder](../purchasing/purchase_order.md) object, the following context variables are available:

{{ report_context("models", "purchaseorder") }}

### Stock Item

When printing a report or label against a [StockItem](../stock/index.md#stock-item) object, the following context variables are available:

{{ report_context("models", "stockitem") }}

::: stock.models.StockItem.report_context
    options:
        show_source: True

### Stock Location

When printing a report or label against a [StockLocation](../stock/index.md#stock-location) object, the following context variables are available:

{{ report_context("models", "stocklocation") }}

::: stock.models.StockLocation.report_context
    options:
        show_source: True

### Part

When printing a report or label against a [Part](../part/index.md) object, the following context variables are available:

{{ report_context("models", "part") }}

::: part.models.Part.report_context
    options:
        show_source: True

## Model Variables

Additional to the context variables provided directly to each template, each model type has a number of attributes and methods which can be accessedd via the template.

For each model type, a subset of the most commonly used attributes are listed below. For a full list of attributes and methods, refer to the source code for the particular model type.

### Parts

#### Part

Each part object has access to a lot of context variables about the part. The following context variables are provided when accessing a `Part` object from within the template.

| Variable | Description |
|----------|-------------|
| name | Brief name for this part |
| full_name | Full name for this part (including IPN, if not null and including variant, if not null) |
| variant | Optional variant number for this part - Must be unique for the part name
| category | The [PartCategory](#part-category) object to which this part belongs
| description | Longer form description of the part
| keywords | Optional keywords for improving part search results
| IPN | Internal part number (optional)
| revision | Part revision
| is_template | If True, this part is a 'template' part
| link | Link to an external page with more information about this part (e.g. internal Wiki)
| image | Image of this part
| default_location | The default [StockLocation](#stock-location) object where the item is normally stored (may be null)
| default_supplier | The default [SupplierPart](#supplierpart) which should be used to procure and stock this part
| default_expiry | The default expiry duration for any StockItem instances of this part
| minimum_stock | Minimum preferred quantity to keep in stock
| units | Units of measure for this part (default='pcs')
| salable | Can this part be sold to customers?
| assembly | Can this part be build from other parts?
| component | Can this part be used to make other parts?
| purchaseable | Can this part be purchased from suppliers?
| trackable | Trackable parts can have unique serial numbers assigned, etc, etc
| active | Is this part active? Parts are deactivated instead of being deleted
| virtual | Is this part "virtual"? e.g. a software product or similar
| notes | Additional notes field for this part
| creation_date | Date that this part was added to the database
| creation_user | User who added this part to the database
| responsible | User who is responsible for this part (optional)
| starred | Whether the part is starred or not |
| disabled | Whether the part is disabled or not |
| total_stock | The total amount in stock |
| quantity_being_built | The amount being built |
| required_build_order_quantity | The amount required for build orders |
| allocated_build_order_quantity | The amount allocated for build orders |
| build_order_allocations | Query set with all build order allocations for that part |
| required_sales_order_quantity | The amount required for sales orders |
| allocated_sales_order_quantity | The amount allocated for sales orders |
| available | Whether the part is available or not |
| on_order | The amount that are on order |
| required | The total amount required for build orders and sales orders |
| allocated | The total amount allocated for build orders and sales orders |

#### Part Category


| Variable | Description |
|----------|-------------|
| name | Name of this category |
| parent | Parent category |
| default_location | Default [StockLocation](#stock-location) object for parts in this category or child categories |
| default_keywords | Default keywords for parts created in this category |

### Stock

#### StockItem


| Variable | Description |
|----------|-------------|
| parent | Link to another [StockItem](#stock-item) from which this StockItem was created |
| uid | Field containing a unique-id which is mapped to a third-party identifier (e.g. a barcode) |
| part | Link to the master abstract [Part](#part) that this [StockItem](#stock-item) is an instance of |
| supplier_part | Link to a specific [SupplierPart](#supplierpart) (optional) |
| location | The [StockLocation](#stock-location) Where this [StockItem](#stock-item) is located |
| quantity | Number of stocked units |
| batch | Batch number for this [StockItem](#stock-item) |
| serial | Unique serial number for this [StockItem](#stock-item) |
| link | Optional URL to link to external resource |
| updated | Date that this stock item was last updated (auto) |
| expiry_date | Expiry date of the [StockItem](#stock-item) (optional) |
| stocktake_date | Date of last stocktake for this item |
| stocktake_user | User that performed the most recent stocktake |
| review_needed | Flag if [StockItem](#stock-item) needs review |
| delete_on_deplete | If True, [StockItem](#stock-item) will be deleted when the stock level gets to zero |
| status | Status of this [StockItem](#stock-item) (ref: InvenTree.status_codes.StockStatus) |
| status_label | Textual representation of the status e.g. "OK" |
| notes | Extra notes field |
| build | Link to a Build (if this stock item was created from a build) |
| is_building | Boolean field indicating if this stock item is currently being built (or is "in production") |
| purchase_order | Link to a [PurchaseOrder](#purchase-order) (if this stock item was created from a PurchaseOrder) |
| infinite | If True this [StockItem](#stock-item) can never be exhausted |
| sales_order | Link to a [SalesOrder](#sales-order) object (if the StockItem has been assigned to a SalesOrder) |
| purchase_price | The unit purchase price for this [StockItem](#stock-item) - this is the unit price at time of purchase (if this item was purchased from an external supplier) |
| packaging | Description of how the StockItem is packaged (e.g. "reel", "loose", "tape" etc) |

#### StockLocation

| Variable | Description |
|----------|-------------|
| barcode | Brief payload data (e.g. for labels). Example: `{"stocklocation": 826}` where 826 is the primary key|
| description | The description of the location  |
| icon | The name of the icon if set, e.g. fas fa-warehouse |
| item_count | Simply returns the number of stock items in this location |
| name | The name of the location. This is only the name of this location, not the path |
| owner | The owner of the location if it has one. The owner can only be assigned in the admin interface |
| parent | The parent location. Returns None if it is already the top most one |
| path | A queryset of locations that contains the hierarchy starting from the top most parent |
| pathstring | A string that contains all names of the path separated by slashes e.g. A/B/C |
| structural | True if the location is structural |

### Suppliers

#### Company


| Variable | Description |
|----------|-------------|
| name | Name of the company |
| description | Longer form description |
| website | URL for the company website |
| primary_address | [Address](#address) object that is marked as primary address |
| address | String format of the primary address |
| contact | Contact Name |
| phone | Contact phone number |
| email | Contact email address |
| link | A second URL to the company (Actually only accessible in the admin interface) |
| notes | Extra notes about the company (Actually only accessible in the admin interface) |
| is_customer | Boolean value, is this company a customer |
| is_supplier | Boolean value, is this company a supplier |
| is_manufacturer | Boolean value, is this company a manufacturer |
| currency_code | Default currency for the company |
| parts | Query set with all parts that the company supplies |

#### Address


| Variable | Description |
|----------|-------------|
| line1 | First line of the postal address |
| line2 | Second line of the postal address |
| postal_code | ZIP code of the city |
| postal_city | City name |
| country | Country name |

#### Contact

| Variable | Description |
|----------|-------------|
| company | Company object where the contact belongs to |
| name | First and second name of the contact |
| phone | Phone number |
| email | Email address |
| role | Role of the contact |

#### SupplierPart


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
| lead_time | Supplier lead time |
| packaging | packaging that the part is supplied in, e.g. "Reel" |
| pretty_name | The IPN, supplier name, supplier SKU and (if not null) manufacturer string joined by `|`. Ex. `P00037 | Company | 000021` |
| unit_pricing | The price for one unit. |
| price_breaks | Return the associated price breaks in the correct order |
| has_price_breaks | Whether this [SupplierPart](#supplierpart) has price breaks |
| manufacturer_string | Format a MPN string for this [SupplierPart](#supplierpart). Concatenates manufacture name and part number. |

### User

| Variable | Description |
|----------|-------------|
| username | the username of the user |
| fist_name | The first name of the user |
| last_name | The last name of the user |
| email | The email address of the user |
| pk | The primary key of the user |
