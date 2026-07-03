---
title: Report Mixin
---

## ReportMixin

The `ReportMixin` class provides a plugin with the ability to extend the functionality of custom [report templates](../../report/report.md). A plugin which implements the ReportMixin mixin class can add custom context data to a report template for rendering, and can also receive a callback when a report is generated.

### Add Report Context

A plugin which implements the ReportMixin mixin can define the `add_report_context` method, allowing custom context data to be added to a report template at time of printing.

This method is called each time a report is generated, and is passed the following arguments:

| Argument | Description |
| --- | --- |
| `report_instance` | The report template instance which is being rendered |
| `model_instance` | The model instance against which the report is being generated |
| `user` | The user who initiated the report generation |
| `context` | The context dictionary, which can be modified in-place |

Any data added to the provided `context` dictionary is made available to the report template, and can be rendered using standard django template syntax:

```python
def add_report_context(self, report_instance, model_instance, user, context):
    """Add extra context data to the report template."""
    context['my_custom_data'] = self.calculate_custom_data(model_instance)
```

### Add Label Context

Similarly, the `add_label_context` method allows custom context data to be added to a label template at time of printing:

| Argument | Description |
| --- | --- |
| `label_instance` | The label template instance which is being rendered |
| `model_instance` | The model instance against which the label is being generated |
| `user` | The user who initiated the label generation |
| `context` | The context dictionary, which can be modified in-place |

### Report Callback

The `report_callback` method is called after a report has been generated, and allows the plugin to perform custom actions with the generated report - for example, forwarding the report to an external system, or performing custom post-processing.

| Argument | Description |
| --- | --- |
| `template` | The report template instance which was used to generate the report |
| `instance` | The model instance against which the report was generated |
| `report` | The generated report (PDF file data) |
| `user` | The user who initiated the report generation |

```python
def report_callback(self, template, instance, report, user, **kwargs):
    """Custom callback function - called after a report is generated."""
    # For example, forward the generated report to an external service
    self.upload_to_external_service(report)
```

### Sample Plugin

A sample plugin which provides additional context data to the report templates is available:

::: plugin.samples.integration.report_plugin_sample.SampleReportPlugin
    options:
        show_bases: False
        show_root_heading: False
        show_root_toc_entry: False
        show_source: True
        members: []
