---
title: Builtin Plugins
---

## Builtin Plugins

InvenTree comes with a number of builtin plugins, which provide additional functionality to the system. These plugins are installed by default, and do not require any additional configuration.

Some of the provided builtin plugins are *mandatory*, as they provide core functionality to the system. Other plugins are optional, and can be enabled or disabled as required.

### Available Plugins

The following builtin plugins are available in InvenTree:

| Category | Plugin Name | Description | Mandatory |
| -------- | ----------- | ----------- | --------- |
| Barcodes | [DigiKey](./barcode_digikey.md) | DigiKey barcode support | No |
| Barcodes | [InvenTree Barcode](./inventree_barcode.md) | Internal barcode support | Yes |
| Barcodes | [LCSC](./barcode_lcsc.md) | LCSC barcode support | No |
| Barcodes | [Mouser](./barcode_mouser.md) | Mouser barcode support | No |
| Barcodes | [TME](./barcode_tme.md) | TME barcode support | No |
| Data Export | [BOM Exporter](./bom_exporter.md) | Custom [exporter](../mixins/export.md) for BOM data | Yes |
| Data Export | [InvenTree Exporter](./inventree_exporter.md) | Custom [exporter](../mixins/export.md) for InvenTree data | Yes |
| Data Export | [Parameter Exporter](./parameter_exporter.md) | Custom [exporter](../mixins/export.md) for parameter data | Yes |
| Data Export | [Stocktake Exporter](./stocktake_exporter.md) | Custom [exporter](../mixins/export.md) for stocktake data | No |
| Events | [Auto Create Child Builds](./auto_create_builds.md) | Automatically create child build orders for sub-assemblies | No |
| Events | [Auto Issue Orders](./auto_issue.md) | Automatically issue pending orders when target date is reached | No |
| Label Printing | [Label Printer](./inventree_label.md) | Custom [label](../mixins/label.md) for InvenTree data | Yes |
| Label Printing | [Label Machine](./inventree_label_machine.md) | Custom [label](../mixins/label.md) for InvenTree data | Yes |
| Label Printing | [Label Sheet](./inventree_label_sheet.md) | Custom [label](../mixins/label.md) for InvenTree data | Yes |
| Notifications | [Email Notification](./email_notification.md) | Email notification plugin | Yes |
| Notifications | [Part Update Notifications](./part_notifications.md) | Notifications for part changes | No |
| Notifications | [Slack Notification](./slack_notification.md) | Slack notification plugin | No |
| Notifications | [UI Notification](./ui_notification.md) | UI notification plugin | Yes |
| Pricing | [Currency Exchange](./currency_exchange.md) | Currency exchange rate plugin | Yes |

### Plugin Table

In the admin center, the plugins table can be filtered to display only builtin plugins. This is done by selecting the "Builtin" filter in the table toolbar:

{{ image("filter_plugins.png", base="plugin/builtin", title="Builtin Plugin Filter") }}
