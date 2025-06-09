---
title: InvenTree Label Machine Plugin
---

## InvenTree Label Machine Plugin

The **InvenTree Label Machine Plugin** provides support for printing labels using the [machines interface](../machines/overview.md) in InvenTree.

It allows labels to be printed directly to an external label printer, using the machines interface.

This plugin by itself does *not* provide connection to any specific label printer. Instead, it provides a generic interface for printing labels to any machine that is configured in InvenTree. A separate plugin is required to provide the actual connection to the label printer.

### Activation

This plugin is a *mandatory* plugin, and is always enabled.

### Plugin Settings

This plugin has no configurable settings.

## Usage

When printing a label, select the *InvenTreeLabelMachine* option from the list of available plugins. Then, select the desired machine from the list of available machines.
