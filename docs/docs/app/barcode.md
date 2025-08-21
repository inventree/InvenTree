---
title: App Barcode Support
---

## Barcode Support

One of the key elements of functionality provided by the InvenTree app is the native support for context-sensitive barcode scanning.

Barcode integration allows extremely efficient stock control, for information lookup and also performing various actions.

### Supported Codes

The following code types are known to be supported

**1D Codes**

- Code-39
- Code-93
- Code-128
- ITF

**2D Codes**

- QR Code
- Data Matrix
- Aztec

## Barcode Input Methods

Barcodes can be scanned using the following methods:

### Camera Input

The camera input method allows you to scan barcodes using the device's internal camera. Both the forward and rear-facing cameras are supported.

### Keyboard Input

The keyboard wedge input method allows you to scan barcodes using any scanner which presents barcode data as keyboard input. This works with external bluetooth scanners, and also provides support for integrated barcode scanner devices which run Android natively.

Note that if using keyboard wedge input mode, the scanner must be configured to append an enter (`\n`) character to the end of the barcode data.

## Barcode Actions

The InvenTree app uses barcodes where possible to provide efficient stock control operations. Some pages in the app will provide context-sensitive barcode actions. These actions are available from the *Barcode Actions* menu, which is displayed in the bottom right corner of the screen.

### Global Scan

Available from the global bottom menu, the *Scan Barcode* provides quick access for scanning a barcode already associated with an InvenTree database item (such as a stock item or location).

If a match is found, the app will navigate to the relevant page.

### Stock Location Actions

From the [Stock Location detail page](./stock.md#stock-location-view), multiple barcode actions may be available:

{{ image("app/barcode_stock_location_actions.png", "Stock location barcode actions") }}

#### Assign Barcode

Assign a custom barcode to the selected location. Scanning a barcode (which is not already associated with an item in the database) will result in that barcode being assigned to the selected location.

#### Transfer Stock Location

Transfer the currently selected stock location into another location. Scanning a valid barcode associated with a stock location will result in the current location being *moved* to the scanned location.

#### Scan Received Parts

Receive incoming purchase order items into the selected location. Scanning a *new* barcode which is associated with an item in an incoming purchase order will receive the item into the selected location.

#### Scan Items Into Location

the *Scan Items Into Location* action allows you to scan items into the selected location. Scanning a valid barcode associated with a stock item (already in the database) will result in that item being transferred to the selected location.

### Stock Item Actions

From the [Stock Item detail page](./stock.md#stock-item-detail-view), the following barcode actions may be available:

{{ image("app/barcode_stock_item_actions.png", "Stock item barcode actions") }}

#### Assign Barcode

Assign a custom barcode to the selected stock item. Scanning a barcode (which is not already associated with an item in the database) will result in that barcode being assigned to the selected stock item.

#### Scan Into Location

Scan the selected stock item into a stock location. Scanning a valid barcode associated with a stock location will result in the selected stock item being transferred to the scanned location.

### Part Actions

From the [Part detail page](./part.md#part-detail-view), the following barcode actions are available:

{{ image("app/barcode_part_actions.png", "Part barcode actions") }}

#### Assign Barcode

Assign a custom barcode to the selected part. Scanning a barcode (which is not already associated with an item in the database) will result in that barcode being assigned to the selected part.

### Purchase Order Actions

From the [Purchase Order detail page](./po.md#purchase-order-detail) page, the following barcode actions are available:

{{ image("app/barcode_po_actions.png", "Purchase order barcode actions") }}

#### Scan Received Parts

Receive incoming purchase order items against the selected purchase order. Scanning a *new* barcode which is associated with an item in an incoming purchase order will receive the item into stock.

### Sales Order Actions

The following barcode actions are available for [Sales Orders](./so.md):

#### Add Line Item

Add a new line item to the selected order by scanning a *Part* barcode

#### Assign Stock

Allocate stock items to the selected sales order by scanning a *StockItem* barcode
