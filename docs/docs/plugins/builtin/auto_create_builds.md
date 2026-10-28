---
title: Auto Create Child Builds Plugin
---

## Auto Create Child Builds Plugin

The **Auto Create Child Builds Plugin** provides a mechanism to automatically create build orders for sub-assemblies when a higher level build order is issued.

### Activation

This plugin is an *optional* plugin, and must be enabled in the InvenTree settings.

Additionally, the {{ globalsetting("ENABLE_PLUGINS_EVENTS", short=True) }} setting must be enabled in the InvenTree plugin settings. This is required to allow plugins to respond to events in the InvenTree system.

### Plugin Settings

| Setting | Description | Default |
| --- | --- | --- |
| Cascade Depth | How many levels of the sub-assembly tree to generate child build orders for | 1 |

With the default depth of `1`, child build orders are only created for the direct sub-assemblies of the issued build order. A larger value cascades further down the BOM tree - each additional level is processed as a separate background task.

## Usage

When this plugin is enabled, any time a build order is issued, the plugin will automatically create build orders for any sub-assemblies that are required by the issued build order.

This process is performed in the background, and does not require any user interaction.

Any new build orders that are created by this plugin will be marked as `PENDING`, and will require review and approval by the user before they can be issued.

### Quantity Calculation

A child build order is only created when there is insufficient stock of the sub-assembly. The quantity of the new build order is calculated as:

```
required = (BOM requirement) + (minimum stock) + (allocated stock) - (stock on hand) - (quantity in production)
```

The result is rounded up to the nearest whole number.

### Duplicate Prevention

A child build order is not created for a sub-assembly if the build order already has a child build order for that part. This means that issuing a build order multiple times (e.g. after placing it on hold) will not create duplicate child build orders.

If a sub-assembly cannot be built (for example, the part is inactive and {{ globalsetting("BUILDORDER_REQUIRE_ACTIVE_PART", short=True) }} is enabled), it is skipped and a warning is logged.
