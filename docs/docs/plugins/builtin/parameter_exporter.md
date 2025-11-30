---
title: Parameter Exporter
---

## Parameter Exporter

The **Parameter Exporter** plugin provides custom export functionality for models which support custom [Parameter](../../concepts/parameters.md) data.

It utilizes the [ExporterMixin](../mixins/export.md) mixin to provide a custom export format for part parameter data.

In addition to the standard exported fields, this plugin also exports all associated parameter data for each row of the export.

### Activation

This plugin is a *mandatory* plugin, and is always enabled.

### Plugin Settings

This plugin has no configurable settings.

## Usage

This plugin is used in the same way as the [InvenTree Exporter Plugin](./inventree_exporter.md), but provides a custom export format for part parameter data.

When exporting parameter data, the *Parameter Exporter* plugin is available for selection in the export dialog. When selected, the plugin provides some additional export options to control the data export process.

{{ image("parameter_export_options.png", base="plugin/builtin", title="Parameter Export Options") }}
