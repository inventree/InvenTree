---
title: Report Mixin
---

## ReportMixin

The ReportMixin class provides a plugin with the ability to extend the functionality of custom [report templates](../../report/report.md). A plugin which implements the ReportMixin mixin class can add custom context data to a report template for rendering.

### Add Report Context

A plugin which implements the ReportMixin mixin can define the `add_report_context` method, allowing custom context data to be added to a report template at time of printing.

### Add Label Context

Additionally the `add_label_context` method, allowing custom context data to be added to a label template at time of printing.

### Sample Plugin

A sample plugin which provides additional context data to the report templates is available:

::: plugin.samples.integration.report_plugin_sample.SampleReportPlugin
    options:
        show_bases: False
        show_root_heading: False
        show_root_toc_entry: False
        show_source: True
        members: []
