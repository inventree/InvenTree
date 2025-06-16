---
title: Builtin Plugins
---

## Builtin Plugins

InvenTree comes with a number of builtin plugins, which provide additional functionality to the system. These plugins are installed by default, and do not require any additional configuration.

Some of the provided builtin plugins are *mandatory*, as they provide core functionality to the system. Other plugins are optional, and can be enabled or disabled as required.

### Available Plugins

The following builtin plugins are available in InvenTree:

| Plugin Name | Description | Mandatory |
| ----------- | ----------- | --------- |
| [Auto Create Child Builds](./auto_create_builds.md) | Automatically create child build orders for sub-assemblies | No |
| [Auto Issue Orders](./auto_issue.md) | Automatically issue pending orders when target date is reached | No |
| [BOM Exporter](./bom_exporter.md) | Custom [exporter](../mixins/export.md) for BOM data | Yes |
| [Currency Exchange](./currency_exchange.md) | Currency exchange rate plugin | Yes |
| [DigiKey](./digikey.md) | DigiKey barcode support | No |
| [Email Notification](./email_notification.md) | Email notification plugin | Yes |
| [InvenTree Barcode](./inventree_barcode.md) | Internal barcode support | Yes |
| [InvenTree Exporter](./inventree_exporter.md) | Custom [exporter](../mixins/export.md) for InvenTree data | Yes |
| [Label Printer](./inventree_label.md) | Custom [label](../mixins/label.md) for InvenTree data | Yes |
| [Label Machine](./inventree_label_machine.md) | Custom [label](../mixins/label.md) for InvenTree data | Yes |
| [Label Sheet](./inventree_label_sheet.md) | Custom [label](../mixins/label.md) for InvenTree data | Yes |
| [LCSC](./lcsc.md) | LCSC barcode support | No |
| [Mouser](./mouser.md) | Mouser barcode support | No |
| [Parameter Exporter](./part_parameter_exporter.md) | Custom [exporter](../mixins/export.md) for part parameter data | Yes |
| [Part Update Notifications](./part_notifications.md) | Notifications for part changes | No |
| [Slack Notification](./slack_notification.md) | Slack notification plugin | No |
| [TME](./tme.md) | TME barcode support | No |
| [UI Notification](./ui_notification.md) | UI notification plugin | Yes |

### Plugin Table

In the admin center, the plugins table can be filtered to display only builtin plugins. This is done by selecting the "Builtin" filter in the table toolbar:

{{ image("filter_plugins.png", base="plugin/builtin", title="Builtin Plugin Filter") }}
