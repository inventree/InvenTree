---
title: Part Parameter Exporter
---

## Part Parameter Exporter

The **Part Parameter Exporter** plugin provides custom export functionality for [Part Parameter](../../part/parameter.md) data.

It utilizes the [ExporterMixin](../mixins/export.md) mixin to provide a custom export format for part parameter data.

### Activation

This plugin is a *mandatory* plugin, and is always enabled.

### Plugin Settings

This plugin has no configurable settings.

## Usage

This plugin is used in the same way as the [InvenTree Exporter Plugin](./inventree_exporter.md), but provides a custom export format for part parameter data.

When exporting part parameter data, the *Part Parameter Exporter* plugin is available for selection in the export dialog. When selected, the plugin provides some additional export options to control the data export process.

{{ image("parameter_export_options.png", base="plugin/builtin", title="Part Parameter Export Options") }}
