---
title: Auto Create Child Builds Plugin
---

## Auto Create Child Builds Plugin

The **Auto Create Child Builds Plugin** provides a mechanism to automatically create build orders for sub-assemblies when a higher level build order is issued.

### Activation

This plugin is an *optional* plugin, and must be enabled in the InvenTree settings.

Additionally, the {{ globalsetting("ENABLE_PLUGINS_EVENTS", short=True) }} setting must be enabled in the InvenTree plugin settings. This is required to allow plugins to respond to events in the InvenTree system.

## Usage

When this plugin is enabled, any time a build order is issued, the plugin will automatically create build orders for any sub-assemblies that are required by the issued build order.

This process is performed in the background, and does not require any user interaction.

Any new build orders that are created by this plugin will be marked as `PENDING`, and will require review and approval by the user before they can be issued.
