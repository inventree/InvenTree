---
title: Auto Issue Orders Plugin
---

## Auto Issue Orders Plugin

The **Auto Issue Orders Plugin** provides a mechanism to automatically issue pending orders when the target date is reached.

### Activation

This plugin is an *optional* plugin, and must be enabled in the InvenTree settings.

Additionally, the "Enable Schedule Integration" setting must be enabled in the InvenTree plugin settings. This is required to allow plugins to run scheduled tasks.

### Plugin Settings

The plugin allows configuration for which order types should be automatically issued.

{{ image("auto_issue_settings.png", base="plugin/builtin", title="Auto Issue Settings") }}

## Usage

When this plugin is enabled, any pending orders will be automatically issued when the target date is reached. This is done in the background, and does not require any user interaction.

The plugin checks once per day to see if any orders are pending and have reached their target date. If so, the order will be automatically issued.
