---
title: Custom Barcodes
---

## Custom Barcode Functionality

With the provision of [internal](./internal.md) and [external](./external.md) barcode support, a lot of potential use-cases are already supported directly by InvenTree.

However, if further customization is required, or a bespoke barcode workflow which is not supported already, then this can easily be implemented using the [plugin system](../extend/plugins/barcode.md).

A custom barcode plugin can be used to (for example) perform a particular action when a barcode is scanned.

### Scanning a Barcode

To scan (process) a barcode, the barcode data is sent via a `POST` request to the `/api/barcode/` API endpoint.

### Barcode Scanning Priority

When a barcode is scanned (sent to the `/barcode/scan/` endpoint), each available "plugin" is checked to see if it returns a valid result for the provided barcode data. The first plugin to return a result prevents any further plugins from being checked.

The barcode is tested as follows, in decreasing order of priority:

- [Internal Barcode Plugin](./internal.md)
- [External Barcode Plugin](./external.md)
- [Custom Barcode Plugins](../extend/plugins/barcode.md)

!!! tip "Plugin Loading Order"
    The first custom plugin to return a result "wins". As the loading order of custom plugins is not defined (or configurable), take special care if you are running multiple plugins which support barcode actions.
