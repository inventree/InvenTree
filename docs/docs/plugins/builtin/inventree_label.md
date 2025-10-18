---
title: InvenTree Label Plugin
---

## InvenTree Label Plugin

The **InvenTree Label Plugin** provides a simple way to print labels for InvenTree products. The plugin utilizes the [label mixin](../mixins/label.md) to provide custom printing support.

When printing labels using this plugin, the labels are printed as PDF files which can be downloaded and printed using any PDF viewer.

### Activation

This plugin is a *mandatory* plugin, and is always enabled.

### Plugin Settings

This plugin provides a "DEBUG" mode, which can be enabled in the plugin settings. This mode is intended for development and testing purposes only, and should not be used in production environments. In debug mode, the plugin will generate labels with raw HTML - which can be useful for debugging purposes. However, this mode may not produce valid PDF files, and should not be used for actual label printing.

{{ image("label_options.png", base="plugin/builtin", title="Label Options") }}

## Usage

To use this plugin, select the *InvenTreeLabel* option from the list of available plugins when printing labels. The plugin will generate a PDF file containing the labels for the selected products.

{{ image("label_select.png", base="plugin/builtin", title="Label Plugin") }}
