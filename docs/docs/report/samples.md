---
title: Sample Templates
---

## Sample Templates

A number of pre-built templates are provided with InvenTree, which can be used as a starting point for creating custom reports and labels.

Users can create their own custom templates, or modify the provided templates to suit their needs.

## Report Templates

The following report templates are provided "out of the box" and can be used as a starting point, or as a reference for creating custom reports templates:

| Template | Model Type | Description |
| --- | --- | --- |
| [Bill of Materials](#bill-of-materials-report) | [Part](../part/part.md) | Bill of Materials report |
| [Build Order](#build-order) | [BuildOrder](../build/build.md) | Build Order report |
| [Purchase Order](#purchase-order) | [PurchaseOrder](../order/purchase_order.md) | Purchase Order report |
| [Return Order](#return-order) | [ReturnOrder](../order/return_order.md) | Return Order report |
| [Sales Order](#sales-order) | [SalesOrder](../order/sales_order.md) | Sales Order report |
| [Sales Order Shipment](#sales-order-shipment) | [SalesOrderShipment](../order/sales_order.md) | Sales Order Shipment report |
| [Stock Location](#stock-location) | [StockLocation](../stock/stock.md#stock-location) | Stock Location report |
| [Test Report](#test-report) | [StockItem](../stock/stock.md#stock-item) | Test Report |

### Bill of Materials Report

{{ templatefile("report/inventree_bill_of_materials_report.html") }}

### Build Order

{{ templatefile("report/inventree_build_order_report.html") }}

### Purchase Order

{{ templatefile("report/inventree_bill_of_materials_report.html") }}

### Return Order

{{ templatefile("report/inventree_return_order_report.html") }}

### Sales Order

{{ templatefile("report/inventree_sales_order_report.html") }}

### Sales Order Shipment

{{ templatefile("report/inventree_sales_order_shipment_report.html") }}

### Stock Location

{{ templatefile("report/inventree_stock_location_report.html") }}

### Test Report

{{ templatefile("report/inventree_test_report.html") }}

## Label Templates

The following label templates are provided "out of the box" and can be used as a starting point, or as a reference for creating custom label templates:

| Template | Model Type | Description |
| --- | --- | --- |
| [Build Line](#build-line-label) | [Build line item](../build/build.md) | Build Line label |
| [Part](#part-label) | [Part](../part/part.md) | Part label |
| [Stock Item](#stock-item-label) | [StockItem](../stock/stock.md#stock-item) | Stock Item label |
| [Stock Location](#stock-location-label) | [StockLocation](../stock/stock.md#stock-location) | Stock Location label |

### Build Line Label

{{ templatefile("label/buildline_label.html") }}

### Part Label

{{ templatefile("label/part_label_code128.html") }}

### Stock Item Label

{{ templatefile("label/stockitem_qr.html") }}

### Stock Location Label

{{ templatefile("label/stocklocation_qr_and_text.html") }}
