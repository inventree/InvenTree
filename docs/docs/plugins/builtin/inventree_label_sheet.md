---
title: InvenTree Label Sheet Plugin
---

## InvenTree Label Sheet Plugin

The **InvenTree Label Sheet Plugin** provides a custom label sheet format for InvenTree. This plugin utilizes the [label mixin](../mixins/label.md) to provide custom printing support.

When printing labels using this plugin, the labels are collated and printed on a single "sheet", in a regular grid format. This is useful for printing labels on standard label sheets.

### Activation

This plugin is a *mandatory* plugin, and is always enabled.

### Plugin Settings

### Plugin Settings

This plugin provides a "DEBUG" mode, which can be enabled in the plugin settings. This mode is intended for development and testing purposes only, and should not be used in production environments. In debug mode, the plugin will generate labels with raw HTML - which can be useful for debugging purposes. However, this mode may not produce valid PDF files, and should not be used for actual label printing.

{{ image("label_sheet_options.png", base="plugin/builtin", title="Label Options") }}

## Usage

To use this plugin, select the *InvenTreeLabelSheet* option from the list of available plugins when printing labels. The plugin will generate a PDF file containing the labels for the selected products.

This plugin provides some additional options in the dialog for customizing the output.

{{ image("label_sheet_select.png", base="plugin/builtin", title="Label Sheet Plugin") }}
