---
title: Admin Shell
---

## Error Logs

Any critical server error logs are recorded to the database, and can be viewed by staff users using the admin interface.

In the admin interface, select the "Errors" view:

{% with id="admin_error_link", url="admin/admin_errors_link.png", description="Admin errors" %}
{% include 'img.html' %}
{% endwith %}

!!! info "URL"
    Alternatively, navigate to the error list view at /admin/error_report/error/

A list of error logs is presented.

{% with id="admin_error_logs", url="admin/admin_errors.png", description="Error logs" %}
{% include 'img.html' %}
{% endwith %}

!!! info "Deleting Logs"
    Error logs should be deleted periodically

## Reporting Errors

Errors should be reported to the [InvenTree GitHub page](https://github.com/inventree/inventree/issues), and include the full error output as recorded to the error log.

### Sentry Integration

If [sentry.io integration](../start/config.md#sentry-integration) is enabled, some error logs are automatically reported to sentry.io
