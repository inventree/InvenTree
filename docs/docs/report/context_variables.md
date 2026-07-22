---
title: Report Context
---


## Report Context Variables

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
| [company](#company) | A Company instance |
| [build](#build-order) | A [Build Order](../manufacturing/build.md) instance |
| [buildline](#build-line) | A [Build Order Line Item](../manufacturing/build.md) instance |
| [salesorder](#sales-order) | A [Sales Order](../sales/sales_order.md) instance |
| [salesordershipment](#sales-order-shipment) | A [Sales Order Shipment](../sales/sales_order.md#sales-order-shipments) instance |
| [returnorder](#return-order) | A [Return Order](../sales/return_order.md) instance |
| [purchaseorder](#purchase-order) | A [Purchase Order](../purchasing/purchase_order.md) instance |
| [transferorder](#transfer-order) | A [Transfer Order](../stock/transfer_order.md) instance |
| [stockitem](#stock-item) | A [StockItem](../stock/index.md#stock-item) instance |
| [stocklocation](#stock-location) | A [StockLocation](../stock/index.md#stock-location) instance |
| [part](#part) | A [Part](../part/index.md) instance |

### Company

When printing a report or label against a Company instance, the following context variables are available:

{{ report_context("models", "company") }}

For the fields and properties available on the underlying `Company` instance, refer to the [Model Context](model_context.md#company) page.

::: company.models.Company.report_context
    options:
        show_source: True

### Build Order

When printing a report or label against a [Build Order](../manufacturing/build.md) object, the following context variables are available:

{{ report_context("models", "build") }}

For the fields and properties available on the underlying `Build` instance, refer to the [Model Context](model_context.md#build-order) page.

::: build.models.Build.report_context
    options:
        show_source: True

### Build Line

When printing a report or label against a [BuildOrderLineItem](../manufacturing/build.md) object, the following context variables are available:

{{ report_context("models", "buildline") }}

For the fields and properties available on the underlying `BuildLine` instance, refer to the [Model Context](model_context.md#build-line) page.

::: build.models.BuildLine.report_context
    options:
        show_source: True

### Sales Order

When printing a report or label against a [SalesOrder](../sales/sales_order.md) object, the following context variables are available:

{{ report_context("models", "salesorder") }}

For the fields and properties available on the underlying `SalesOrder` instance, refer to the [Model Context](model_context.md#sales-order) page.

::: order.models.Order.report_context
    options:
        show_source: True

### Sales Order Shipment

When printing a report or label against a [SalesOrderShipment](../sales/sales_order.md#sales-order-shipments) object, the following context variables are available:

{{ report_context("models", "salesordershipment") }}

For the fields and properties available on the underlying `SalesOrderShipment` instance, refer to the [Model Context](model_context.md#sales-order-shipment) page.

::: order.models.SalesOrderShipment.report_context
    options:
        show_source: True

### Return Order

When printing a report or label against a [ReturnOrder](../sales/return_order.md) object, the following context variables are available:

{{ report_context("models", "returnorder") }}

For the fields and properties available on the underlying `ReturnOrder` instance, refer to the [Model Context](model_context.md#return-order) page.

### Purchase Order

When printing a report or label against a [PurchaseOrder](../purchasing/purchase_order.md) object, the following context variables are available:

{{ report_context("models", "purchaseorder") }}

For the fields and properties available on the underlying `PurchaseOrder` instance, refer to the [Model Context](model_context.md#purchase-order) page.

### Transfer Order

When printing a report or label against a [TransferOrder](../stock/transfer_order.md) object, the following context variables are available:

{{ report_context("models", "transferorder") }}

For the fields and properties available on the underlying `TransferOrder` instance, refer to the [Model Context](model_context.md#transfer-order) page.

::: order.models.TransferOrder.report_context
    options:
        show_source: True

### Stock Item

When printing a report or label against a [StockItem](../stock/index.md#stock-item) object, the following context variables are available:

{{ report_context("models", "stockitem") }}

For the fields and properties available on the underlying `StockItem` instance, refer to the [Model Context](model_context.md#stock-item) page.

::: stock.models.StockItem.report_context
    options:
        show_source: True

### Stock Location

When printing a report or label against a [StockLocation](../stock/index.md#stock-location) object, the following context variables are available:

{{ report_context("models", "stocklocation") }}

For the fields and properties available on the underlying `StockLocation` instance, refer to the [Model Context](model_context.md#stock-location) page.

::: stock.models.StockLocation.report_context
    options:
        show_source: True

### Part

When printing a report or label against a [Part](../part/index.md) object, the following context variables are available:

{{ report_context("models", "part") }}

For the fields and properties available on the underlying `Part` instance, refer to the [Model Context](model_context.md#part) page.

::: part.models.Part.report_context
    options:
        show_source: True

## Model Context

For the underlying fields and properties available on each of the model instances above (plus related model types such as `Address` or `SupplierPart`), refer to the [Model Context](model_context.md) page.
