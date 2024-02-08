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

### Barcode Data Types

Barcodes can be linked with the following data model types:

- [Part](../part/part.md#part)
- [Stock Item](../stock/stock.md#stock-item)
- [Stock Location](../stock/stock.md#stock-location)
- [Supplier Part](../order/company.md#supplier-parts)

## Web Integration

Barcode scanning can be enabled within the web interface. Barcode scanning in the web interface supports scanning via:

- Keyboard style scanners (e.g. USB connected)
- Webcam (image processing)

### Configuration

Barcode scanning may need to be enabled for the web interface:

{% with id="barcode_config", url="barcode/barcode_settings.png", description="Barcode settings" %}
{% include 'img.html' %}
{% endwith %}

### Scanning

When enabled, select the barcode icon in the top-right of the menu bar to scan a barcode. If the barcode is recognized by the system, the web browser will automatically navigate to the correct item:

{% with id="barcode_scan", url="barcode/barcode_scan.png", description="Barcode scan" %}
{% include 'img.html' %}
{% endwith %}

#### No Match Found

If no match is found for the scanned barcode, the following error message is displayed:

{% with id="barcode_no_match", url="barcode/barcode_no_match.png", description="No match for barcode" %}
{% include 'img.html' %}
{% endwith %}

## App Integration

Barcode scanning is a key feature of the [companion mobile app](../app/barcode.md).
