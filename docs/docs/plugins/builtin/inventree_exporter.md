---
title: InvenTree Exporter Plugin
---

## InvenTree Exporter Plugin

The **InvenTree Exporter Plugin** provides basic data export functionality. It is the "default" export plugin, and can be used to export data from any tabulated dataset.

It utilizes the [ExporterMixin](../mixins/export.md) mixin to provide a general purpose export format for InvenTree data.

### Activation

This plugin is a *mandatory* plugin, and is always enabled.

### Plugin Settings

This plugin has no configurable settings.

## Usage

To export table data using this plugin, first click the *Export Data* button in the table toolbar:

{{ image("download_data.png", base="plugin/builtin", title="Export Data") }}

Then, select the *InvenTree Exporter* plugin from the list of available plugins:

{{ image("select_exporter.png", base="plugin/builtin", title="Select Exporter") }}

Finally, select the desired export format and then click the *Export* button to download the data.
