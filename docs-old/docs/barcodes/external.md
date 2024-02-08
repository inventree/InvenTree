---
title: External Barcodes
---

## External Barcodes

In addition to defining an [internal barcode format](./internal.md), models which have associated barcode information also allow arbitrary external (third party) barcodes to be assigned or "linked" to items in the database.

For example, you have just purchased a reel of capacitors from a supplier, which comes provided with a sufficiently unique barcode or qr-code. Instead of printing an *internal* barcode, the existing barcode can be scanned and *linked* to the specific reel (which is a [Stock Item](../stock/stock.md#stock-item)).

Linking to external barcodes allows an alternative barcode workflow, which may be especially useful when dealing with in-feed components which are received from external suppliers.

!!! tip "Dealer's Choice"
    The use of external barcodes is entirely up to the user, if it is deemed to be convenient.

## Linking Barcodes

### Via the API

Facility for barcode linking (and un-linking) is provided via the [API](../api/api.md).

- The `/api/barcode/link/` API endpoint is used to link a barcode with an existing database item
- The `/api/barcode/unlink/` API endpoint is used to unlink a barcode from an existing database item

### Via the Web Interface

To link an arbitrary barcode, select the *Link Barcode* action as shown below:

{% with id="barcode_link_1", url="barcode/barcode_link_1.png", description="Link barcode" %}
{% include 'img.html' %}
{% endwith %}

{% with id="barcode_link_2", url="barcode/barcode_link_2.png", description="Link barcode" %}
{% include 'img.html' %}
{% endwith %}

If an item already has a linked barcode, it can be un-linked by selecting the *Unlink Barcode* action:

{% with id="barcode_unlink", url="barcode/barcode_unlink.png", description="Unlink barcode" %}
{% include 'img.html' %}
{% endwith %}

### Via the App

External barcodes can be linked to (or unlinked from) database items via the [mobile app](../app/barcode.md)
