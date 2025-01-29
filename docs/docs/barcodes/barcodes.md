---
title: Barcodes
---

## Barcode Support

InvenTree has native support for barcodes, which provides powerful functionality "out of the box", and can be easily extended:

- Barcodes can be scanned [via the API](../api/api.md)
- The web interface supports barcode scanning
- Barcodes integrate natively [with the mobile app](../app/barcode.md)
- Custom barcodes can be assigned to items
- Barcodes can be embedded in [labels or reports](../report/barcodes.md)
- Barcode functionality can be [extended via plugins](../extend/plugins/barcode.md)

### Barcode Formats

InvenTree supports the following barcode formats:

- [Internal Barcodes](./internal.md): Native InvenTree barcodes, which are automatically generated for each item
- [External Barcodes](./external.md): External (third party) barcodes which can be assigned to items
- [Custom Barcodes](./custom.md): Fully customizable barcodes can be generated using the plugin system.

### Barcode Model Linking

Barcodes can be linked with the following data model types:

- [Part](../part/part.md#part)
- [Stock Item](../stock/stock.md#stock-item)
- [Stock Location](../stock/stock.md#stock-location)
- [Supplier Part](../order/company.md#supplier-parts)
- [Purchase Order](../order/purchase_order.md#purchase-orders)
- [Sales Order](../order/sales_order.md#sales-orders)
- [Return Order](../order/return_order.md#return-orders)
- [Build Order](../build/build.md#build-orders)

### Configuration Options

The barcode system can be configured via the [global settings](../settings/global.md#barcodes).

## Web Integration

Barcode scanning can be enabled within the web interface. This allows users to scan barcodes directly from the web browser.

### Input Modes

The following barcode input modes are supported by the web interface:

- **Webcam**: Use a connected webcam to scan barcodes
- **Scanner**: Use a connected barcode scanner to scan barcodes
- **Keyboard**: Manually enter a barcode via the keyboard

### Quick Scan

If barcode scanning is enabled in the web interface, select the barcode icon in the top-right of the menu bar to perform a quick-scan of a barcode. If the barcode is recognized by the system, the web browser will automatically navigate to the correct item:

{% with id="barcode_scan", url="barcode/barcode_scan.png", description="Barcode scan" %}
{% include 'img.html' %}
{% endwith %}

If no match is found for the scanned barcode, the following error message is displayed:

{% with id="barcode_no_match", url="barcode/barcode_no_match.png", description="No match for barcode" %}
{% include 'img.html' %}
{% endwith %}

### Scanning Action Page

A more comprehensive barcode scanning interface is available via the "Scan" page in the web interface. This page allows the user to scan multiple barcodes, and perform certain actions on the scanned items.

To access this page, select *Scan Barcode* from the main navigation menu:

{% with id="barcode_nav_menu", url="barcode/barcode_nav_menu.png", description="Barcode menu item" %}
{% include 'img.html' %}
{% endwith %}

{% with id="barcode_scan_page", url="barcode/barcode_scan_page.png", description="Barcode scan page" %}
{% include 'img.html' %}
{% endwith %}

## App Integration

Barcode scanning is a key feature of the [companion mobile app](../app/barcode.md). When running on a device with an integrated camera, the app can scan barcodes directly from the camera feed.

## Barcode History

If enabled, InvenTree can retain logs of the most recent barcode scans. This can be very useful for debugging or auditing purpopes.

Refer to the [barcode settings](../settings/global.md#barcodes) to enable barcode history logging.

The barcode history can be viewed via the admin panel in the web interface.
