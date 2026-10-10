---
title: InvenTree Barcode Plugin
---

## InvenTree Barcode Plugin

The **InvenTree Barcode Plugin** provides builtin barcode support for InvenTree products. It provides functionality for generating and scanning barcodes. It implements the [BarcodeMixin](../mixins/barcode.md) mixin to provide custom barcode support.

### Activation

This plugin is a *mandatory* plugin, and is always enabled.

### Plugin Settings

This plugin provides selection of the barcode format to use when generating labels. The format can be selected from:

- **Short Barcodes**: This format is used for generating barcodes in a short format, which is a more compact representation of the barcode data.
- **JSON Barcodes**: This format is used for generating barcodes in JSON format, which is a more verbose format. This format is not recommended for use in production environments, as it can be more difficult to parse and may not be supported by all barcode scanners. It is supported for legacy purposes, and is not recommended for use in new deployments.

Additionally, if the "Short Barcodes" format is selected, the user can specify the prefix used for the barcode. This prefix is used to identify the barcode format, and can be set to any value. The default value is `INV-` - although can be changed.

{{ image("barcode_plugin_settings.png", base="plugin/builtin", title="Barcode Plugin Settings") }}
