---
title: Mouser Barcode Plugin
---

## Mouser Barcode Plugin

The **Mouser Barcode Plugin** provides barcode support for [Mouser](https://www.mouser.com/) products. When receiving items from Mouser, the barcode on the product can be scanned to automatically identify the product in InvenTree.

This plugin implements the [BarcodeMixin](../mixins/barcode.md) mixin to provide custom barcode support.

### Activation

This plugin is an *optional* plugin, and must be enabled in the InvenTree admin center.

### Plugin Settings

After activating the plugin, the user must specify which [supplier](../../purchasing/supplier.md) the plugin should be associated with. This is done by selecting the supplier from the dropdown list in the plugin settings:

{{ image("mouser_plugin_settings.png", base="plugin/builtin", title="Mouser Plugin Settings") }}
