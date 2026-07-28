---
title: Error Logs
---

## Error Logs

Any critical server error logs are recorded to the database, and can be viewed by staff users in the [Admin Center](./admin.md#admin-center), under the *Error Reports* section:

{{ image("admin/admin_errors_link.png", "Error Reports in the Admin Center") }}

A list of error logs is presented. Select an entry to view the full error details, including the traceback.

{{ image("admin/admin_errors.png", "Error logs") }}

!!! info "Database Admin Interface"
    Error logs can also be viewed via the [Database Admin interface](./db_admin.md), at the URL `/admin/error_report/error/`

!!! info "Deleting Logs"
    Error logs should be deleted periodically

## Reporting Errors

Errors should be reported to the [InvenTree GitHub page](https://github.com/inventree/inventree/issues), and include the full error output as recorded to the error log.

### Sentry Integration

If [sentry.io integration](../start/config.md#sentry-integration) is enabled, some error logs are automatically reported to sentry.io
