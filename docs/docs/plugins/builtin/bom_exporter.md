---
title: BOM Exporter Plugin
---

## BOM Exporter Plugin

The **BOM Exporter Plugin** provides custom export functionality for [Bill of Materials (BOM)](../../manufacturing/bom.md) data.

It utilizies the [ExporterMixin](../mixins/export.md) mixin to provide a custom export format for BOM data.

### Activation

This plugin is a *mandatory* plugin, and is always enabled.

### Plugin Settings

This plugin has no configurable settings.

## Usage

This plugin is used in the same way as the [InvenTree Exporter Plugin](./inventree_exporter.md), but provides a custom export format for BOM data.

When exporting BOM data, the *BOM Exporter* plugin is available for selection in the export dialog. When selected, the plugin provides some additional export options to control the data export process.

{{ image("bom_export_options.png", base="plugin/builtin", title="BOM Export Options") }}
