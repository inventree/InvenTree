---
title: Manufacturer Barcode Plugin
---

## Manufacturer Barcode Plugin

The **Manufacturer Barcode Plugin** provides *fallback* barcode support for matching a scanned barcode against the manufacturer part number (MPN) of an existing [manufacturer part](../../purchasing/manufacturer.md).

It is intended for barcodes which are not handled by any of the supplier-specific barcode plugins (e.g. [DigiKey](./barcode_digikey.md) or [Mouser](./barcode_mouser.md)), but which still contain a manufacturer part number.

This plugin implements the [BarcodeMixin](../mixins/barcode.md) mixin to provide custom barcode support - see [Barcode Plugins](./barcode_index.md).

### Activation

This plugin is an *optional* plugin, and must be enabled in the InvenTree admin center.

### Supported Formats

The following barcode formats are supported:

| Format | Example | Notes |
| --- | --- | --- |
| 2D barcode (e.g. DataMatrix) | `[)>␞06␝K123␝1PLM358␝Q10␞␄` | Fields separated by GS / RS characters (ISO/IEC 15434 / ECIA). The `1P` field is used if present, otherwise the `P` field. |
| Prefixed MPN | `1PLM358` or `PLM358` | A single field with a `1P` or `P` prefix, followed by the MPN. |
| Raw MPN | `LM358` | The barcode data is the MPN itself. |

For a single prefixed field, both the MPN with the prefix removed *and* the raw barcode data are checked. For example, `PIC16F84A` matches a manufacturer part with MPN `PIC16F84A`.

### Matching Rules

- The MPN must match *exactly*.
- A match is only returned if exactly *one* manufacturer part matches. If the same MPN exists for multiple manufacturers, no match is returned.
- The user must have permission to view manufacturer parts.

### Priority

This plugin has a low [barcode priority](../mixins/barcode.md#barcode-priority), and is only used if no other barcode plugin is able to match the scanned barcode. A match from a supplier plugin (which may also identify the supplier part) is always preferred.

!!! warning "Supplier Plugin Configuration"
    If a supplier barcode plugin is enabled, but no supplier is configured for it (and none can be automatically determined), that plugin may match *any* standard 2D barcode by MPN alone. Ensure that each enabled supplier plugin has the correct supplier selected.

This plugin does not support receiving items against a purchase order, as a manufacturer part number alone cannot identify the supplier.
